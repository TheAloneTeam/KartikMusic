# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, anon, app, db, lang
from anony.helpers import buttons, can_manage_vc


@Bot.on_message(filters.command(["pause"]) & filters.group & ~filters.bl_users)
@lang.language()
@can_manage_vc
async def _pause(client, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    if not await db.playing(m.chat.id):
        return await m.reply_text(m.lang["play_already_paused"])

    await anon.pause(m.chat.id, client_bot=client)
    await m.reply_text(
        text=m.lang["play_paused"].format(m.from_user.mention),
        reply_markup=buttons.controls(m.chat.id),
    )
