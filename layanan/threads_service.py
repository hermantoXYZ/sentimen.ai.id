import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import requests


def parse_threads_input(user_input: str) -> dict:
    """Parse Threads post URL, profile URL, or @username into structured info."""
    raw = user_input.strip()
    if not raw:
        raise ValueError('Masukkan URL Threads atau @username.')

    if raw.startswith('http://') or raw.startswith('https://'):
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if 'threads.net' not in host and 'threads.com' not in host:
            raise ValueError('URL harus berasal dari threads.net atau threads.com.')
        path = parsed.path.strip('/')
        m_post = re.match(r'^@?([^/]+)/post/([A-Za-z0-9_-]+)', path)
        if m_post:
            username = m_post.group(1)
            code = m_post.group(2)
            return {
                'kind': 'post',
                'username': f'@{username}',
                'post_code': code,
                'url': f'https://www.threads.net/@{username}/post/{code}'
            }
        m_user = re.match(r'^@?([^/]+)$', path)
        if m_user:
            username = m_user.group(1)
            return {
                'kind': 'profile',
                'username': f'@{username}',
                'post_code': None,
                'url': f'https://www.threads.net/@{username}'
            }
        raise ValueError('Format URL Threads tidak dikenali. Gunakan URL post atau profil Threads.')

    username = raw.lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9._]+', username):
        raise ValueError('Format username Threads tidak valid.')
    return {
        'kind': 'profile',
        'username': f'@{username}',
        'post_code': None,
        'url': f'https://www.threads.net/@{username}'
    }


def _extract_post_text(post: dict) -> str:
    """Extract text from caption.text or text_post_app_info.text_fragments."""
    caption = post.get('caption') or {}
    if isinstance(caption, dict) and caption.get('text'):
        return caption['text'].strip()
    fragments = (
        post.get('text_post_app_info', {})
        .get('text_fragments', {})
        .get('fragments', [])
    )
    if isinstance(fragments, list):
        parts = [f.get('plaintext', '') for f in fragments if isinstance(f, dict)]
        joined = ''.join(parts).strip()
        if joined:
            return joined
    return ''


def _walk_thread_items(obj, results: list, seen: set):
    """Recursively extract thread post items from Threads SSR/GraphQL JSON."""
    if isinstance(obj, dict):
        if 'thread_items' in obj and isinstance(obj['thread_items'], list):
            for item in obj['thread_items']:
                post = item.get('post') if isinstance(item, dict) else None
                if not isinstance(post, dict):
                    continue
                text = _extract_post_text(post)
                if not text or text in seen:
                    continue
                seen.add(text)
                user = post.get('user') or {}
                uname = user.get('username') or 'threads_user'
                likes = int(post.get('like_count') or 0)
                taken_at = post.get('taken_at')
                created_at = datetime.utcfromtimestamp(taken_at) if isinstance(taken_at, (int, float)) else datetime.utcnow()
                results.append({
                    'username': f'@{uname}',
                    'content': text,
                    'likes': likes,
                    'shares': int(post.get('text_post_app_info', {}).get('direct_reply_count') or 0),
                    'created_at': created_at
                })
        for v in obj.values():
            _walk_thread_items(v, results, seen)
    elif isinstance(obj, list):
        for item in obj:
            _walk_thread_items(item, results, seen)


def _find_pagination_info(obj):
    """Find (end_cursor, has_next_page) in Threads SSR/GraphQL JSON."""
    if isinstance(obj, dict):
        pi = obj.get('page_info')
        if isinstance(pi, dict) and pi.get('end_cursor') and pi.get('has_next_page'):
            return pi.get('end_cursor'), True
        for v in obj.values():
            res = _find_pagination_info(v)
            if res[0]:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = _find_pagination_info(item)
            if res[0]:
                return res
    return None, False


def _fetch_more_graphql(html: str, cursor: str, headers: dict, max_posts: int, results: list, seen: set):
    """Attempt to fetch additional pages via Threads public GraphQL endpoint."""
    m_lsd = re.search(r'"LSD",\[\],\{"token":"([^"]+)"\}', html)
    m_uid = re.search(r'"userID":"(\d+)"', html) or re.search(r'"target_user_id":"(\d+)"', html)
    if not m_lsd or not m_uid:
        return

    lsd_token = m_lsd.group(1)
    user_id = m_uid.group(1)
    gql_headers = {
        **headers,
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-FB-LSD': lsd_token,
        'X-IG-App-ID': '238260118697367',
    }

    for _ in range(3):
        if len(results) >= max_posts or not cursor:
            break
        variables = json.dumps({
            'userID': user_id,
            'after': cursor,
            'before': None,
            'first': 15,
            'last': None
        })
        resp = requests.post(
            'https://www.threads.net/api/graphql',
            headers=gql_headers,
            data={
                'lsd': lsd_token,
                'variables': variables,
                'doc_id': '25568623819432257'
            },
            timeout=10
        )
        if not resp.ok:
            break
        try:
            payload = resp.json()
        except ValueError:
            break
        prev_len = len(results)
        _walk_thread_items(payload, results, seen)
        next_cursor, has_next = _find_pagination_info(payload)
        if not has_next or not next_cursor or len(results) == prev_len:
            break
        cursor = next_cursor


def _extract_posts_from_html(html: str, default_username: str, headers: dict = None, max_posts: int = 50) -> list:
    """Extract Threads posts/replies from SSR JSON scripts, optional GraphQL pagination, or OpenGraph fallback."""
    results = []
    seen = set()
    cursor = None

    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL):
        raw_json = m.group(1).strip()
        if 'thread_items' not in raw_json:
            continue
        try:
            data = json.loads(raw_json)
            _walk_thread_items(data, results, seen)
            if not cursor:
                c, has_next = _find_pagination_info(data)
                if has_next and c:
                    cursor = c
        except json.JSONDecodeError:
            continue

    if results and cursor and headers and len(results) < max_posts:
        try:
            _fetch_more_graphql(html, cursor, headers, max_posts, results, seen)
        except Exception:
            pass

    if results:
        return results[:max_posts]

    # Fallback: OpenGraph meta description (sering tersedia pada post publik Threads)
    m_desc = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', html)
    if m_desc:
        desc = m_desc.group(1).strip()
        if desc and 'Threads' not in desc[:20]:
            results.append({
                'username': default_username,
                'content': desc,
                'likes': 0,
                'shares': 0,
                'created_at': datetime.utcnow()
            })
    return results


def _fetch_threads_via_api(token: str, max_posts: int = 25) -> dict:
    """Fetch authenticated user's Threads posts via official Meta Threads Graph API."""
    url = 'https://graph.threads.net/v1.0/me/threads'
    params = {
        'fields': 'id,text,timestamp,username,permalink',
        'limit': max_posts,
        'access_token': token
    }
    resp = requests.get(url, params=params, timeout=12)
    resp.raise_for_status()
    items = resp.json().get('data', [])
    posts = []
    for it in items:
        text = (it.get('text') or '').strip()
        if not text:
            continue
        ts = it.get('timestamp', '')[:19]
        created_at = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S') if ts else datetime.utcnow()
        uname = it.get('username') or 'threads_user'
        posts.append({
            'username': f'@{uname}',
            'content': text,
            'likes': 0,
            'shares': 0,
            'created_at': created_at
        })
    if not posts:
        raise ValueError('Tidak ada post teks yang ditemukan dari Threads API.')
    return {
        'mode': 'threads',
        'target': posts[0]['username'],
        'kind': 'api',
        'total_likes': 0,
        'total_posts': len(posts),
        'posts': posts
    }


def analyze_threads_url(user_input: str, max_posts: int = 50) -> dict:
    """Fetch public Threads post/replies or profile posts for sentiment analysis."""
    info = parse_threads_input(user_input)
    token = os.getenv('THREADS_ACCESS_TOKEN')
    if token and info['kind'] == 'profile' and info['username'] == '@me':
        return _fetch_threads_via_api(token, max_posts=max_posts)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Fetch-Mode': 'navigate'
    }
    resp = requests.get(info['url'], headers=headers, timeout=12)
    if resp.status_code in (401, 403, 429):
        raise ValueError(
            f"Threads membatasi akses publik (HTTP {resp.status_code}). "
            "Anda dapat mengisi THREADS_ACCESS_TOKEN di .env atau menyalin teks thread ke Quick Text Analyzer."
        )
    resp.raise_for_status()

    posts = _extract_posts_from_html(resp.text, info['username'], headers=headers, max_posts=max_posts)
    if not posts:
        raise ValueError(
            'Tidak dapat mengekstrak konten/balasan dari URL Threads tersebut '
            '(kemungkinan halaman memerlukan login atau JavaScript penuh).'
        )

    return {
        'mode': 'threads',
        'target': info['username'],
        'kind': info['kind'],
        'url': info['url'],
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }
