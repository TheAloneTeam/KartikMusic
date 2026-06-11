# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from anony import config
from anony.helpers import Media, Track


class Thumbnail:
    def __init__(self):
        try:
            self.font_title = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 55)
            self.font_artist = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 35)
            self.font_time = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 25)
            self.font_4k = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 80)
            self.font_overlay_artist = ImageFont.truetype(
                "anony/helpers/Raleway-Bold.ttf", 60
            )
            self.font_overlay_song = ImageFont.truetype(
                "anony/helpers/Inter-Light.ttf", 30
            )
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_time = ImageFont.load_default()
            self.font_4k = ImageFont.load_default()
            self.font_overlay_artist = ImageFont.load_default()
            self.font_overlay_song = ImageFont.load_default()

    def _make_sq(self, im, radius=60):
        """Creates a rounded square image."""
        mask = Image.new("L", im.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.paste(im, (0, 0), mask)
        return out

    def _draw_player(self, thumb_path, videoid, title, duration, artist):
        # 1. Background
        if thumb_path and os.path.exists(thumb_path):
            background = Image.open(thumb_path)
        else:
            background = Image.new("RGB", (1280, 720), (20, 20, 20))

        background = background.resize((1280, 720))
        background = background.filter(ImageFilter.GaussianBlur(radius=50))

        # Darken background
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.4)

        draw = ImageDraw.Draw(background)

        # 2. Thumbnail image (Left)
        if thumb_path and os.path.exists(thumb_path):
            thumb = Image.open(thumb_path).convert("RGBA")
        else:
            thumb = Image.new("RGBA", (520, 520), (40, 40, 40, 255))

        thumb = thumb.resize((520, 520))

        # Add overlay on thumb
        overlay = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        # Blueish translucent overlay on the left
        overlay_draw.rectangle([0, 0, 220, 520], fill=(0, 70, 140, 210))

        # Artist name on overlay
        artist_upper = str(artist).upper()
        y_off = 60
        words = artist_upper.split()
        for word in words[:3]:
            if len(word) > 8:
                word = word[:8]
            overlay_draw.text(
                (30, y_off), word, font=self.font_overlay_artist, fill="white"
            )
            y_off += 70

        # Song title (small) on overlay
        title_upper = str(title).upper()
        title_lines = []
        words = title_upper.split()
        line = ""
        for word in words:
            if len(line + " " + word) < 15:
                line += " " + word
            else:
                title_lines.append(line.strip())
                line = word
        title_lines.append(line.strip())

        y_off += 10
        for line in title_lines[:2]:
            overlay_draw.text(
                (30, y_off), line, font=self.font_overlay_song, fill=(220, 220, 220)
            )
            y_off += 40

        # 4K text at the bottom
        overlay_draw.text((30, 390), "4K", font=self.font_4k, fill="white")

        thumb.alpha_composite(overlay)
        thumb = self._make_sq(thumb, radius=60)
        background.paste(thumb, (70, 100), thumb)

        # 4. Text (Title & Artist)
        title = str(title)
        artist = str(artist)
        max_title_width = 450
        if draw.textbbox((0, 0), title, font=self.font_title)[2] > max_title_width:
            while (
                draw.textbbox((0, 0), title + "...", font=self.font_title)[2]
                > max_title_width
            ):
                title = title[:-1]
            title += "..."

        draw.text((630, 220), title, font=self.font_title, fill="white")
        draw.text((630, 290), artist, font=self.font_artist, fill=(200, 200, 200))

        # Star icon
        star_pts = [
            (1130, 268),
            (1135, 280),
            (1148, 280),
            (1138, 288),
            (1142, 301),
            (1130, 293),
            (1118, 301),
            (1122, 288),
            (1112, 280),
            (1125, 280),
        ]
        draw.polygon(star_pts, fill="white")

        # Three dots (vertical)
        draw.ellipse([1180, 265, 1186, 271], fill="white")
        draw.ellipse([1180, 280, 1186, 286], fill="white")
        draw.ellipse([1180, 295, 1186, 301], fill="white")

        # 5. Progress Bar
        bar_x_start = 630
        bar_x_end = 1230
        bar_y = 420
        progress = 0.35

        draw.line([bar_x_start, bar_y, bar_x_end, bar_y], fill=(100, 100, 100), width=6)
        current_x = bar_x_start + (bar_x_end - bar_x_start) * progress
        draw.line([bar_x_start, bar_y, current_x, bar_y], fill="white", width=6)
        draw.ellipse([current_x - 6, bar_y - 6, current_x + 6, bar_y + 6], fill="white")

        # 6. Time Labels
        draw.text((630, 440), "0:35", font=self.font_time, fill=(200, 200, 200))
        draw.text((1180, 440), str(duration), font=self.font_time, fill=(200, 200, 200))

        # 7. Controls
        # Centered at 930
        y_ctrl = 520
        # Skip Back
        draw.polygon(
            [(790, y_ctrl + 30), (840, y_ctrl), (840, y_ctrl + 60)], fill="white"
        )
        draw.polygon(
            [(740, y_ctrl + 30), (790, y_ctrl), (790, y_ctrl + 60)], fill="white"
        )
        # Play/Pause
        draw.rectangle([900, y_ctrl, 920, y_ctrl + 60], fill="white")
        draw.rectangle([940, y_ctrl, 960, y_ctrl + 60], fill="white")
        # Skip Forward
        draw.polygon(
            [(1020, y_ctrl), (1070, y_ctrl + 30), (1020, y_ctrl + 60)], fill="white"
        )
        draw.polygon(
            [(1070, y_ctrl), (1120, y_ctrl + 30), (1070, y_ctrl + 60)], fill="white"
        )

        # 8. Volume Bar
        # Centered at 930
        y_vol = 675
        draw.polygon(
            [
                (735, y_vol),
                (755, y_vol),
                (770, y_vol - 15),
                (770, y_vol + 15),
                (755, y_vol),
            ],
            fill="white",
        )
        draw.polygon(
            [
                (1105, y_vol),
                (1125, y_vol),
                (1140, y_vol - 15),
                (1140, y_vol + 15),
                (1125, y_vol),
            ],
            fill="white",
        )
        draw.arc(
            [1145, y_vol - 15, 1170, y_vol + 15],
            start=-60,
            end=60,
            fill="white",
            width=3,
        )
        draw.arc(
            [1140, y_vol - 25, 1180, y_vol + 25],
            start=-60,
            end=60,
            fill="white",
            width=3,
        )
        draw.line([785, y_vol, 1090, y_vol], fill=(150, 150, 150), width=6)
        draw.line([785, y_vol, 1010, y_vol], fill="white", width=6)
        draw.ellipse([1004, y_vol - 6, 1016, y_vol + 6], fill="white")

        # 9. Bottom Left Icons
        y_icons = 665
        draw.rounded_rectangle(
            [630, y_icons, 660, y_icons + 20], radius=5, outline="white", width=2
        )
        draw.polygon(
            [(638, y_icons + 20), (645, y_icons + 20), (638, y_icons + 28)],
            fill="white",
        )
        draw.line([685, y_icons + 3, 705, y_icons + 3], fill="white", width=2)
        draw.line([685, y_icons + 11, 705, y_icons + 11], fill="white", width=2)
        draw.line([685, y_icons + 19, 705, y_icons + 19], fill="white", width=2)
        draw.rectangle([678, y_icons + 2, 680, y_icons + 4], fill="white")
        draw.rectangle([678, y_icons + 10, 680, y_icons + 12], fill="white")
        draw.rectangle([678, y_icons + 18, 680, y_icons + 20], fill="white")

        final_thumb = background.convert("RGB")
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
            artist = (
                getattr(media, "channel_name", "Unknown Artist") or "Unknown Artist"
            )
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
