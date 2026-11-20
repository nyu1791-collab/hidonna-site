"""ヒドンナ公式ポータル用 軽量Webサーバー + 全5媒体（Kick・ふわっち・ツイキャス・X・YouTube）最新3件取得API。

すべて無料・APIキー不要の公開エンドポイントを使用。
起動:
  python server.py [--host 127.0.0.1] [--port 8788]
"""
from __future__ import annotations

import argparse
import errno
import html as html_lib
import json
import re
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))
UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/136.0.0.0 Safari/537.36'
)

CACHE_TTL_SEC = 45.0
_CACHE_LOCK = threading.Lock()
_CACHE: dict = {'at': 0.0, 'data': None}

FALLBACK_YOUTUBE = [
    {
        'id': 'I7eLLRDpNFc',
        'title': 'ヒドンナお一人サスペンス劇場　エンドロールver.',
        'published': '2026-07-09',
        'url': 'https://www.youtube.com/watch?v=I7eLLRDpNFc',
        'thumbnail': 'https://i.ytimg.com/vi/I7eLLRDpNFc/hqdefault.jpg',
    },
    {
        'id': '7QR5TZdWfRQ',
        'title': 'エグプリフェス2026',
        'published': '2026-06-21',
        'url': 'https://www.youtube.com/watch?v=7QR5TZdWfRQ',
        'thumbnail': 'https://i.ytimg.com/vi/7QR5TZdWfRQ/hqdefault.jpg',
    },
    {
        'id': 'L5T0R9id454',
        'title': '2016→2026 ヒドンナ配信10周年記念｜10年間の感謝を込めて',
        'published': '2026-04-23',
        'url': 'https://www.youtube.com/watch?v=L5T0R9id454',
        'thumbnail': 'https://i.ytimg.com/vi/L5T0R9id454/hqdefault.jpg',
    },
]

FALLBACK_KICK_VODS = [
    {
        'id': '01a1f46d-fbb8-7fcc-b6e2-d67918c8003a',
        'title': 'とあるキッカーズのメンバーと会うので見てて',
        'date': '2026-11-20',
        'duration': '5:24:23',
        'category': 'IRL',
        'url': 'https://kick.com/hidonna/videos/01a1f46d-fbb8-7fcc-b6e2-d67918c8003a',
        'thumbnail': 'https://images.kick.com/video_thumbnails/S7SprJJLNbY0/2HrlLiEAMchU/720.webp',
    },
    {
        'id': '01a1ef4e-b820-7336-b615-17043f3ea280',
        'title': 'ランジェリーで露出魔さんぽ',
        'date': '2026-11-19',
        'duration': '4:33:09',
        'category': 'IRL',
        'url': 'https://kick.com/hidonna/videos/01a1ef4e-b820-7336-b615-17043f3ea280',
        'thumbnail': 'https://images.kick.com/video_thumbnails/S7SprJJLNbY0/aEL9prSac7H9/720.webp',
    },
    {
        'id': '01a1ea14-b0f8-7341-ab64-e8d680193357',
        'title': '行方不明の配信者と失踪者を探しに行く　静岡へ',
        'date': '2026-11-18',
        'duration': '6:44:44',
        'category': 'IRL',
        'url': 'https://kick.com/hidonna/videos/01a1ea14-b0f8-7341-ab64-e8d680193357',
        'thumbnail': 'https://images.kick.com/video_thumbnails/S7SprJJLNbY0/iuhtmTkQ6wgm/720.webp',
    },
]

FALLBACK_WHO_ARCHIVES = [
    {
        'id': '77643976',
        'title': 'さようなら洗濯機',
        'date': '2026-11-12',
        'duration': '1:30:50',
        'views': 4869,
        'url': 'https://whowatch.tv/archives/77643976',
        'thumbnail': 'https://img.whowatch.tv/user_files/1948697/user_live_thumbnail_image/1794398242613.jpeg',
    },
    {
        'id': '77638766',
        'title': '【23時バビエちゃん】さようなら洗濯機',
        'date': '2026-11-11',
        'duration': '3:09:16',
        'views': 7632,
        'url': 'https://whowatch.tv/archives/77638766',
        'thumbnail': 'https://img.whowatch.tv/user_files/1948697/user_live_thumbnail_image/1794398242613.jpeg',
    },
    {
        'id': '77616318',
        'title': 'ポッキーの日1111本配ります',
        'date': '2026-11-11',
        'duration': '1:09:49',
        'views': 3843,
        'url': 'https://whowatch.tv/archives/77616318',
        'thumbnail': 'https://img.whowatch.tv/user_files/1948697/user_live_thumbnail_image/1794312069417.jpeg',
    },
]

FALLBACK_TWITCASTING_MOVIES = [
    {
        'id': '843145216',
        'title': 'モイ！iPhoneからキャス配信中 - / 失踪者を探しに静岡へ',
        'date': '2026-11-19 22:43',
        'duration': '1:47:28',
        'views': 4047,
        'url': 'https://twitcasting.tv/hid0nna/movie/843145216',
        'thumbnail': 'https://imagegw03.twitcasting.tv/image3/image.twitcasting.tv/image159_1/00/60/32416000-1.jpg',
    },
    {
        'id': '843141878',
        'title': 'モイ！iPhoneからキャス配信中 - / 失踪者を探しに静岡へ',
        'date': '2026-11-19 21:41',
        'duration': '',
        'views': 2438,
        'url': 'https://twitcasting.tv/hid0nna/movie/843141878',
        'thumbnail': 'https://imagegw03.twitcasting.tv/image3/image.twitcasting.tv/image158_1/f6/52/324152f6-1.jpg',
    },
    {
        'id': '843110693',
        'title': 'モイ！iPhoneからキャス配信中 - / 失踪者を探しに静岡へ',
        'date': '2026-11-18 23:18',
        'duration': '1:20:32',
        'views': 3510,
        'url': 'https://twitcasting.tv/hid0nna/movie/843110693',
        'thumbnail': 'https://imagegw03.twitcasting.tv/image3/image.twitcasting.tv/image158_1/25/d9/3240d925-1.jpg',
    },
]


def _strip_whowatch_schedule_text(text: str) -> str:
    """廃止されたふわっち定時配信の旧記載をプロフィール文から自然に除去する。"""
    if not text:
        return ''
    out_lines = []
    for raw in str(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.search(r'^ふわっち\s*[:：]\s*毎日.*配信中$', line):
            continue
        line = re.sub(r'夜?\s*20[:：]00から24[:：]00まで定時配信をやっています[！!。]*', '', line)
        line = re.sub(r'ふわっちにて20時35分から定時で配信中[。！!]*', '', line)
        line = re.sub(r'ふわっちでは毎晩決まった時間に[、,\s]*', '', line)
        line = line.strip()
        if line:
            out_lines.append(line)
    return '\n'.join(out_lines)


def _http_get(url: str, timeout: float = 8.0) -> str:
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json, application/xml, text/xml, */*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', 'replace')
    except Exception:
        try:
            from curl_cffi import requests as cffi_requests
            r = cffi_requests.get(url, headers=headers, impersonate='chrome', timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            raise


def _fmt_duration(seconds: int | float | None) -> str:
    if not seconds or seconds <= 0:
        return ''
    sec = int(round(seconds))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'


def _iso_to_jst_date(iso_str: str | None) -> str:
    if not iso_str:
        return ''
    try:
        s = iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(s).astimezone(JST)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return str(iso_str)[:10]


def _epoch_ms_to_jst_date(ms: int | float | None) -> str:
    if not ms:
        return ''
    try:
        dt = datetime.fromtimestamp(float(ms) / 1000.0, tz=JST)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return ''


def _fetch_kick() -> dict:
    out = {
        'is_live': False,
        'title': '',
        'viewers': 0,
        'category': '',
        'thumbnail': '',
        'followers': 20740,
        'username': 'HIDONNA',
        'avatar': './assets/avatar_kick.webp',
        'bio': (
            '女装配信者\n'
            'KICK: 配信開始！主に深夜から朝方にかけて配信\n'
            '複数のプラットフォームで活動中の女装配信者。'
            'KICKでは夜更かし派の視聴者に向けて深夜・早朝の時間帯に配信を展開中。'
        ),
        'url': 'https://kick.com/hidonna',
        'videos': list(FALLBACK_KICK_VODS),
        'status_ok': False,
    }
    channel_id = 58253068
    for ep in (
        'https://kick.com/api/v2/channels/hidonna',
        'https://kick.com/api/v1/channels/hidonna',
    ):
        try:
            d = json.loads(_http_get(ep, timeout=8.0))
            out['status_ok'] = True
            if d.get('id'):
                channel_id = int(d['id'])
            if d.get('followers_count') is not None:
                out['followers'] = int(d['followers_count'])
            u = d.get('user') or {}
            if u.get('username'):
                out['username'] = str(u['username'])
            if u.get('profile_pic'):
                out['avatar'] = str(u['profile_pic'])
            if u.get('bio'):
                cleaned = _strip_whowatch_schedule_text(str(u['bio']))
                if cleaned:
                    out['bio'] = cleaned
            ls = d.get('livestream')
            if isinstance(ls, dict) and ls.get('is_live') is not False:
                out['is_live'] = True
                out['title'] = str(ls.get('session_title') or '').strip()
                out['viewers'] = int(ls.get('viewer_count') or 0)
                cats = ls.get('categories') or []
                if cats and isinstance(cats[0], dict):
                    out['category'] = str(cats[0].get('name') or '')
                thumb = ls.get('thumbnail')
                if isinstance(thumb, dict):
                    out['thumbnail'] = str(thumb.get('url') or thumb.get('src') or '')
                elif isinstance(thumb, str):
                    out['thumbnail'] = thumb
            break
        except Exception:
            continue

    # Kick 最新配信アーカイブ 3本（正規VOD UUID が取れる web.kick.com API を使用）
    try:
        vd = json.loads(_http_get(f'https://web.kick.com/api/v1/channels/{channel_id}/videos', timeout=8.0))
        raw_list = vd.get('data') if isinstance(vd, dict) else (vd if isinstance(vd, list) else [])
        vods = []
        for item in raw_list:
            if not isinstance(item, dict) or item.get('is_live'):
                continue
            vid = str(item.get('id') or '').strip()
            if not vid:
                continue
            th = item.get('thumbnail')
            thumb_url = str(th.get('src') or th.get('url') or '') if isinstance(th, dict) else str(th or '')
            cat = (item.get('category') or {}).get('name') if isinstance(item.get('category'), dict) else ''
            vods.append({
                'id': vid,
                'title': str(item.get('title') or 'Kick 過去配信').strip(),
                'date': _iso_to_jst_date(item.get('start_time') or item.get('created_at')),
                'duration': _fmt_duration(item.get('duration')),
                'category': str(cat or ''),
                'url': f'https://kick.com/hidonna/videos/{vid}',
                'thumbnail': thumb_url,
            })
            if len(vods) >= 3:
                break
        if vods:
            out['videos'] = vods
    except Exception:
        pass
    return out


def _fetch_whowatch() -> dict:
    out = {
        'is_live': False,
        'title': '',
        'viewers': 0,
        'thumbnail': '',
        'followers': 57837,
        'name': 'ヒドンナ@どやさ',
        'avatar': './assets/avatar_whowatch.jpg',
        'bio': '東京都足立区在住。女装家です。',
        'url': 'https://whowatch.tv/profile/t:hid0nna',
        'archives': list(FALLBACK_WHO_ARCHIVES),
        'status_ok': False,
    }
    user_id = 1948697
    try:
        d = json.loads(_http_get('https://api.whowatch.tv/users/t:hid0nna/profile', timeout=8.0))
        out['status_ok'] = True
        if d.get('user_id'):
            user_id = int(d['user_id'])
        if d.get('name'):
            out['name'] = str(d['name'])
        if d.get('follower_count') is not None:
            out['followers'] = int(d['follower_count'])
        if d.get('icon_url'):
            out['avatar'] = str(d['icon_url'])
        if d.get('description'):
            parts = [p.strip() for p in str(d['description']).splitlines() if p.strip()]
            intro = [p for p in parts if not p.startswith(('■', 'http', 'YOUTUBE'))]
            if intro:
                cleaned = _strip_whowatch_schedule_text('\n'.join(intro))
                if cleaned:
                    out['bio'] = cleaned
        lv = d.get('live')
        if isinstance(lv, dict) and lv.get('id'):
            live_id = lv['id']
            out['is_live'] = True
            out['title'] = str(lv.get('title') or '').strip()
            out['url'] = f'https://whowatch.tv/viewer/{live_id}'
            try:
                detail = json.loads(_http_get(f'https://api.whowatch.tv/lives/{live_id}', timeout=5.0))
                lobj = detail.get('live') if isinstance(detail.get('live'), dict) else detail
                if isinstance(lobj, dict):
                    if lobj.get('view_count') is not None:
                        out['viewers'] = int(lobj['view_count'])
                    elif lobj.get('total_view_count') is not None:
                        out['viewers'] = int(lobj['total_view_count'])
                    thumb = lobj.get('latest_thumbnail_url') or lobj.get('thumbnail_url') or ''
                    if thumb:
                        out['thumbnail'] = str(thumb)
            except Exception:
                pass
    except Exception:
        pass

    # ふわっち 最新配信履歴 3本
    try:
        lh = json.loads(_http_get(f'https://api.whowatch.tv/users/{user_id}/live_histories', timeout=8.0))
        if isinstance(lh, list):
            arcs = []
            for item in lh[:3]:
                if not isinstance(item, dict) or not item.get('id'):
                    continue
                aid = str(item['id'])
                arcs.append({
                    'id': aid,
                    'title': str(item.get('title') or 'ふわっち配信アーカイブ').strip(),
                    'date': _epoch_ms_to_jst_date(item.get('started_at')),
                    'duration': _fmt_duration(item.get('running_time')),
                    'views': int(item.get('total_view_count') or 0),
                    'url': f'https://whowatch.tv/archives/{aid}',
                    'thumbnail': str(item.get('thumbnail_url') or item.get('latest_thumbnail_url') or './assets/avatar_whowatch.jpg'),
                })
            if arcs:
                out['archives'] = arcs
    except Exception:
        pass
    return out


def _fetch_twitcasting() -> dict:
    """ツイキャス（@hid0nna）のリアルタイム配信判定＋最新録画3本＋プロフィールを無料取得。"""
    out = {
        'is_live': False,
        'title': '',
        'viewers': 0,
        'thumbnail': '',
        'supporters': '2.1k',
        'level': 39,
        'name': 'HIDONNA',
        'screen_id': '@hid0nna',
        'avatar': './assets/avatar_twitcasting.jpg',
        'bio': '東京都足立区在住。女装家。',
        'url': 'https://twitcasting.tv/hid0nna',
        'movies': list(FALLBACK_TWITCASTING_MOVIES),
        'status_ok': False,
    }
    # 1) リアルタイム LIVE / OFFLINE 判定（無料公開 streamserver.php）
    try:
        ss = json.loads(_http_get('https://twitcasting.tv/streamserver.php?target=hid0nna&mode=client', timeout=7.0))
        mv = ss.get('movie') if isinstance(ss, dict) else None
        if isinstance(mv, dict):
            out['status_ok'] = True
            if mv.get('live') is True:
                out['is_live'] = True
                if mv.get('id'):
                    out['url'] = f'https://twitcasting.tv/hid0nna/movie/{mv["id"]}'
    except Exception:
        pass

    # 2) プロフィール・サポーター数・アバター・ライブ時タイトル＆サムネイル
    try:
        page = _http_get('https://twitcasting.tv/hid0nna', timeout=8.0)
        out['status_ok'] = True
        m_name = re.search(r'class="tw-user-nav2-name"[^>]*>(.*?)<', page, re.S)
        if m_name and m_name.group(1).strip():
            out['name'] = html_lib.unescape(m_name.group(1).strip())
        m_av = re.search(r'class="tw-user-nav2-icon"[^>]*>.*?<img[^>]+src="([^"]+)"', page, re.S)
        if m_av and m_av.group(1).strip():
            out['avatar'] = html_lib.unescape(m_av.group(1).strip())
        m_sup = re.search(r'/hid0nna/backers/"[^>]*>.*?class=[\'"]tw-user-nav-list-count[\'"][^>]*>([^<]+)<', page, re.S)
        if m_sup and m_sup.group(1).strip():
            out['supporters'] = m_sup.group(1).strip()
        m_lv = re.search(r'レベル\s*(\d+)', page)
        if m_lv:
            out['level'] = int(m_lv.group(1))
        m_bio = re.search(r'id="authorcomment"[^>]*>(.*?)</div>', page, re.S)
        if m_bio:
            raw_bio = html_lib.unescape(re.sub(r'<[^>]+>', '', m_bio.group(1))).strip()
            cleaned = _strip_whowatch_schedule_text(raw_bio)
            if cleaned:
                out['bio'] = cleaned
        if out['is_live']:
            m_title = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', page)
            if m_title and m_title.group(1).strip():
                out['title'] = html_lib.unescape(m_title.group(1).strip())
            m_og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', page)
            if m_og and m_og.group(1).strip():
                out['thumbnail'] = html_lib.unescape(m_og.group(1).strip())
    except Exception:
        pass

    # 3) 最新録画（アーカイブ）3本
    try:
        sh = _http_get('https://twitcasting.tv/hid0nna/show/', timeout=8.0)
        cards = re.findall(r'<a class="tw-movie-thumbnail2"[^>]*href="(/hid0nna/movie/(\d+))"[^>]*>(.*?)</a>', sh, re.S)
        movies = []
        seen = set()
        for href, mid, body in cards:
            if mid in seen:
                continue
            seen.add(mid)
            m_img = re.search(r'class="tw-movie-thumbnail2-image"[^>]*src="([^"]+)"(?:[^>]*title="([^"]*)")?', body)
            m_dur = re.search(r'class="tw-movie-thumbnail2-duration"[^>]*>(.*?)</span>', body, re.S)
            m_view = re.search(r'class="tw-movie-thumbnail2-view"[^>]*>(.*?)</span>', body, re.S)
            m_title = re.search(r'class="tw-movie-thumbnail2-title[^"]*"[^>]*>(.*?)</', body, re.S)

            thumb = ''
            date_str = ''
            if m_img:
                thumb = html_lib.unescape(m_img.group(1)).replace('-s.jpg', '.jpg')
                raw_date = (m_img.group(2) or '').strip()
                if raw_date:
                    date_str = raw_date.replace('/', '-')[:16]
            views = 0
            if m_view:
                digits = re.sub(r'[^\d]', '', m_view.group(1))
                if digits:
                    views = int(digits)
            title = 'ツイキャス配信アーカイブ'
            if m_title:
                t_clean = html_lib.unescape(re.sub(r'<[^>]+>', '', m_title.group(1))).replace('\xa0', ' ').strip()
                if t_clean:
                    title = t_clean

            movies.append({
                'id': mid,
                'title': title,
                'date': date_str,
                'duration': m_dur.group(1).strip() if m_dur else '',
                'views': views,
                'url': f'https://twitcasting.tv{href}',
                'thumbnail': thumb or './assets/avatar_twitcasting.jpg',
            })
            if len(movies) >= 3:
                break
        if movies:
            out['movies'] = movies
    except Exception:
        pass
    return out


def _fetch_x_posts() -> dict:
    """x_posts.json をベースに、無料公開の fxtwitter API で最新いいね数・表示回数・画像を自動更新。"""
    xp = ROOT / 'x_posts.json'
    posts = []
    if xp.exists():
        try:
            posts = json.loads(xp.read_text(encoding='utf-8'))
        except Exception:
            posts = []

    enriched = []
    for raw in posts[:3]:
        item = dict(raw)
        pid = str(item.get('id') or '').strip()
        if pid:
            try:
                fx = json.loads(_http_get(f'https://api.fxtwitter.com/hid0nna/status/{pid}', timeout=5.0))
                tw = fx.get('tweet') if isinstance(fx, dict) else None
                if isinstance(tw, dict):
                    if tw.get('likes') is not None:
                        item['likes'] = int(tw['likes'])
                    if tw.get('retweets') is not None:
                        item['reposts'] = int(tw['retweets'])
                    if tw.get('views') is not None:
                        item['views'] = int(tw['views'])
                    txt = str(tw.get('text') or '').strip()
                    txt_no_urls = re.sub(r'https?://\S+', '', txt).strip()
                    # URLのみの投稿はそのままURLを露出させず分かりやすい日本語タイトルを維持
                    if txt_no_urls:
                        item['text'] = txt_no_urls
                    media = (tw.get('media') or {}).get('photos') or []
                    if media and isinstance(media[0], dict) and media[0].get('url'):
                        murl = str(media[0]['url']).replace('name=orig', 'name=medium')
                        item['image'] = murl
            except Exception:
                pass
        enriched.append(item)

    return {
        'handle': '@hid0nna',
        'url': 'https://x.com/hid0nna',
        'posts': enriched,
        'status_ok': bool(enriched),
    }


def _fetch_youtube() -> dict:
    """YouTube のショート動画を除外した通常動画（UULF プレイリスト）から最新3本を取得。"""
    out = {
        'channel_name': 'ヒドンナちゃんねる',
        'channel_url': 'https://www.youtube.com/channel/UCzc8gfCm5pMSkyj9bqHKieQ',
        'videos': list(FALLBACK_YOUTUBE),
        'status_ok': False,
    }
    ns = {
        'a': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
    }
    for feed_url in (
        'https://www.youtube.com/feeds/videos.xml?playlist_id=UULFzc8gfCm5pMSkyj9bqHKieQ',
        'https://www.youtube.com/feeds/videos.xml?channel_id=UCzc8gfCm5pMSkyj9bqHKieQ',
    ):
        try:
            body = _http_get(feed_url, timeout=8.0)
            root = ET.fromstring(body)
            vids = []
            for entry in root.findall('a:entry', ns):
                link_el = entry.find('a:link', ns)
                href = (link_el.attrib.get('href') if link_el is not None else '') or ''
                if '/shorts/' in href:
                    continue
                vid = (entry.findtext('yt:videoId', '', ns) or '').strip()
                title = (entry.findtext('a:title', '', ns) or '').strip()
                pub = (entry.findtext('a:published', '', ns) or '')[:10]
                if vid:
                    vids.append({
                        'id': vid,
                        'title': title,
                        'published': pub,
                        'url': f'https://www.youtube.com/watch?v={vid}',
                        'thumbnail': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
                    })
                if len(vids) >= 3:
                    break
            if vids:
                out['videos'] = vids
                out['status_ok'] = True
                break
        except Exception:
            continue
    return out


def get_live_status(force: bool = False) -> dict:
    now = time.time()
    with _CACHE_LOCK:
        if not force and _CACHE['data'] is not None and (now - _CACHE['at']) < CACHE_TTL_SEC:
            return _CACHE['data']

    results: dict = {}
    threads = [
        threading.Thread(target=lambda: results.__setitem__('kick', _fetch_kick()), daemon=True),
        threading.Thread(target=lambda: results.__setitem__('whowatch', _fetch_whowatch()), daemon=True),
        threading.Thread(target=lambda: results.__setitem__('twitcasting', _fetch_twitcasting()), daemon=True),
        threading.Thread(target=lambda: results.__setitem__('x', _fetch_x_posts()), daemon=True),
        threading.Thread(target=lambda: results.__setitem__('youtube', _fetch_youtube()), daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    payload = {
        'fetched_at': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST'),
        'kick': results.get('kick') or _fetch_kick(),
        'whowatch': results.get('whowatch') or _fetch_whowatch(),
        'twitcasting': results.get('twitcasting') or _fetch_twitcasting(),
        'x': results.get('x') or _fetch_x_posts(),
        'youtube': results.get('youtube') or _fetch_youtube(),
    }
    with _CACHE_LOCK:
        _CACHE['at'] = time.time()
        _CACHE['data'] = payload
    return payload


class SafeThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


class PortalHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        path = urlparse(self.path).path
        if path.startswith(('/assets/', '/fonts/')):
            self.send_header('Cache-Control', 'public, max-age=300')
        else:
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/live-status':
            qs = parse_qs(parsed.query)
            force = qs.get('refresh', ['0'])[0] in ('1', 'true', 'yes')
            data = get_live_status(force=force)
            raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            return
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, format, *args):
        return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8788)
    a = ap.parse_args()
    try:
        srv = SafeThreadingHTTPServer((a.host, a.port), PortalHandler)
    except OSError as e:
        if e.errno in (errno.EADDRINUSE, 10048):
            print(f'Port {a.port} already active (reusing running server).', flush=True)
            return
        raise
    print(f'HIDONNA Portal Server listening on http://{a.host}:{a.port}/', flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
