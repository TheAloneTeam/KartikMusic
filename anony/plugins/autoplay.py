# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import can_manage_vc


@app.on_message(filters.command(["autoplay"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(f"<b>Usage:</b>\n\n/{m.command[0]} [enable|disable]")

    arg = m.command[1].lower()
    if arg in ["enable", "on"]:
        await db.set_autoplay(m.chat.id, True)
        return await m.reply_text(m.lang["autoplay_on"].format(m.from_user.mention))
    elif arg in ["disable", "off"]:
        await db.set_autoplay(m.chat.id, False)
        return await m.reply_text(m.lang["autoplay_off"].format(m.from_user.mention))

    return await m.reply_text(f"<b>Usage:</b>\n\n/{m.command[0]} [enable|disable]")
