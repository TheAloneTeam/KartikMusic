# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, lang, yt
from anony.helpers import buttons


@app.on_message(filters.command(["song"]) & ~app.bl_users)
@lang.language()
async def song_hndlr(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(m.lang["play_usage"])

    query = m.text.split(None, 1)[1]
    sent = await m.reply_text(m.lang["play_searching"])

    track = await yt.search(query, sent.id)
    if not track:
        return await sent.edit_text(m.lang["play_not_found"].format("support chat"))

    await sent.delete()
    await m.reply_photo(
        photo=track.thumbnail,
        caption=f"<b>Title:</b> {track.title}\n<b>Channel:</b> {track.channel_name}\n<b>Duration:</b> {track.duration}",
        reply_markup=buttons.song_markup(track.id),
    )
