import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import requests


def parse_instagram_input(user_input: str) -> dict:
    """Parse Instagram post/reel URL, profile URL, or @username."""
    raw = user_input.strip()
    if not raw:
        raise ValueError('Masukkan URL Instagram atau @username.')

    if raw.startswith('http://') or raw.startswith('https://'):
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if 'instagram.com' not in host:
            raise ValueError('URL harus berasal dari instagram.com.')
        path = parsed.path.strip('/')
        m_post = re.match(r'^(?:p|reel|tv)/([A-Za-z0-9_-]+)', path)
        if m_post:
            return {
                'kind': 'post',
                'username': '@instagram_post',
                'shortcode': m_post.group(1),
                'url': f'https://www.instagram.com/p/{m_post.group(1)}/'
            }
        m_user = re.match(r'^@?([A-Za-z0-9._]+)$', path.split('/')[0])
        if m_user:
            uname = m_user.group(1)
            return {
                'kind': 'profile',
                'username': f'@{uname}',
                'shortcode': None,
                'url': f'https://www.instagram.com/{uname}/'
            }
        raise ValueError('Format URL Instagram tidak dikenali.')

    username = raw.lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9._]+', username):
        raise ValueError('Format username Instagram tidak valid.')
    return {
        'kind': 'profile',
        'username': f'@{username}',
        'shortcode': None,
        'url': f'https://www.instagram.com/{username}/'
    }


def _extract_from_web_profile_json(data: dict, default_username: str, max_items: int = 25) -> list:
    """Extract captions and engagement from Instagram web_profile_info JSON."""
    user = data.get('data', {}).get('user') or {}
    uname = user.get('username') or default_username.lstrip('@')
    edges = user.get('edge_owner_to_timeline_media', {}).get('edges', [])

    posts = []
    for edge in edges[:max_items]:
        node = edge.get('node', {})
        cap_edges = node.get('edge_media_to_caption', {}).get('edges', [])
        text = cap_edges[0].get('node', {}).get('text', '').strip() if cap_edges else ''
        if not text:
            continue
        ts = node.get('taken_at_timestamp')
        created_at = datetime.utcfromtimestamp(int(ts)) if ts else datetime.utcnow()
        likes = int(node.get('edge_liked_by', {}).get('count') or node.get('edge_media_preview_like', {}).get('count') or 0)
        comments = int(node.get('edge_media_to_comment', {}).get('count') or 0)
        posts.append({
            'username': f'@{uname}',
            'content': text,
            'likes': likes,
            'shares': comments,
            'created_at': created_at
        })
    return posts


def _extract_ig_post_from_html(html: str, default_username: str) -> list:
    """Extract caption from Instagram post HTML OpenGraph metadata."""
    m_desc = re.search(r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]+)"', html)
    if not m_desc:
        return []
    desc = m_desc.group(1).strip()
    # Format umum og:description IG: "123 likes, 4 comments - username on Date: \"caption\""
    m_cap = re.search(r':\s*"(.+)"\s*$', desc, re.DOTALL)
    text = m_cap.group(1).strip() if m_cap else desc
    m_user = re.search(r'-\s*([A-Za-z0-9._]+)\s+on\s+', desc)
    uname = f'@{m_user.group(1)}' if m_user else default_username
    if not text or 'Instagram' in text[:25]:
        return []
    return [{
        'username': uname,
        'content': text,
        'likes': 0,
        'shares': 0,
        'created_at': datetime.utcnow()
    }]


def _fetch_ig_via_api(token: str, max_items: int = 25) -> dict:
    """Fetch media captions via official Instagram Graph API."""
    resp = requests.get(
        'https://graph.instagram.com/me/media',
        params={
            'fields': 'id,caption,like_count,comments_count,timestamp,username',
            'limit': max_items,
            'access_token': token
        },
        timeout=12
    )
    resp.raise_for_status()
    posts = []
    for item in resp.json().get('data', []):
        text = (item.get('caption') or '').strip()
        if not text:
            continue
        ts = item.get('timestamp', '')[:19]
        created_at = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S') if ts else datetime.utcnow()
        uname = item.get('username') or 'instagram_user'
        posts.append({
            'username': f'@{uname}',
            'content': text,
            'likes': int(item.get('like_count') or 0),
            'shares': int(item.get('comments_count') or 0),
            'created_at': created_at
        })
    if not posts:
        raise ValueError('Tidak ada post dengan caption yang ditemukan dari Instagram API.')
    return {
        'mode': 'instagram',
        'target': posts[0]['username'],
        'kind': 'api',
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }


def _extract_ig_embed_html(shortcode: str, headers: dict) -> list:
    """Fetch public Instagram post embed page (/embed/captioned/) which works without login."""
    embed_url = f'https://www.instagram.com/p/{shortcode}/embed/captioned/'
    resp = requests.get(embed_url, headers=headers, timeout=12)
    if not resp.ok:
        return []
    html = resp.text

    m_user = re.search(r'class="UsernameText"[^>]*>([^<]+)<', html)
    uname = f'@{m_user.group(1).strip().lstrip("@")}' if m_user else '@instagram_user'

    # Ambil isi caption dari blok <div class="Caption">
    m_cap = re.search(r'<div class="Caption"[^>]*>.*?<a[^>]*class="CaptionUsername"[^>]*>([^<]+)</a>(.*?)</div>', html, re.DOTALL)
    if m_cap:
        if not m_user:
            uname = f'@{m_cap.group(1).strip().lstrip("@")}'
        raw_cap = re.sub(r'<br\s*/?>', ' ', m_cap.group(2))
        clean_cap = re.sub(r'<[^>]+>', '', raw_cap)
        clean_cap = re.sub(r'\s+', ' ', clean_cap).strip()
        if clean_cap:
            return [{
                'username': uname,
                'content': clean_cap,
                'likes': 0,
                'shares': 0,
                'created_at': datetime.utcnow()
            }]

    # Fallback: cari caption di JSON embed ("caption":"...")
    m_json_cap = re.search(r'"caption":"((?:[^"\\]|\\.)+)"', html)
    if m_json_cap:
        text = m_json_cap.group(1).encode('utf-8').decode('unicode_escape', errors='ignore').strip()
        if text:
            return [{
                'username': uname,
                'content': text,
                'likes': 0,
                'shares': 0,
                'created_at': datetime.utcnow()
            }]
    return []


def analyze_instagram_manual(target_account: str, raw_texts: str) -> dict:
    """Analyze pasted Instagram captions or comments (1 line = 1 item)."""
    target = target_account.strip() or '@instagram_user'
    if not target.startswith('@'):
        target = f'@{target}'
    lines = [ln.strip() for ln in raw_texts.splitlines() if ln.strip()]
    if not lines:
        raise ValueError('Harap masukkan minimal 1 baris komentar/caption Instagram.')

    now = datetime.utcnow()
    posts = []
    for idx, line in enumerate(lines, start=1):
        uname = f'@ig_user_{idx}'
        content = line
        if ':' in line and len(line.split(':', 1)[0]) <= 30:
            left, right = line.split(':', 1)
            if right.strip():
                uname = f'@{left.strip().lstrip("@")}'
                content = right.strip()
        posts.append({
            'username': uname,
            'content': content,
            'likes': 0,
            'shares': 0,
            'created_at': now
        })

    return {
        'mode': 'instagram_manual',
        'target': target,
        'kind': 'manual',
        'total_likes': 0,
        'total_posts': len(posts),
        'posts': posts
    }


def analyze_instagram_url(user_input: str, max_items: int = 25) -> dict:
    """Analyze Instagram post/reel or profile posts for sentiment analysis."""
    info = parse_instagram_input(user_input)
    token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if token and info['kind'] == 'profile' and info['username'] == '@me':
        return _fetch_ig_via_api(token, max_items=max_items)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
        'X-IG-App-ID': '936619743392459'
    }
    posts = []
    if info['kind'] == 'post' and info.get('shortcode'):
        posts = _extract_ig_embed_html(info['shortcode'], headers)

    if not posts and info['kind'] == 'profile':
        uname = info['username'].lstrip('@')
        api_resp = requests.get(
            f'https://www.instagram.com/api/v1/users/web_profile_info/?username={uname}',
            headers=headers,
            timeout=12
        )
        if api_resp.ok:
            try:
                posts = _extract_from_web_profile_json(api_resp.json(), info['username'], max_items=max_items)
            except ValueError:
                posts = []

    if not posts:
        resp = requests.get(info['url'], headers=headers, timeout=12)
        if resp.status_code in (401, 403, 429):
            raise ValueError(
                f'Instagram membatasi akses publik (HTTP {resp.status_code}). '
                'Anda dapat mengisi INSTAGRAM_ACCESS_TOKEN di .env atau menempelkan caption/komentar di Quick Text Analyzer.'
            )
        resp.raise_for_status()
        posts = _extract_ig_post_from_html(resp.text, info['username'])

    if not posts:
        raise ValueError(
            'Tidak dapat mengekstrak caption/komentar dari Instagram (kemungkinan halaman memerlukan login). '
            'Silakan isi INSTAGRAM_ACCESS_TOKEN di .env atau gunakan Quick Text Analyzer / Upload CSV.'
        )

    return {
        'mode': 'instagram',
        'target': info['username'],
        'kind': info['kind'],
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }
