#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import html

from pyrogram import errors, raw, types

from KartikMusic import app, config, db, lang, logger
from KartikMusic.helpers import buttons


@app.on_chat_join_request()
async def join_request_handler(_, request: types.ChatJoinRequest):
    if not request.from_user or not request.chat:
        return

    user_id = request.from_user.id
    chat_id = request.chat.id

    # Automatically approve the user's join request immediately
    try:
        await app.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        logger.info(
            f"[join request] automatically approved user {user_id} in chat {chat_id}"
        )
    except Exception as err:
        logger.warning(
            f"[join request] auto-approve failed for user {user_id} in chat {chat_id}: {err}"
        )

    # Track user and chat in database
    try:
        if not await db.is_user(user_id):
            await db.add_user(user_id)
        if not await db.is_chat(chat_id):
            await db.add_chat(chat_id)
    except Exception:
        pass

    try:
        chat_lang = await lang.get_lang(chat_id)
    except Exception:
        chat_lang = lang.languages.get(config.LANG_CODE, {})

    name = html.escape(request.from_user.first_name or "User")
    user_link = f"<a href='tg://user?id={user_id}'>{name}</a>"

    title = html.escape(request.chat.title or "this chat")
    bot_mention = (
        app.mention or f"<a href='tg://user?id={app.id}'>{html.escape(app.name)}</a>"
    )

    caption_template = chat_lang.get("join_caption") or (
        "<b>HeY {user}</b>\n"
        "<b>YOUR REQUEST TO JOIn {chat}\n"
        "HAS BEEn APPROVED! </b>\n\n"
        "<b>I'M {bOt} - A HIGH QUALITY MUSIC STREAMING BOT FOR TELEGRAM GROUPS &\n"
        "CHANNELS\n</b>\n\n"
        "<b>JUST SEnD /\n"
        "StarT TO SEE BOT MENU AND COMMANDS\n</b>"
    )

    caption = (
        caption_template.replace("{user}", user_link)
        .replace("{chat}", title)
        .replace("{bot}", bot_mention)
        .replace("{bOt}", bot_mention)
    )

    markup = buttons.join_key(chat_lang)

    # UserChatId is the private chat with the user
    target = getattr(request, "user_chat_id", None) or user_id

    photo = config.START_IMG
    if photo:
        try:
            await app.send_photo(
                chat_id=target,
                photo=photo,
                caption=caption,
                reply_markup=markup,
            )
            return
        except (errors.Forbidden, errors.ChatWriteForbidden, errors.UserIsBlocked):
            logger.debug(f"[join request] user {user_id} blocked bot or cannot message")
            return
        except Exception as ex:
            logger.debug(f"[join request] photo to {target} failed, sending text: {ex}")

    try:
        await app.send_message(
            chat_id=target,
            text=caption,
            reply_markup=markup,
        )
    except Exception as ex:
        logger.debug(f"[join request] cannot message {target}: {ex}")


@app.on_raw_update()
async def pending_join_requests_handler(client, update, users, chats):
    # Automatically approves all pending requests in the chat
    update_name = update.__class__.__name__
    if update_name in ("UpdateChatPendingJoinRequests", "UpdatePendingJoinRequests"):
        chat_id = getattr(update, "chat_id", None) or getattr(
            update, "channel_id", None
        )
        if not chat_id:
            return
        try:
            peer = await client.resolve_peer(chat_id)
            if hasattr(raw.functions.messages, "HideAllChatJoinRequests"):
                await client.invoke(
                    raw.functions.messages.HideAllChatJoinRequests(
                        peer=peer,
                        approved=True,
                    )
                )
            count = getattr(
                getattr(update, "pending_join_requests", None),
                "total_count",
                "all",
            )
            logger.info(
                f"[join request] bulk auto-approved {count} pending join requests in chat {chat_id}"
            )
        except Exception as err:
            logger.debug(
                f"[join request] bulk auto-approve in chat {chat_id} failed: {err}"
            )
