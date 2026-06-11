# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import asyncio
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont)

from anony import config
from anony.helpers import Media, Track


class Thumbnail:
    def __init__(self):
        try:
            self.font_title = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 40)
            self.font_artist = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 30)
            self.font_time = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 22)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_time = ImageFont.load_default()

    def _make_sq(self, im, radius=80):
        """Creates a rounded square image."""
        mask = Image.new('L', im.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
        out = Image.new('RGBA', im.size, (0, 0, 0, 0))
        out.paste(im, (0, 0), mask)
        return out

    def _draw_player(self, thumb_path, videoid, title, duration, artist):
        # 1. Background
        if thumb_path and os.path.exists(thumb_path):
            background = Image.open(thumb_path)
        else:
            background = Image.new("RGB", (1280, 720), (20, 20, 20))

        background = background.resize((1280, 720))
        background = background.filter(ImageFilter.GaussianBlur(radius=60))

        # Darken background
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.35)

        # Use RGBA for all drawing
        canvas = background.convert("RGBA")
        draw = ImageDraw.Draw(canvas)

        # 2. Thumbnail image (Left)
        if thumb_path and os.path.exists(thumb_path):
            thumb = Image.open(thumb_path).convert("RGBA")
        else:
            thumb = Image.new("RGBA", (520, 520), (40, 40, 40, 255))

        thumb = thumb.resize((520, 520))
        thumb = self._make_sq(thumb, radius=80)
        canvas.paste(thumb, (90, 100), thumb)

        # 3. Text (Title & Artist)
        x_start = 720
        x_end = 1210

        title = str(title)
        draw.text((x_start, 160), title[:22] + ("..." if len(title) > 22 else ""), font=self.font_title, fill="white")

        artist = str(artist)
        draw.text((x_start, 215), artist[:25] + ("..." if len(artist) > 25 else ""), font=self.font_artist, fill=(180, 180, 180))

        # Star and Dots icons (White circles)
        draw.ellipse([1100, 160, 1150, 210], fill="white")
        # Simple star shape (inverted color for visibility)
        star_pts = [(1125, 172), (1128, 182), (1138, 182), (1130, 189), (1134, 199), (1125, 193), (1116, 199), (1120, 189), (1112, 182), (1122, 182)]
        draw.polygon(star_pts, fill=(50, 50, 50))

        draw.ellipse([1170, 160, 1220, 210], fill="white")
        for y in [175, 185, 195]:
            draw.ellipse([1192, y, 1198, y+6], fill=(50, 50, 50))

        # 4. Progress Bar
        bar_y = 310
        draw.line([x_start, bar_y, x_end, bar_y], fill=(255, 255, 255, 40), width=10)
        # Dummy 15% progress
        draw.line([x_start, bar_y, x_start + 70, bar_y], fill=(220, 220, 220), width=10)
        draw.ellipse([x_start + 60, bar_y - 10, x_start + 80, bar_y + 10], fill=(220, 220, 220))

        # Time Labels
        draw.text((x_start, 345), "0:03", font=self.font_time, fill=(180, 180, 180))
        draw.text((x_end - 65, 345), f"-{duration}", font=self.font_time, fill=(180, 180, 180))

        # 5. Playback Controls
        y_ctrl = 500
        # Skip Back <<
        draw.polygon([(820, y_ctrl), (770, y_ctrl - 25), (820, y_ctrl - 50)], fill="white")
        draw.polygon([(770, y_ctrl), (720, y_ctrl - 25), (770, y_ctrl - 50)], fill="white")
        # Pause ||
        draw.rectangle([930, y_ctrl - 65, 948, y_ctrl + 5], fill="white")
        draw.rectangle([962, y_ctrl - 65, 980, y_ctrl + 5], fill="white")
        # Skip Forward >>
        draw.polygon([(1100, y_ctrl), (1150, y_ctrl - 25), (1100, y_ctrl - 50)], fill="white")
        draw.polygon([(1150, y_ctrl), (1200, y_ctrl - 25), (1150, y_ctrl - 50)], fill="white")

        # 6. Volume Bar
        y_vol = 610
        draw.line([x_start + 30, y_vol, x_end - 30, y_vol], fill=(255, 255, 255, 40), width=8)
        # Dummy 80% volume
        vol_x = x_start + 30 + (x_end - x_start - 60) * 0.8
        draw.line([x_start + 30, y_vol, vol_x, y_vol], fill="white", width=8)
        draw.ellipse([vol_x - 8, y_vol - 8, vol_x + 8, y_vol + 8], fill="white")

        # Left Volume Icon |<
        draw.rectangle([x_start + 5, y_vol - 8, x_start + 8, y_vol + 8], fill="white")
        draw.polygon([(x_start + 10, y_vol), (x_start + 22, y_vol - 8), (x_start + 22, y_vol + 8)], fill="white")
        # Right Volume Icon >))
        draw.polygon([(x_end - 22, y_vol - 8), (x_end - 10, y_vol), (x_end - 22, y_vol + 8)], fill="white")
        draw.arc([x_end - 10, y_vol - 10, x_end + 5, y_vol + 10], start=-60, end=60, fill="white", width=2)
        draw.arc([x_end - 15, y_vol - 18, x_end + 12, y_vol + 18], start=-60, end=60, fill="white", width=2)

        # 7. Bottom Icons
        y_bot = 670
        # Quote bubble "99"
        draw.rounded_rectangle([800, y_bot, 835, y_bot + 25], radius=5, outline="white", width=2)
        try: qf = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 20)
        except: qf = ImageFont.load_default()
        draw.text((809, y_bot - 1), "99", font=qf, fill="white")

        # List Icon
        for i in range(3):
            draw.line([1110, y_bot + 5 + i*8, 1140, y_bot + 5 + i*8], fill="white", width=3)
            draw.ellipse([1100, y_bot + 3 + i*8, 1104, y_bot + 7 + i*8], fill="white")

        final_thumb = canvas.convert("RGB")
        out_path = f"cache/{videoid}.png"
        final_thumb.save(out_path)
        return out_path

    async def generate(self, media: Media | Track) -> str:
        try:
            videoid = media.id
            output = f"cache/{videoid}.png"
            if os.path.exists(output):
                return output

            title = media.title
            duration = media.duration
            artist = getattr(media, "channel_name", "Unknown Artist") or "Unknown Artist"
            thumbnail_url = getattr(media, "thumbnail", None)

            thumb_path = f"cache/thumb_{videoid}.png"

            if not os.path.exists(thumb_path) and thumbnail_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail_url) as resp:
                        if resp.status == 200:
                            with open(thumb_path, "wb") as f:
                                f.write(await resp.read())

            if not os.path.exists(thumb_path):
                thumb_path = None

            return await asyncio.to_thread(
                self._draw_player, thumb_path, videoid, title, duration, artist
            )
        except Exception:
            return config.DEFAULT_THUMB
