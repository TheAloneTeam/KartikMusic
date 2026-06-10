# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, anon, app, db, lang
from anony.helpers import can_manage_vc


@Bot.on_message(filters.command(["end", "stop"]) & filters.group & ~filters.bl_users)
@lang.language()
@can_manage_vc
async def _stop(client, m: types.Message):
    if len(m.command) > 1:
        return

    call = await db.get_call(m.chat.id)
    await anon.stop(m.chat.id, client_bot=client)
    if not call:
        return await m.reply_text(m.lang["not_playing"])

    await m.reply_text(m.lang["play_stopped"].format(m.from_user.mention))
