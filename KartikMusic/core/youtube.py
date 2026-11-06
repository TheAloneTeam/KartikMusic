#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import random
import re
import urllib.parse
from typing import Any

import aiohttp
from py_yt import Playlist, Recommendations, VideosSearch

from KartikMusic import logger
from KartikMusic.helpers import Track, utils

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# Use environment variables for configuration
API_URL = os.getenv("API_URL", "https://www.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "riteshfree7bf33e2c0825084d93617e83")

DEFAULT_API_URL = API_URL
DEFAULT_API_KEY = API_KEY


def _safe_search_ytdlp(query: str) -> dict[str, Any]:
    """Local fallback using yt-dlp to search and extract video info."""
    if yt_dlp is None:
        return {"result": []}
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["mweb", "ios", "android"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries", [])
            if entries and entries[0]:
                entry = entries[0]
                vidid = entry.get("id")
                title = entry.get("title", "Track")
                duration = entry.get("duration", 0)
                d_str = "00:00"
                if duration:
                    m, s = divmod(int(duration), 60)
                    h, m = divmod(m, 60)
                    d_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                thumbnails = entry.get("thumbnails", [])
                thumb = (
                    thumbnails[0]["url"].split("?")[0]
                    if thumbnails
                    else f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
                )
                return {
                    "result": [
                        {
                            "id": vidid,
                            "title": title,
                            "link": f"https://www.youtube.com/watch?v={vidid}",
                            "duration": d_str,
                            "thumbnails": [{"url": thumb}],
                        }
                    ]
                }
        except Exception:
            pass
    return {"result": []}


async def download_assistant(query: str, dl_type: str) -> str:
    """Helper to get stream URL from the API"""
    safe_query = urllib.parse.quote(query)
    ext = "mp3" if dl_type == "audio" else "mp4"
    if API_KEY:
        # Use query_masked path to satisfy bots that look for direct file extensions
        url = f"{API_URL}/downloads/{API_KEY}/{safe_query}.{ext}"
    else:
        url = f"{API_URL}/downloads/stream?query={safe_query}&dl_type={dl_type}"
    return url


class YouTube:
    """
    Universal media player and extractor supporting 80+ platforms:
    YouTube, Spotify, Apple Music, JioSaavn, Wynk, Hungama, Amazon Music,
    Soundcloud, Deezer, Gaana, Resso, Tidal, Audiomack, Bandcamp, Boomplay,
    Mixcloud, Anghami, Qobuz, Pandora, iHeart, TuneIn, Napster, Last.fm,
    Shazam, Genius, ReverbNation, HearThis.at, Apple Podcasts, Google Podcasts,
    Vimeo, Dailymotion, Bilibili, Twitch, Kick, Rumble, Streamable, OK.ru, Coub,
    Odysee, Bitchute, Ted, Loom, Rutube, Archive.org, Youku, iQiyi, Instagram,
    TikTok/Douyin, Twitter/X, Facebook, Pinterest, Reddit, Snapchat, Threads,
    Tumblr, VK, Likee, Triller, Kwai, ShareChat, Moj, Josh, Bluesky, Mastodon,
    Weibo, Kuaishou, Patreon, Discord, Line, LinkedIn, Terabox, Google Drive,
    Dropbox, OneDrive, Mediafire, Mega, Yandex Disk, Catbox, QQ Music, NetEase,
    Kugou, Kuwo, Zing MP3, NhacCuaTui, Joox, and direct audio/video streams.
    """

    PLATFORM_PATTERNS = [
        # --- Primary Music & Audio Services ---
        ("spotify", r"(?:open\.|music\.)?spotify\.com|spotify:"),
        ("applemusic", r"(?:music|itunes)\.apple\.com"),
        ("jiosaavn", r"(?:jiosaavn|saavn)\.com"),
        ("youtube", r"(?:youtube\.com|youtu\.be)"),
        ("soundcloud", r"soundcloud\.com"),
        ("deezer", r"deezer\.com"),
        ("gaana", r"gaana\.com"),
        ("resso", r"resso\.(?:com|link)"),
        ("tidal", r"tidal\.com"),
        ("audiomack", r"audiomack\.com"),
        ("bandcamp", r"bandcamp\.com"),
        ("boomplay", r"boomplay\.com"),
        ("mixcloud", r"mixcloud\.com"),
        ("anghami", r"anghami\.com"),
        ("wynk", r"wynk\.in"),
        ("hungama", r"hungama\.com"),
        (
            "amazonmusic",
            r"music\.amazon\.(?:com|in|co\.uk|de|fr|es|it|co\.jp|ca|com\.au|com\.br|com\.mx)",
        ),
        ("qobuz", r"qobuz\.com"),
        ("pandora", r"pandora\.com"),
        ("iheart", r"iheart\.com"),
        ("tunein", r"tunein\.com"),
        ("napster", r"napster\.com"),
        ("lastfm", r"last\.fm"),
        ("shazam", r"shazam\.com"),
        ("genius", r"genius\.com"),
        ("reverbnation", r"reverbnation\.com"),
        ("hearthisat", r"hearthis\.at"),
        ("anchor", r"anchor\.fm"),
        ("podcasts_apple", r"podcasts\.apple\.com"),
        ("podcasts_google", r"podcasts\.google\.com"),
        # --- Video & Livestreaming Platforms ---
        ("vimeo", r"vimeo\.com"),
        ("dailymotion", r"(?:dailymotion\.com|dai\.ly)"),
        ("bilibili", r"(?:bilibili\.com|b23\.tv)"),
        ("twitch", r"twitch\.tv"),
        ("kick", r"kick\.com"),
        ("rumble", r"rumble\.com"),
        ("streamable", r"streamable\.com"),
        ("okru", r"ok\.ru"),
        ("coub", r"coub\.com"),
        ("odysee", r"(?:odysee\.com|lbry\.tv)"),
        ("bitchute", r"bitchute\.com"),
        ("ted", r"ted\.com"),
        ("loom", r"loom\.com"),
        ("rutube", r"rutube\.ru"),
        ("archiveorg", r"archive\.org"),
        ("youku", r"youku\.com"),
        ("iqiyi", r"(?:iq\.com|iqiyi\.com)"),
        ("mxplayer", r"mxplayer\.in"),
        ("imdb", r"imdb\.com"),
        # --- Social Media & Short-form Video ---
        ("instagram", r"(?:instagram\.com|instagr\.am)"),
        ("tiktok", r"(?:tiktok\.com|douyin\.com)"),
        ("twitter", r"(?:twitter\.com|(?:^|[\/\.])x\.com)"),
        ("facebook", r"(?:facebook\.com|fb\.watch)"),
        ("pinterest", r"(?:pinterest\.com|pin\.it)"),
        ("reddit", r"reddit\.com"),
        ("snapchat", r"(?:snapchat\.com|story\.snapchat\.com)"),
        ("threads", r"threads\.net"),
        ("tumblr", r"tumblr\.com"),
        ("vk", r"vk\.com"),
        ("likee", r"likee\.(?:video|com)"),
        ("triller", r"triller\.co"),
        ("kwai", r"(?:kwai\.com|kwai-video\.com)"),
        ("sharechat", r"sharechat\.com"),
        ("moj", r"mojapp\.in"),
        ("josh", r"myjosh\.in"),
        ("bluesky", r"bsky\.app"),
        ("mastodon", r"(?:mastodon\.[a-z]+|mstdn\.[a-z]+)"),
        ("weibo", r"(?:weibo\.com|weibo\.cn)"),
        ("kuaishou", r"(?:kuaishou\.com|kwai\.com)"),
        ("patreon", r"patreon\.com"),
        ("discord", r"(?:discord\.com|discordapp\.com)"),
        ("line", r"(?:line\.me|linevoom\.line\.me)"),
        ("linkedin", r"linkedin\.com"),
        # --- Cloud Storage & File Hosts ---
        ("terabox", r"(?:terabox|1024tera)"),
        ("google_drive", r"drive\.google\.com"),
        ("dropbox", r"dropbox\.com"),
        ("onedrive", r"(?:onedrive\.live\.com|1drv\.ms)"),
        ("mediafire", r"mediafire\.com"),
        ("mega", r"mega\.(?:nz|io)"),
        ("yandex_disk", r"disk\.yandex\.(?:ru|com)"),
        ("catbox", r"(?:catbox\.moe|files\.catbox\.moe)"),
        # --- Asian Regional Music Services ---
        ("qqmusic", r"(?:y\.qq\.com|qq\.com)"),
        ("netease", r"music\.163\.com"),
        ("kugou", r"kugou\.com"),
        ("kuwo", r"kuwo\.cn"),
        ("zingmp3", r"zingmp3\.vn"),
        ("nhaccuatui", r"nhaccuatui\.com"),
        ("joox", r"joox\.com"),
    ]

    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        self.api_key = (
            api_key
            if api_key is not None
            else (
                os.environ.get("API_KEY")
                or os.environ.get("ALONE_API_KEY")
                or os.environ.get("RITESH_API_KEY")
                or API_KEY
            )
        )
        raw_url = (
            api_url
            or os.environ.get("API_URL")
            or os.environ.get("ALONE_API_URL")
            or os.environ.get("RITESH_API_URL")
            or API_URL
            or DEFAULT_API_URL
        )
        self.api_url = raw_url.rstrip("/")

        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "KartikMusic/cookies"
        self.warned = False
        self._recent_prefetches = {}  # vidid -> timestamp
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )
        self._client = None

    async def get_client(self):
        if self._client is None or self._client.closed:
            self._client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=600.0, connect=10.0)
            )
        return self._client

    def _get_params(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        if extra:
            params.update({k: v for k, v in extra.items() if v is not None})
        return params

    def detect_platform(self, url_or_query: str) -> str:
        """
        Auto-detect the platform of a given URL or query.
        Returns the platform identifier string (e.g. 'spotify', 'youtube', 'jiosaavn').
        """
        s = str(url_or_query).strip()
        if not s:
            return "generic"

        if s.startswith("spot_"):
            return "spotify"

        if re.match(r"^[a-zA-Z0-9_-]{11}$", s):
            return "youtube"

        for platform, pattern in self.PLATFORM_PATTERNS:
            if re.search(pattern, s, re.IGNORECASE):
                return platform

        if "http://" in s or "https://" in s:
            return "generic"

        return "youtube"

    def get_cookies(self):
        if not self.checked:
            for file in os.listdir(self.cookie_dir):
                if file.endswith(".txt"):
                    self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        async with aiohttp.ClientSession() as session:
            for url in urls:
                name = url.split("/")[-1]
                link = "https://batbin.me/raw/" + name
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                        fw.write(await resp.read())
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        s = url.strip()
        if not s:
            return False

        if bool(re.match(self.regex, s)):
            return True

        if s.startswith("spot_") or re.match(r"^[a-zA-Z0-9_-]{11}$", s):
            return True

        for _, pattern in self.PLATFORM_PATTERNS:
            if re.search(pattern, s, re.IGNORECASE):
                return True

        return bool(re.match(r"^https?://[^\s]+", s))

    def invalid(self, url: str) -> bool:
        if not url:
            return False
        # If it matches any recognized platform, it is NOT invalid
        for _, pattern in self.PLATFORM_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        return bool(re.match(self.iregex, url))

    def _clean_link(self, link: str):
        if not link:
            return ""
        link = str(link)
        if "&" in link and "youtube" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        return link

    def get_stream_url(
        self, query_or_id: str, dl_type: str = "audio", quality: int = 720
    ) -> str:
        """
        Construct a direct stream / download URL with API key for music bots.
        """
        safe_query = urllib.parse.quote(str(query_or_id).strip())
        extension = "mp3" if dl_type == "audio" else "mp4"

        if self.api_key:
            return f"{self.api_url}/downloads/{self.api_key}/{safe_query}.{extension}"

        return f"{self.api_url}/download?query={safe_query}&dl_type={dl_type}&quality={quality}"

    async def download_track(
        self, link: str, chat_id: int | None = None, *args, **kwargs
    ) -> str | None:
        """Voicechat bot helper: construct direct stream URL for a given track link."""
        return self.get_stream_url(link, dl_type="audio")

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        client = await self.get_client()
        platform = self.detect_platform(query)
        is_url = bool(re.match(r"^https?://", query.strip()))

        # If it's a non-YouTube platform URL, resolve details first
        if is_url and platform != "youtube":
            try:
                # 1. Try /details endpoint
                params = self._get_params({"link": query})
                async with client.get(f"{self.api_url}/details", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and data.get("title"):
                            vidid = data.get("id") or data.get("vidid")
                            # Check if download_url contains a valid 11-char YouTube ID
                            dl_url = data.get("download_url") or ""
                            dl_match = re.search(
                                r"/([A-Za-z0-9_-]{11})(?:$|\?|\.|\/)", dl_url
                            )
                            if dl_match:
                                vidid = dl_match.group(1)

                            title = data.get("title", "Track")
                            duration = str(data.get("duration", "00:00"))
                            thumb = data.get("thumb") or data.get("thumbnail", "")

                            # If vidid is not a standard 11-char YouTube ID, resolve to YouTube
                            if not vidid or not re.match(r"^[A-Za-z0-9_-]{11}$", vidid):
                                yt_match = await self.search(
                                    f"{title} {data.get('artist', '')}".strip(),
                                    m_id,
                                    video=video,
                                )
                                if yt_match:
                                    yt_match.title = title[:25]
                                    if thumb:
                                        yt_match.thumbnail = thumb
                                    return yt_match

                            ytlink = f"https://www.youtube.com/watch?v={vidid}"
                            return Track(
                                id=vidid,
                                channel_name=data.get("artist")
                                or platform.capitalize(),
                                duration=duration,
                                duration_sec=utils.to_seconds(duration),
                                message_id=m_id,
                                title=title[:25],
                                thumbnail=thumb
                                or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg",
                                url=ytlink,
                                view_count="",
                                video=video,
                            )
            except Exception as e:
                logger.error(f"Error fetching details for {query}: {e}")

            # 2. Try /api/get endpoint
            try:
                params = self._get_params({"url": query})
                async with client.get(f"{self.api_url}/api/get", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and data.get("title"):
                            dl_url = data.get("download_url") or ""
                            dl_match = re.search(
                                r"/([A-Za-z0-9_-]{11})(?:$|\?|\.|\/)", dl_url
                            )
                            vidid = (
                                dl_match.group(1)
                                if dl_match
                                else (
                                    data.get("id")
                                    if data.get("platform") == "youtube"
                                    else None
                                )
                            )

                            title = data.get("title", "Track")
                            duration = str(data.get("duration", "00:00"))
                            thumb = data.get("thumbnail") or data.get("thumb", "")

                            if not vidid or not re.match(r"^[A-Za-z0-9_-]{11}$", vidid):
                                yt_match = await self.search(title, m_id, video=video)
                                if yt_match:
                                    yt_match.title = title[:25]
                                    if thumb:
                                        yt_match.thumbnail = thumb
                                    return yt_match

                            ytlink = f"https://www.youtube.com/watch?v={vidid}"
                            return Track(
                                id=vidid,
                                channel_name=platform.capitalize(),
                                duration=duration,
                                duration_sec=utils.to_seconds(duration),
                                message_id=m_id,
                                title=title[:25],
                                thumbnail=thumb
                                or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg",
                                url=ytlink,
                                view_count="",
                                video=video,
                            )
            except Exception as e:
                logger.error(f"Error extracting metadata for {query}: {e}")

        # Regular search via API
        params = self._get_params({"query": query, "limit": 1})
        try:
            async with client.get(f"{self.api_url}/search", params=params) as response:
                if response.status == 200:
                    result_data = await response.json()
                    result = result_data.get("result")
                    if result:
                        data = result[0]
                        return Track(
                            id=data.get("id"),
                            channel_name=data.get("channel", {}).get("name"),
                            duration=data.get("duration"),
                            duration_sec=utils.to_seconds(data.get("duration")),
                            message_id=m_id,
                            title=data.get("title")[:25],
                            thumbnail=data.get("thumbnails", [{}])[-1]
                            .get("url")
                            .split("?")[0],
                            url=data.get("link"),
                            view_count=data.get("viewCount", {}).get("short"),
                            video=video,
                        )
        except Exception as e:
            logger.error(f"Error in search from API: {e}")

        # Fallback to py_yt VideosSearch
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
            if results and results["result"]:
                data = results["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                    url=data.get("link"),
                    view_count=data.get("viewCount", {}).get("short"),
                    video=video,
                )
        except Exception:
            pass

        # Local yt-dlp search fallback
        try:
            res_local = await asyncio.to_thread(_safe_search_ytdlp, query)
            if res_local and res_local.get("result"):
                data = res_local["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name="YouTube",
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                    url=data.get("link"),
                    view_count="",
                    video=video,
                )
        except Exception:
            pass

        return None

    async def playlist(
        self, limit: int, user: str, url: str, video: bool
    ) -> list[Track | None]:
        url = self._clean_link(url)
        client = await self.get_client()
        params = self._get_params({"link": url, "limit": limit})
        try:
            async with client.get(
                f"{self.api_url}/playlist", params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = (
                        data.get("videos") or data.get("tracks") or data.get("result")
                    )
                    if videos:
                        tracks = []
                        for item in videos:
                            if isinstance(item, str):
                                track_obj = await self.search(item, 0, video=video)
                                if track_obj:
                                    track_obj.user = user
                                    tracks.append(track_obj)
                            elif isinstance(item, dict):
                                vid_id = item.get("id")
                                title = item.get("title") or item.get("name") or "Track"
                                duration = item.get("duration", "00:00")
                                thumb = (
                                    item.get("thumbnails", [{}])[-1].get("url")
                                    if item.get("thumbnails")
                                    else item.get("thumb", "")
                                )
                                track = Track(
                                    id=vid_id or title,
                                    channel_name=item.get("channel", {}).get("name", "")
                                    if isinstance(item.get("channel"), dict)
                                    else item.get("artist", ""),
                                    duration=duration,
                                    duration_sec=utils.to_seconds(duration),
                                    title=title[:25],
                                    thumbnail=thumb.split("?")[0] if thumb else "",
                                    url=item.get("link", "").split("&list=")[0]
                                    if item.get("link")
                                    else f"https://www.youtube.com/watch?v={vid_id}"
                                    if vid_id
                                    else url,
                                    user=user,
                                    view_count="",
                                    video=video,
                                )
                                tracks.append(track)
                        return tracks
        except Exception as e:
            logger.error(f"Error fetching playlist from API: {e}")

        # Fallback to py_yt Playlist
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def prefetch(self, link: str, video: bool = False):
        """Triggers background pre-fetching on the API"""
        dl_type = "video" if video else "audio"
        link = self._clean_link(link)

        import time

        now = time.time()
        regex = (
            r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)"
            r"([^\"&?\/\s]{11})"
        )
        match = re.search(regex, link)
        vidid = match.group(1) if match else link

        cache_key = f"{vidid}_{dl_type}"
        if cache_key in self._recent_prefetches:
            if now - self._recent_prefetches[cache_key] < 30:
                return True

        self._recent_prefetches[cache_key] = now

        if len(self._recent_prefetches) > 100:
            self._recent_prefetches = {
                k: v for k, v in self._recent_prefetches.items() if now - v < 300
            }

        client = await self.get_client()
        params = self._get_params(
            {"query": link, "dl_type": dl_type, "prefetch": "true"}
        )
        try:
            async with client.get(f"{self.api_url}/download", params=params):
                return True
        except Exception as e:
            logger.error(f"Prefetch failed for {link}: {e}")
        return False

    async def get_related(
        self, video_id: str, video: bool = False, max_duration: int = 0
    ) -> Track | None:
        try:
            _results = await Recommendations.getRelated(video_id)
            if not isinstance(_results, dict):
                return None
            results = _results.get("result")
            if results:
                videos = [r for r in results if r.get("type") == "video"]

                if max_duration:
                    videos = [
                        v
                        for v in videos
                        if utils.to_seconds(v.get("duration") or "00:00")
                        <= max_duration
                    ]

                if not videos:
                    return None
                data = random.choice(videos)
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration") or "00:00"),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                    url=data.get("link"),
                    user="Autoplay",
                    video=video,
                )
        except Exception as e:
            logger.error(f"Error fetching related videos: {e}")
        return None

    async def download(
        self,
        video_id: str,
        video: bool = False,
        *args,
        **kwargs,
    ) -> str | None:
        raw_target = str(video_id).strip()
        is_url = bool(re.match(r"^https?://", raw_target))
        # If not a URL and not a valid 11-char YouTube ID, resolve to a YouTube video ID
        actual_id = raw_target
        if not is_url and not re.match(r"^[A-Za-z0-9_-]{11}$", raw_target):
            try:
                resolved_track = await self.search(raw_target, 0, video=video)
                if resolved_track and re.match(
                    r"^[A-Za-z0-9_-]{11}$", resolved_track.id
                ):
                    actual_id = resolved_track.id
            except Exception as e:
                logger.error(f"Error resolving video ID for {raw_target}: {e}")

        url = actual_id if is_url else (self.base + actual_id)
        dl_type = "video" if video else "audio"

        asyncio.create_task(self.prefetch(url, video=video))

        if self.api_key:
            safe_query = urllib.parse.quote(
                url if is_url else f"youtube.com/{actual_id}"
            )
            ext = "mp4" if video else "mp3"
            stream_url = f"{self.api_url}/downloads/{self.api_key}/{safe_query}.{ext}"
        else:
            stream_url = await download_assistant(url, dl_type)

        try:
            client = await self.get_client()
            async with client.get(stream_url, timeout=30) as resp:
                if resp.status in [200, 206]:
                    await resp.content.read(1024)
                else:
                    logger.warning(
                        f"Download stream URL returned status {resp.status} for {video_id}"
                    )
        except Exception as e:
            logger.warning(
                f"Error checking download stream readiness for {video_id}: {e}"
            )

        return stream_url

    async def extract_async(self, url: str) -> dict[str, Any]:
        """Async multi-platform extractor using master /api/get endpoint."""
        client = await self.get_client()
        async with client.get(
            f"{self.api_url}/api/get", params=self._get_params({"url": url})
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def search_async(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Search multi-platform media using /search endpoint."""
        client = await self.get_client()
        async with client.get(
            f"{self.api_url}/search",
            params=self._get_params({"q": query, "limit": limit}),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def details_async(self, link_or_id: str) -> dict[str, Any]:
        """Fetch track metadata details using /details endpoint."""
        client = await self.get_client()
        async with client.get(
            f"{self.api_url}/details", params=self._get_params({"link": link_or_id})
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def close(self):
        if self._client and not self._client.closed:
            await self._client.close()


# Consolidated Aliases and drop-in exports
AllSupport = YouTube
AloneAPI = YouTube
UniversalAPI = YouTube
all_support = YouTube(api_key=API_KEY, api_url=API_URL)

__all__ = [
    "API_KEY",
    "API_URL",
    "DEFAULT_API_KEY",
    "DEFAULT_API_URL",
    "AllSupport",
    "AloneAPI",
    "UniversalAPI",
    "YouTube",
    "all_support",
]
