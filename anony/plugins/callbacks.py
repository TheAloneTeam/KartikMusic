# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import re
import time
from pyrogram import enums, errors, filters, types

from anony import anon, app, db, lang, queue, tg, yt
from anony.helpers import admin_check, buttons, can_manage_vc


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])
    qaction = len(args) == 4
    user = query.from_user.mention

    if not await db.get_call(chat_id):
        try:
            return await query.answer(query.lang["not_playing"], show_alert=True)
        except errors.QueryIdInvalid:
            try:
                await query.message.delete()
            except Exception:
                pass
            return

    if action == "status":
        return await query.answer()
    await query.answer(query.lang["processing"], show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id):
            return await query.answer(
                query.lang["play_already_paused"], show_alert=True
            )
        await anon.pause(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["paused"], False)
            )
        status = query.lang["paused"]
        reply = query.lang["play_paused"].format(user)

    elif action == "resume":
        if await db.playing(chat_id):
            return await query.answer(query.lang["play_not_paused"], show_alert=True)
        await anon.resume(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["playing"], True)
            )
        reply = query.lang["play_resumed"].format(user)

    elif action == "skip":
        await anon.play_next(chat_id)
        status = query.lang["skipped"]
        reply = query.lang["play_skipped"].format(user)

    elif action == "force":
        pos, media = queue.check_item(chat_id, args[3])
        if not media or pos == -1:
            return await query.edit_message_text(query.lang["play_expired"])

        current = queue.get_current(chat_id)
        if current and current.message_id:
            try:
                await app.delete_messages(chat_id, current.message_id)
            except Exception:
                pass

        queue.force_add(chat_id, media, remove=pos)

        msg = query.message
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)

        media.message_id = msg.id
        return await anon.play_media(chat_id, msg, media)

    elif action == "replay":
        media = queue.get_current(chat_id)
        media.user = user
        await anon.replay(chat_id)
        status = query.lang["replayed"]
        reply = query.lang["play_replayed"].format(user)

    elif action == "stop":
        await anon.stop(chat_id)
        status = query.lang["stopped"]
        reply = query.lang["play_stopped"].format(user)

    elif action == "seek":
        if not await db.playing(chat_id):
            return await query.answer(
                query.lang["play_already_paused"], show_alert=True
            )

        media = queue.get_current(chat_id)
        if not media or not media.duration_sec:
            return await query.answer(
                query.lang["play_seek_no_dur"], show_alert=True
            )

        to_seek = int(args[3])
        current_pos = int((time.time() - media.played_at) + media.time)
        new_pos = current_pos + to_seek

        if new_pos < 1:
            new_pos = 1
        elif new_pos + 10 > media.duration_sec:
            new_pos = media.duration_sec - 5

        await anon.play_media(chat_id, query.message, media, new_pos)
        media.time = new_pos
        return await query.answer(
            f"Seeked to {new_pos}s", show_alert=True
        )

    elif action == "close":
        try:
            return await query.message.delete()
        except Exception:
            return

    elif action in ["more", "cautoplay", "cthumb", "back"]:
        if action == "cautoplay":
            autoplay = not await db.get_autoplay(chat_id)
            await db.set_autoplay(chat_id, autoplay)
        elif action == "cthumb":
            thumb = not await db.get_thumb_mode(chat_id)
            await db.set_thumb_mode(chat_id, thumb)

        autoplay = await db.get_autoplay(chat_id)
        thumb = await db.get_thumb_mode(chat_id)

        keyboard = buttons.controls(
            chat_id,
            more=action != "back",
            autoplay=autoplay,
            thumb=thumb,
        )
        try:
            return await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception:
            return

    try:
        if action in ["skip", "replay", "stop"]:
            await query.message.reply_text(reply, quote=False)
            await query.message.delete()
        else:
            mtext = re.sub(
                r"\n\n<blockquote>.*?</blockquote>",
                "",
                query.message.caption.html or query.message.text.html,
                flags=re.DOTALL,
            )
            keyboard = buttons.controls(
                chat_id, status=status if action != "resume" else None
            )
        await query.edit_message_text(
            f"{mtext}\n\n<blockquote>{reply}</blockquote>", reply_markup=keyboard
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex("help") & ~app.bl_users)
@lang.language()
async def _help(_, query: types.CallbackQuery):
    data = query.data.split()
    if len(data) == 1:
        _text = query.lang["help_menu"]
        _key = buttons.help_markup(query.lang)
    elif data[1] == "home":
        private = query.message.chat.type == enums.ChatType.PRIVATE
        _text = (
            query.lang["start_pm"].format(query.from_user.first_name, app.name)
            if private
            else query.lang["start_gp"].format(app.name)
        )
        _key = buttons.start_key(query.lang, private)
    elif data[1] == "back":
        _text = query.lang["help_menu"]
        _key = buttons.help_markup(query.lang)
    elif data[1] == "close":
        try:
            await query.message.delete()
            return await query.message.reply_to_message.delete()
        except Exception:
            return
    else:
        _text = query.lang[f"help_{data[1]}"]
        _key = buttons.help_markup(query.lang, True)

    try:
        if query.message.photo or query.message.video:
            await query.edit_message_caption(caption=_text, reply_markup=_key)
        else:
            await query.edit_message_text(text=_text, reply_markup=_key)
    except Exception:
        pass


@app.on_callback_query(filters.regex("settings") & ~app.bl_users)
@lang.language()
@admin_check
async def _settings_cb(_, query: types.CallbackQuery):
    cmd = query.data.split()
    if len(cmd) == 1:
        return await query.answer()
    await query.answer(query.lang["processing"], show_alert=True)

    chat_id = query.message.chat.id
    _admin = await db.get_play_mode(chat_id)
    _delete = await db.get_cmd_delete(chat_id)
    _autoplay = await db.get_autoplay(chat_id)
    _vclog = await db.get_vclogger(chat_id)
    _thumbnail = await db.get_thumb_mode(chat_id)
    _language = await db.get_lang(chat_id)

    if cmd[1] == "delete":
        _delete = not _delete
        await db.set_cmd_delete(chat_id, _delete)
    elif cmd[1] == "play":
        await db.set_play_mode(chat_id, _admin)
        _admin = not _admin
    elif cmd[1] == "autoplay":
        _autoplay = not _autoplay
        await db.set_autoplay(chat_id, _autoplay)
    elif cmd[1] == "vclog":
        _vclog = not _vclog
        await db.set_vclogger(chat_id, _vclog)
    elif cmd[1] == "thumb":
        _thumbnail = not _thumbnail
        await db.set_thumb_mode(chat_id, _thumbnail)

    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            _admin,
            _delete,
            _autoplay,
            _vclog,
            _thumbnail,
            _language,
            chat_id,
        )
    )
