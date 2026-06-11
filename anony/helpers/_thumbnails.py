# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import asyncio
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from anony import config
from anony.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        try:
            self.font1 = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 30)
            self.font2 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 30)
        except Exception:
            self.font1 = ImageFont.load_default()
            self.font2 = ImageFont.load_default()
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f:
                f.write(await resp.read())
        return output_path

    def _draw_image(self, temp, output, song: Track, size=(1280, 720)):
        thumb = Image.open(temp).convert("RGBA").resize(
            size, Image.Resampling.LANCZOS,
        )
        blur = thumb.filter(ImageFilter.GaussianBlur(25))
        image = ImageEnhance.Brightness(blur).enhance(.40)

        _rect = ImageOps.fit(
            thumb, self.rect,
            method=Image.LANCZOS, centering=(0.5, 0.5),
        )
        mask = Image.new("L", self.rect, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, self.rect[0], self.rect[1]),
            radius=15,
            fill=255,
        )
        _rect.putalpha(mask)
        image.paste(_rect, (183, 30), _rect)

        draw = ImageDraw.Draw(image)
        draw.text(
            xy=(50, 560),
            text=f"{(song.channel_name or 'Unknown')[:25]} | {song.view_count or 0}",
            font=self.font2, fill=self.fill,
        )
        draw.text((50, 600), (song.title or "Unknown")[:50], font=self.font1, fill=self.fill)
        draw.text((40, 650), "0:01", font=self.font1)
        draw.line([(140, 670), (1160, 670)], fill=self.fill, width=5, joint="curve")
        draw.text((1185, 650), song.duration or "00:00", font=self.font1, fill=self.fill)

        image.save(output)
        return output

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            await asyncio.to_thread(self._draw_image, temp, output, song, size)

            try:
                os.remove(temp)
            except Exception:
                pass
            return output
        except Exception:
            return config.DEFAULT_THUMB
