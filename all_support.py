# Copyright (C) 2026 by Kartike Mishra, < https://github.com/meowkingm >.
# Universal All Platforms Client API SDK for AloneMusic / KartikeAPI.
# Drop-in helper module for Telegram music & media bots (Yukki, Yukon, Aviax, Fallen, etc.)
# All rights reserved.

import asyncio
import json
import os
import re
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List, Tuple, Union

try:
    import httpx
except ImportError:
    httpx = None

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# -------------------------------------------------------------
# Configuration (Aap yaha direct apna API_URL aur API_KEY daal sakte hain)
# -------------------------------------------------------------
API_URL = os.getenv("API_URL") or os.getenv("ALONE_API_URL") or os.getenv("RITESH_API_URL") or "https://api.riteshyt.in"
API_KEY = os.getenv("API_KEY") or os.getenv("ALONE_API_KEY") or os.getenv("RITESH_API_KEY") or ""

DEFAULT_API_URL = API_URL
DEFAULT_API_KEY = API_KEY


def _safe_search_ytdlp(query: str) -> Dict[str, Any]:
    """Local fallback using yt-dlp to search and extract video info."""
    if yt_dlp is None:
        return {"result": []}
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "ios", "android"]
            }
        },
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
                thumb = thumbnails[0]["url"].split("?")[0] if thumbnails else f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
                return {
                    "result": [{
                        "id": vidid,
                        "title": title,
                        "link": f"https://www.youtube.com/watch?v={vidid}",
                        "duration": d_str,
                        "thumbnails": [{"url": thumb}],
                    }]
                }
        except Exception:
            pass
    return {"result": []}


class AllSupport:
    """
    Universal All Platforms Client API SDK.
    Consolidates 80+ supported platforms across global and regional services:
    - Major Music: Spotify, Apple Music, JioSaavn, YouTube, SoundCloud, Deezer,
      Gaana, Resso, Tidal, Audiomack, Bandcamp, Boomplay, Mixcloud, Anghami,
      Wynk, Hungama, Amazon Music, Qobuz, Pandora, iHeartRadio, TuneIn, Napster,
      Last.fm, Shazam, Genius, ReverbNation, HearThis.at, Anchor, Apple Podcasts, Google Podcasts.
    - Video & Streams: YouTube, Vimeo, Dailymotion, Bilibili, Twitch, Kick, Rumble,
      Streamable, OK.ru, Coub, Odysee, Bitchute, Ted, Loom, Rutube, Archive.org,
      Youku, iQiyi.
    - Social & Short Videos: Instagram, TikTok/Douyin, Twitter/X, Facebook, Pinterest,
      Reddit, Snapchat, Threads, Tumblr, VK, Likee, Triller, Kwai, ShareChat, Moj,
      Josh, Bluesky, Mastodon, Weibo, Kuaishou, Patreon, Discord, Line, LinkedIn.
    - Cloud & File Sharing: Terabox, Google Drive, Dropbox, OneDrive, Mediafire, Mega,
      Yandex Disk, Catbox.
    - Asian & Regional Streaming: QQ Music, NetEase Cloud Music, Kugou, Kuwo,
      Zing MP3, NhacCuaTui, Joox.

    Compatible as a drop-in replacement or companion to Spotify.py and Youtube.py
    for Telegram voice chat music bots (YukkiMusic, AnonXMusic, FallenMusic, AviaxMusic).
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
        ("amazonmusic", r"music\.amazon\.(?:com|in|co\.uk|de|fr|es|it|co\.jp|ca|com\.au|com\.br|com\.mx)"),
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

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
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

    def _get_params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

        # Check for Spotify URI/id shorthand
        if s.startswith("spot_"):
            return "spotify"

        # Check 11-char YouTube Video ID
        if re.match(r"^[a-zA-Z0-9_-]{11}$", s):
            return "youtube"

        for platform, pattern in self.PLATFORM_PATTERNS:
            if re.search(pattern, s, re.IGNORECASE):
                return platform

        if "http://" in s or "https://" in s:
            return "generic"

        return "youtube"

    async def valid(self, link: str) -> bool:
        """Check if a URL or query string is valid and supported."""
        if not link or not isinstance(link, str):
            return False
        s = link.strip()
        if not s:
            return False

        # Spotify/Apple/JioSaavn/YouTube or any recognized pattern
        for _, pattern in self.PLATFORM_PATTERNS:
            if re.search(pattern, s, re.IGNORECASE):
                return True

        if s.startswith("spot_") or re.match(r"^[a-zA-Z0-9_-]{11}$", s):
            return True

        # Valid http/https URL
        if re.match(r"^https?://[^\s]+", s):
            return True

        return False

    def get_stream_url(self, query_or_id: str, dl_type: str = "audio", quality: int = 720) -> str:
        """
        Construct a direct stream / download URL with API key for music bots.
        """
        safe_query = urllib.parse.quote(str(query_or_id).strip())
        extension = "mp3" if dl_type == "audio" else "mp4"

        if self.api_key:
            return f"{self.api_url}/downloads/{self.api_key}/{safe_query}.{extension}"

        return f"{self.api_url}/download?query={safe_query}&dl_type={dl_type}&quality={quality}"

    async def download_track(self, link: str, chat_id: Optional[int] = None, *args, **kwargs) -> Optional[str]:
        """
        Voicechat bot helper: construct direct stream URL for a given track link.
        """
        return self.get_stream_url(link, dl_type="audio")

    async def download(
        self,
        link: str,
        mystic=None,
        video: bool = False,
        videoid: Optional[str] = None,
        songaudio: bool = False,
        songvideo: bool = False,
        format_id: Optional[str] = None,
        title: Optional[str] = None,
        instant: Optional[bool] = None,
        *args,
        **kwargs,
    ) -> Tuple[Optional[str], bool]:
        """
        Music bot download method compatible with YukkiMusic/AnonXMusic/FallenMusic.
        Returns a tuple of (stream_link, False).
        """
        target = videoid or link
        dl_type = "video" if (video or songvideo) else "audio"
        stream_link = self.get_stream_url(target, dl_type=dl_type)
        return stream_link, False

    async def _http_get_async(self, endpoint: str, params: Dict[str, Any], timeout: float = 20.0) -> Dict[str, Any]:
        """Internal asynchronous HTTP GET using httpx, aiohttp, or thread-based urllib."""
        url = f"{self.api_url}{endpoint}"
        query_str = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_str}" if query_str else url

        if httpx is not None:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()

        if aiohttp is not None:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(full_url) as resp:
                    resp.raise_for_status()
                    return await resp.json()

        def _blocking_urllib():
            req = urllib.request.Request(full_url, headers={"User-Agent": "AloneAPI-Client/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        return await asyncio.to_thread(_blocking_urllib)

    def _http_get_sync(self, endpoint: str, params: Dict[str, Any], timeout: float = 20.0) -> Dict[str, Any]:
        """Internal synchronous HTTP GET using httpx or standard urllib."""
        url = f"{self.api_url}{endpoint}"
        query_str = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_str}" if query_str else url

        if httpx is not None:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()

        req = urllib.request.Request(full_url, headers={"User-Agent": "AloneAPI-Client/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    async def extract_async(self, url: str) -> Dict[str, Any]:
        """
        Async multi-platform extractor using master /api/get endpoint.
        """
        return await self._http_get_async("/api/get", self._get_params({"url": url}), timeout=20.0)

    def extract(self, url: str) -> Dict[str, Any]:
        """Synchronous multi-platform extractor."""
        return self._http_get_sync("/api/get", self._get_params({"url": url}), timeout=20.0)

    async def search_async(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search multi-platform media using /search endpoint."""
        return await self._http_get_async("/search", self._get_params({"q": query, "limit": limit}), timeout=15.0)

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Synchronous search wrapper."""
        return self._http_get_sync("/search", self._get_params({"q": query, "limit": limit}), timeout=15.0)

    async def details_async(self, link_or_id: str) -> Dict[str, Any]:
        """Fetch track metadata details using /details endpoint."""
        return await self._http_get_async("/details", self._get_params({"link": link_or_id}), timeout=15.0)

    def details(self, link_or_id: str) -> Dict[str, Any]:
        """Synchronous details wrapper."""
        return self._http_get_sync("/details", self._get_params({"link": link_or_id}), timeout=15.0)

    async def track(self, link: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Resolve any platform link or query into standardized track details & Video ID
        for voice chat music bot playback.
        Returns (track_details_dict, vidid).
        """
        platform = self.detect_platform(link)
        title = "Track"
        vidid = None
        duration_min = "00:00"
        thumb = ""
        ytlink = ""
        query_info = link

        # 1. Attempt remote /details or /api/get lookup
        try:
            data = await self.details_async(link)
            if data and data.get("title"):
                title = data.get("title", title)
                vidid = data.get("id") or data.get("vidid")
                duration_min = str(data.get("duration", "00:00"))
                thumb = data.get("thumb") or data.get("thumbnail", "")
                ytlink = data.get("link") or (f"https://www.youtube.com/watch?v={vidid}" if vidid else "")
                query_info = f"{title} {data.get('artist', '')}".strip()
        except Exception:
            # Fallback to /api/get if details route had an issue
            try:
                extract_data = await self.extract_async(link)
                if extract_data and extract_data.get("title"):
                    title = extract_data.get("title", title)
                    duration_min = str(extract_data.get("duration", "00:00"))
                    thumb = extract_data.get("thumbnail") or extract_data.get("thumb", "")
                    query_info = f"{title} {extract_data.get('uploader', '')}".strip()
            except Exception:
                pass

        # 2. If no vidid resolved yet, search YouTube for the best audio stream match
        if not vidid:
            search_query = query_info if query_info != link else link
            try:
                search_res = await self.search_async(search_query, limit=1)
                results = search_res.get("result", [])
                if results and isinstance(results, list):
                    first = results[0]
                    vidid = first.get("id")
                    title = first.get("title", title)
                    duration_min = first.get("duration", duration_min)
                    ytlink = first.get("link", f"https://www.youtube.com/watch?v={vidid}")
                    if first.get("thumbnails"):
                        thumb = first["thumbnails"][0].get("url", thumb)
            except Exception:
                # Local yt-dlp search fallback if remote search fails or is unreachable
                try:
                    res_local = await asyncio.to_thread(_safe_search_ytdlp, search_query)
                    if res_local and res_local.get("result"):
                        first = res_local["result"][0]
                        vidid = first.get("id")
                        title = first.get("title", title)
                        duration_min = first.get("duration", duration_min)
                        ytlink = first.get("link", f"https://www.youtube.com/watch?v={vidid}")
                        if first.get("thumbnails"):
                            thumb = first["thumbnails"][0].get("url", thumb)
                except Exception:
                    pass

        if vidid and not thumb:
            thumb = f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"

        track_details = {
            "title": title,
            "link": ytlink or link,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumb,
            "query_info": query_info,
            "platform": platform,
        }
        return track_details, vidid

    async def playlist(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        """
        Fetch playlist tracks from supported platforms.
        Returns (list_of_track_names, playlist_id).
        """
        playlist_id = url.split("/")[-1].split("?")[0]
        try:
            data = await self._http_get_async("/playlist", self._get_params({"link": url, "limit": limit}), timeout=20.0)
            if data:
                tracks = data.get("tracks") or data.get("result") or []
                if isinstance(tracks, list):
                    track_titles = []
                    for t in tracks:
                        if isinstance(t, str):
                            track_titles.append(t)
                        elif isinstance(t, dict):
                            title = t.get("title") or t.get("name")
                            artist = t.get("artist") or ""
                            if title:
                                track_titles.append(f"{title} {artist}".strip())
                    return track_titles, data.get("id", playlist_id)
        except Exception:
            pass

        return [], playlist_id

    async def album(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        """Alias to playlist() for album URLs."""
        return await self.playlist(url, limit=limit)

    async def artist(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        """Alias to playlist() for artist discography / top tracks."""
        return await self.playlist(url, limit=limit)

    async def mix_async(self, query_or_id: str, limit: int = 15) -> Dict[str, Any]:
        """Fetch autoplay recommendations / artist mix tracks using /api/mix."""
        return await self._http_get_async("/api/mix", self._get_params({"query": query_or_id, "limit": limit}), timeout=15.0)

    def mix(self, query_or_id: str, limit: int = 15) -> Dict[str, Any]:
        """Synchronous mix wrapper."""
        return self._http_get_sync("/api/mix", self._get_params({"query": query_or_id, "limit": limit}), timeout=15.0)

    async def lyrics_async(self, query: str) -> Dict[str, Any]:
        """Fetch synchronized track lyrics using /api/lyrics."""
        return await self._http_get_async("/api/lyrics", self._get_params({"q": query}), timeout=10.0)

    def lyrics(self, query: str) -> Dict[str, Any]:
        """Synchronous lyrics wrapper."""
        return self._http_get_sync("/api/lyrics", self._get_params({"q": query}), timeout=10.0)


# Aliases for maximum drop-in flexibility
UniversalAPI = AllSupport
AloneAPI = AllSupport

# Global singleton instance for immediate use
all_support = AllSupport(api_key=API_KEY, api_url=API_URL)
