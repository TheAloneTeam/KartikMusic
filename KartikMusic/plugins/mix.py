#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from pathlib import Path

from pyrogram import filters, types

from KartikMusic import Kartik, app, config, db, lang, queue, yt
from KartikMusic.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


@app.on_message(filters.command(["mix"]) & filters.group & ~app.bl_users)
@lang.language()
@checkUB
async def mix_hndlr(_, m: types.Message) -> None:
    chat_id = m.chat.id
    target = None

    if len(m.command) > 1:
        target = m.text.split(None, 1)[1].strip()
    elif m.reply_to_message and m.reply_to_message.text:
        target = m.reply_to_message.text.strip()
    else:
        current = queue.get_current(chat_id)
        if current:
            target = current.id or getattr(current, "url", None)

    if not target:
        return await m.reply_text(
            "<b>Usage:</b>\n/mix [song or URL]\n\n"
            "Or run /mix while a song is playing to queue recommended songs based on it."
        )

    sent = await m.reply_text("🔍 Fetching recommended mix tracks...")
    limit = int(getattr(config, "AUTO_PLAY_LIMIT", 10))
    tracks = await yt.get_recommendations(target, limit=limit)
    if not tracks:
        return await sent.edit_text(
            "❌ No mix tracks found. Try with another song or URL."
        )

    mention = m.from_user.mention
    for t in tracks:
        t.user = mention

    is_calling = await db.get_call(chat_id)
    first_track = None

    if not is_calling and not queue.get_current(chat_id):
        first_track = tracks.pop(0)
        queue.add(chat_id, first_track)

    added_text = playlist_to_queue(chat_id, tracks)

    if first_track:
        if not first_track.file_path:
            fname = f"downloads/{first_track.id}.webm"
            if Path(fname).exists():
                first_track.file_path = fname
            else:
                await sent.edit_text("📥 Downloading first mix track...")
                first_track.file_path = await yt.download(first_track.id, video=False)

        await Kartik.play_media(chat_id=chat_id, message=sent, media=first_track)
        if tracks:
            await app.send_message(
                chat_id=chat_id,
                text=f"🎶 <b>Queued {len(tracks)} mix tracks:</b>\n" + added_text,
            )
    else:
        await sent.edit_text(
            f"🎶 <b>Added {len(tracks)} mix tracks to queue:</b>\n" + added_text
        )
