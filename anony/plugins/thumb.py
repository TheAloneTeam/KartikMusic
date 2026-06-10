# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, app, db, lang
from anony.helpers import admin_check


@Bot.on_message(filters.command(["thumb", "thumbnail"]) & filters.group & ~filters.bl_users)
@lang.language()
@admin_check
async def _thumb_hndlr(client, m: types.Message):
    status = await db.get_thumb_mode(m.chat.id)
    if status:
        await db.set_thumb_mode(m.chat.id, False)
        return await m.reply_text(m.lang["thumb_off"])

    await db.set_thumb_mode(m.chat.id, True)
    await m.reply_text(m.lang["thumb_on"])
