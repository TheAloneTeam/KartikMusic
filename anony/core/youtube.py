# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import re
import random
import asyncio
import aiohttp
import httpx
import urllib.parse
from pathlib import Path
from typing import Union

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils

# Use environment variables for configuration
API_URL = os.getenv("API_URL", "https://api.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "ritesh_free_3349aed8ab6e1bcd3e51999c")


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
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
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
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        return self._client

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
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    def _clean_link(self, link: str):
        if not link:
            return ""
        link = str(link)
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        return link

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        client = await self.get_client()
        params = {"query": query, "limit": 1}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/search", params=params)
            if response.status_code == 200:
                result_data = response.json()
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
                        thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                        url=data.get("link"),
                        view_count=data.get("viewCount", {}).get("short"),
                        video=video,
                    )
        except Exception as e:
            logger.error(f"Error in search from API: {e}")

        # Fallback to existing search if API fails
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
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        url = self._clean_link(url)
        client = await self.get_client()
        params = {"link": url, "limit": limit}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/playlist", params=params)
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos")
                if videos:
                    tracks = []
                    for data in videos:
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
                    return tracks
        except Exception as e:
            logger.error(f"Error fetching playlist from API: {e}")

        # Fallback
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

        # Avoid redundant prefetches within 30 seconds
        import time

        now = time.time()
        regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
        match = re.search(regex, link)
        vidid = match.group(1) if match else link

        cache_key = f"{vidid}_{dl_type}"
        if cache_key in self._recent_prefetches:
            if now - self._recent_prefetches[cache_key] < 30:
                return True

        self._recent_prefetches[cache_key] = now

        # Cleanup old prefetches (keep cache small)
        if len(self._recent_prefetches) > 100:
            self._recent_prefetches = {
                k: v for k, v in self._recent_prefetches.items() if now - v < 300
            }

        client = await self.get_client()
        params = {"query": link, "dl_type": dl_type, "prefetch": "true"}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            # Fire and forget request to the API
            await client.get(f"{API_URL}/download", params=params)
            return True
        except Exception as e:
            logger.error(f"Prefetch failed for {link}: {e}")
        return False

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        dl_type = "video" if video else "audio"

        # Immediate prefetch
        asyncio.create_task(self.prefetch(url, video=video))

        if API_KEY:
            # Using the optimized stream URL from the API
            stream_url = f"{API_URL}/downloads/{API_KEY}/youtube.com/{video_id}.{'mp4' if video else 'mp3'}"
            return stream_url

        # If no API_KEY or custom logic fails, use download_assistant or fallback
        return await download_assistant(url, dl_type)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
