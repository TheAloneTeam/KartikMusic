# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, app, db, lang
from anony.helpers import can_manage_vc


@Bot.on_message(filters.command(["autoplay"]) & filters.group & ~filters.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(client, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    status = await db.get_autoplay(m.chat.id)
    if status:
        await db.set_autoplay(m.chat.id, False)
        await m.reply_text(m.lang["autoplay_off"].format(m.from_user.mention))
    else:
        await db.set_autoplay(m.chat.id, True)
        await m.reply_text(m.lang["autoplay_on"].format(m.from_user.mention))
