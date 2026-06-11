# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of KartikMusic

import asyncio
import os
from pathlib import Path
from pyrogram import enums, errors, types
from KartikMusic import app, config, db, logger, queue, yt, Kartik
from KartikMusic.helpers import utils, buttons

async def stream_media(
    chat_id: int,
    sent: types.Message,
    track,
    mention: str,
    video: bool = False,
    force: bool = False
):
    """Core logic to add track to queue and start playback"""
    if track.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            sent.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        # Using getattr to safely get user mention if it's not a reply message
        user_mention = getattr(sent.reply_to_message, "from_user", sent.from_user).mention if sent.reply_to_message else mention
        await utils.play_log(sent, sent.link, track.title, track.duration)

    track.user = mention
    if force:
        current = queue.get_current(chat_id)
        if current and current.message_id:
            try:
                await app.delete_messages(chat_id, current.message_id)
            except Exception:
                pass
        queue.force_add(chat_id, track)
    else:
        position = queue.add(chat_id, track)

        if position != 0 or await db.get_call(chat_id):
            return await sent.edit_text(
                sent.lang["play_queued"].format(
                    position,
                    track.url,
                    track.title,
                    track.duration,
                    mention,
                ),
                reply_markup=buttons.play_queued(
                    chat_id, track.id, sent.lang["play_now"]
                ),
            )

    if not track.file_path:
        fname = f"downloads/{track.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            track.file_path = fname
        else:
            await sent.edit_text(sent.lang["play_downloading"])
            track.file_path = await yt.download(track.id, video=video)

    await Kartik.play_media(chat_id=chat_id, message=sent, media=track)

async def check_assistant_and_join(chat_id: int, sent: types.Message) -> bool:
    """Ensures the assistant is in the chat and ready"""
    if chat_id in db.active_calls:
        return True

    client = await db.get_client(chat_id)
    try:
        member = await app.get_chat_member(chat_id, client.id)
        if member.status in [
            enums.ChatMemberStatus.BANNED,
            enums.ChatMemberStatus.RESTRICTED,
        ]:
            try:
                await app.unban_chat_member(chat_id=chat_id, user_id=client.id)
            except Exception:
                await sent.edit_text(
                    sent.lang["play_banned"].format(
                        app.name,
                        client.id,
                        client.mention,
                        f"@{client.username}" if client.username else None,
                    )
                )
                return False
    except errors.ChatAdminRequired:
        await sent.edit_text(sent.lang["admin_required"])
        return False
    except (
        errors.UserNotParticipant,
        errors.exceptions.bad_request_400.UserNotParticipant,
    ):
        invite_link = None
        if (await app.get_chat(chat_id)).username:
            invite_link = (await app.get_chat(chat_id)).username
        else:
            try:
                invite_link = (await app.get_chat(chat_id)).invite_link
                if not invite_link:
                    invite_link = await app.export_chat_invite_link(chat_id)
            except errors.ChatAdminRequired:
                await sent.edit_text(sent.lang["admin_required"])
                return False
            except Exception as ex:
                await sent.edit_text(
                    sent.lang["play_invite_error"].format(type(ex).__name__)
                )
                return False

        await sent.edit_text(sent.lang["play_invite"].format(app.name))
        await asyncio.sleep(2)
        try:
            await client.join_chat(invite_link)
        except errors.UserAlreadyParticipant:
            pass
        except errors.InviteRequestSent:
            await asyncio.sleep(2)
            try:
                await app.approve_chat_join_request(chat_id, client.id)
            except errors.HideRequesterMissing:
                pass
            except Exception as ex:
                await sent.edit_text(
                    sent.lang["play_invite_error"].format(type(ex).__name__)
                )
                return False
        except Exception as ex:
            logger.error(f"Error joining chat - {chat_id}: {ex}")
            await sent.edit_text(
                sent.lang["play_invite_error"].format(type(ex).__name__)
            )
            return False

        await client.resolve_peer(chat_id)

    return True
