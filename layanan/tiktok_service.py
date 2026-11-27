import json
import re
from datetime import datetime
from urllib.parse import urlparse
import requests


def parse_tiktok_input(user_input: str) -> dict:
    """Parse TikTok video URL, profile URL, or @username."""
    raw = user_input.strip()
    if not raw:
        raise ValueError('Masukkan URL TikTok atau @username.')

    if raw.startswith('http://') or raw.startswith('https://'):
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if 'tiktok.com' not in host:
            raise ValueError('URL harus berasal dari tiktok.com.')

        if 'vt.tiktok.com' in host or 'vm.tiktok.com' in host:
            r = requests.get(raw, allow_redirects=True, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            parsed = urlparse(r.url)
            raw = r.url

        m_vid = re.search(r'/@([^/]+)/video/(\d+)', parsed.path)
        if m_vid:
            return {
                'kind': 'video',
                'username': f'@{m_vid.group(1)}',
                'video_id': m_vid.group(2),
                'url': f'https://www.tiktok.com/@{m_vid.group(1)}/video/{m_vid.group(2)}'
            }
        m_user = re.search(r'/@([^/]+)', parsed.path)
        if m_user:
            return {
                'kind': 'profile',
                'username': f'@{m_user.group(1)}',
                'video_id': None,
                'url': f'https://www.tiktok.com/@{m_user.group(1)}'
            }
        raise ValueError('Format URL TikTok tidak dikenali. Gunakan URL video atau profil TikTok.')

    username = raw.lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9._]+', username):
        raise ValueError('Format username TikTok tidak valid.')
    return {
        'kind': 'profile',
        'username': f'@{username}',
        'video_id': None,
        'url': f'https://www.tiktok.com/@{username}'
    }


def _extract_tiktok_from_rehydration(html: str, default_username: str) -> list:
    """Extract TikTok video descriptions or comments from __UNIVERSAL_DATA_FOR_REHYDRATION__."""
    m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    posts = []
    seen = set()

    def _walk(node):
        if isinstance(node, dict):
            if 'desc' in node and isinstance(node.get('desc'), str) and 'stats' in node:
                text = node['desc'].strip()
                if text and text not in seen:
                    seen.add(text)
                    author = node.get('author') or {}
                    uname = author.get('uniqueId') if isinstance(author, dict) else None
                    stats = node.get('stats') or {}
                    ct = node.get('createTime')
                    created_at = datetime.utcfromtimestamp(int(ct)) if str(ct).isdigit() else datetime.utcnow()
                    posts.append({
                        'username': f'@{uname}' if uname else default_username,
                        'content': text,
                        'likes': int(stats.get('diggCount') or 0),
                        'shares': int(stats.get('shareCount') or 0),
                        'created_at': created_at
                    })
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for it in node:
                _walk(it)

    _walk(data)
    return posts


def _fetch_tiktok_comments(video_id: str, headers: dict, max_comments: int = 30) -> list:
    """Fetch public TikTok video comments from TikTok comment API."""
    api_url = 'https://www.tiktok.com/api/comment/list/'
    params = {'aid': '1988', 'aweme_id': video_id, 'count': max_comments, 'cursor': 0}
    resp = requests.get(api_url, params=params, headers=headers, timeout=10)
    if not resp.ok:
        return []
    try:
        data = resp.json()
    except ValueError:
        return []

    posts = []
    for c in data.get('comments', [])[:max_comments]:
        text = (c.get('text') or '').strip()
        if not text:
            continue
        user = c.get('user') or {}
        uname = user.get('unique_id') or user.get('nickname') or 'tiktok_user'
        ct = c.get('create_time')
        created_at = datetime.utcfromtimestamp(int(ct)) if ct else datetime.utcnow()
        posts.append({
            'username': f'@{uname.lstrip("@")}',
            'content': text,
            'likes': int(c.get('digg_count') or 0),
            'shares': 0,
            'created_at': created_at
        })
    return posts


def analyze_tiktok_url(user_input: str, max_items: int = 30) -> dict:
    """Analyze TikTok video comments/caption or profile video captions."""
    info = parse_tiktok_input(user_input)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
        'Referer': 'https://www.tiktok.com/'
    }

    posts = []
    if info['kind'] == 'video' and info['video_id']:
        posts = _fetch_tiktok_comments(info['video_id'], headers, max_comments=max_items)
        if not posts:
            # Fallback ke oEmbed untuk mengambil caption video
            oe = requests.get('https://www.tiktok.com/oembed', params={'url': info['url']}, headers=headers, timeout=10)
            if oe.ok:
                oe_json = oe.json()
                title = (oe_json.get('title') or '').strip()
                author = oe_json.get('author_unique_id') or info['username'].lstrip('@')
                if title:
                    posts.append({
                        'username': f'@{author}',
                        'content': title,
                        'likes': 0,
                        'shares': 0,
                        'created_at': datetime.utcnow()
                    })

    if not posts:
        resp = requests.get(info['url'], headers=headers, timeout=12)
        if resp.status_code in (401, 403, 429):
            raise ValueError(f'TikTok membatasi akses publik (HTTP {resp.status_code}).')
        resp.raise_for_status()
        posts = _extract_tiktok_from_rehydration(resp.text, info['username'])[:max_items]

    if not posts:
        raise ValueError(
            'Tidak dapat mengekstrak komentar/post dari TikTok (kemungkinan dibatasi proteksi anti-bot TikTok).'
        )

    return {
        'mode': 'tiktok',
        'target': info['username'],
        'kind': info['kind'],
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }
