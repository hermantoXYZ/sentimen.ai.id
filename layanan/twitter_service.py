import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import requests


def parse_twitter_input(user_input: str) -> dict:
    """Parse X/Twitter tweet URL, profile URL, or @username."""
    raw = user_input.strip()
    if not raw:
        raise ValueError('Masukkan URL Twitter/X atau @username.')

    if raw.startswith('http://') or raw.startswith('https://'):
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if 'twitter.com' not in host and 'x.com' not in host:
            raise ValueError('URL harus berasal dari x.com atau twitter.com.')
        path = parsed.path.strip('/')
        m_status = re.match(r'^([^/]+)/status/(\d+)', path)
        if m_status:
            return {
                'kind': 'tweet',
                'username': f'@{m_status.group(1)}',
                'tweet_id': m_status.group(2),
                'url': raw
            }
        m_user = re.match(r'^@?([^/]+)$', path)
        if m_user:
            return {
                'kind': 'profile',
                'username': f'@{m_user.group(1)}',
                'tweet_id': None,
                'url': f'https://x.com/{m_user.group(1)}'
            }
        raise ValueError('Format URL Twitter/X tidak dikenali.')

    username = raw.lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9_]{1,15}', username):
        raise ValueError('Format username Twitter/X tidak valid.')
    return {
        'kind': 'profile',
        'username': f'@{username}',
        'tweet_id': None,
        'url': f'https://x.com/{username}'
    }


def _extract_syndication_timeline(html: str, default_username: str) -> list:
    """Extract tweets from Twitter syndication timeline __NEXT_DATA__ JSON."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    entries = (
        data.get('props', {})
        .get('pageProps', {})
        .get('timeline', {})
        .get('entries', [])
    )
    posts = []
    for entry in entries:
        tweet = entry.get('content', {}).get('tweet') if isinstance(entry, dict) else None
        if not isinstance(tweet, dict):
            continue
        text = (tweet.get('full_text') or tweet.get('text') or '').strip()
        if not text:
            continue
        user = tweet.get('user') or {}
        uname = user.get('screen_name') or default_username.lstrip('@')
        posts.append({
            'username': f'@{uname}',
            'content': text,
            'likes': int(tweet.get('favorite_count') or 0),
            'shares': int(tweet.get('retweet_count') or 0),
            'created_at': datetime.utcnow()
        })
    return posts


def _fetch_twitter_via_api(info: dict, bearer: str, max_items: int = 25) -> dict:
    """Fetch tweet/replies or user timeline using official X API v2."""
    headers = {'Authorization': f'Bearer {bearer}'}
    posts = []

    if info['kind'] == 'tweet' and info['tweet_id']:
        r = requests.get(
            'https://api.twitter.com/2/tweets/search/recent',
            headers=headers,
            params={
                'query': f"conversation_id:{info['tweet_id']}",
                'max_results': min(max_items, 100),
                'tweet.fields': 'created_at,public_metrics,author_id',
                'expansions': 'author_id',
                'user.fields': 'username'
            },
            timeout=12
        )
        r.raise_for_status()
        payload = r.json()
        users = {u['id']: u['username'] for u in payload.get('includes', {}).get('users', [])}
        for tw in payload.get('data', []):
            metrics = tw.get('public_metrics', {})
            uname = users.get(tw.get('author_id'), info['username'].lstrip('@'))
            posts.append({
                'username': f'@{uname}',
                'content': tw.get('text', '').strip(),
                'likes': int(metrics.get('like_count', 0)),
                'shares': int(metrics.get('retweet_count', 0)),
                'created_at': datetime.strptime(tw['created_at'][:19], '%Y-%m-%dT%H:%M:%S') if tw.get('created_at') else datetime.utcnow()
            })
    else:
        uname = info['username'].lstrip('@')
        u_resp = requests.get(f'https://api.twitter.com/2/users/by/username/{uname}', headers=headers, timeout=10)
        u_resp.raise_for_status()
        uid = u_resp.json().get('data', {}).get('id')
        if not uid:
            raise ValueError(f'Akun {info["username"]} tidak ditemukan.')
        t_resp = requests.get(
            f'https://api.twitter.com/2/users/{uid}/tweets',
            headers=headers,
            params={'max_results': min(max_items, 100), 'tweet.fields': 'created_at,public_metrics'},
            timeout=12
        )
        t_resp.raise_for_status()
        for tw in t_resp.json().get('data', []):
            metrics = tw.get('public_metrics', {})
            posts.append({
                'username': info['username'],
                'content': tw.get('text', '').strip(),
                'likes': int(metrics.get('like_count', 0)),
                'shares': int(metrics.get('retweet_count', 0)),
                'created_at': datetime.strptime(tw['created_at'][:19], '%Y-%m-%dT%H:%M:%S') if tw.get('created_at') else datetime.utcnow()
            })

    if not posts:
        raise ValueError('Tidak ada tweet atau balasan yang ditemukan.')
    return {
        'mode': 'twitter',
        'target': info['username'],
        'kind': info['kind'],
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }


def analyze_twitter_url(user_input: str, max_items: int = 25) -> dict:
    """Analyze X/Twitter tweet or profile timeline via API v2 or public syndication."""
    info = parse_twitter_input(user_input)
    bearer = os.getenv('TWITTER_BEARER_TOKEN')
    if bearer:
        return _fetch_twitter_via_api(info, bearer, max_items=max_items)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    posts = []
    if info['kind'] == 'tweet' and info['tweet_id']:
        r = requests.get(
            'https://cdn.syndication.twimg.com/tweet-result',
            params={'id': info['tweet_id'], 'token': '0'},
            headers=headers,
            timeout=10
        )
        if r.ok:
            tw = r.json()
            text = (tw.get('text') or '').strip()
            if text:
                uname = tw.get('user', {}).get('screen_name') or info['username'].lstrip('@')
                posts.append({
                    'username': f'@{uname}',
                    'content': text,
                    'likes': int(tw.get('favorite_count') or 0),
                    'shares': int(tw.get('conversation_count') or 0),
                    'created_at': datetime.utcnow()
                })
    else:
        uname = info['username'].lstrip('@')
        r = requests.get(
            f'https://syndication.twitter.com/srv/timeline-profile/screen-name/{uname}',
            headers=headers,
            timeout=12
        )
        if r.ok:
            posts = _extract_syndication_timeline(r.text, info['username'])[:max_items]

    if not posts:
        raise ValueError(
            'X/Twitter membatasi akses publik tanpa login/API. '
            'Anda dapat mengisi TWITTER_BEARER_TOKEN di .env atau menempelkan teks tweet di Quick Text Analyzer.'
        )

    return {
        'mode': 'twitter',
        'target': info['username'],
        'kind': info['kind'],
        'total_likes': sum(p['likes'] for p in posts),
        'total_posts': len(posts),
        'posts': posts
    }
