# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
from pyrogram import filters, types

from anony import anon, app, db, lang, queue
from anony.helpers import can_manage_vc


@app.on_message(
    filters.command(["bass", "echo", "slowed", "nightcore", "normal"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@can_manage_vc
async def audio_effects(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    media = queue.get_current(m.chat.id)
    if not media:
        return await m.reply_text(m.lang["not_playing"])

    command = m.command[0].lower()
    if command == "bass":
        media.filter = "bass=g=15"
    elif command == "echo":
        media.filter = "aecho=0.8:0.88:60:0.4"
    elif command == "slowed":
        media.filter = "asetrate=48000*0.8,aresample=48000,aecho=0.8:0.88:60:0.4"
    elif command == "nightcore":
        media.filter = "asetrate=48000*1.25,aresample=48000"
    elif command == "normal":
        media.filter = None

    sent = await m.reply_text(m.lang["applying_effect"].format(command))

    current_time = media.time
    if media.played_at:
        current_time += int(time.time() - media.played_at)

    await anon.play_media(m.chat.id, sent, media, current_time)

    await sent.edit_text(
        m.lang["effect_applied"].format(command, m.from_user.mention)
    )
