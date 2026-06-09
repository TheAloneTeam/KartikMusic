# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import admin_check


@app.on_message(filters.command(["thumb", "thumbnail"]) & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def _thumb_hndlr(_, m: types.Message):
    status = await db.get_thumb_mode(m.chat.id)
    if status:
        await db.set_thumb_mode(m.chat.id, False)
        return await m.reply_text(m.lang["thumb_off"])

    await db.set_thumb_mode(m.chat.id, True)
    await m.reply_text(m.lang["thumb_on"])
