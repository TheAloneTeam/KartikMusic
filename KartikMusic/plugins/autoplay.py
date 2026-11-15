#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from KartikMusic import app, db, lang
from KartikMusic.helpers import can_manage_vc 


def autoplay_markup(state: bool) -> InlineKeyboardMarkup:
    btn_text = "Autoplay: ON | ✅" if state else "Autoplay: OFF | ❌"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=btn_text, callback_data="autoplay_toggle")]]
    )


@app.on_message(filters.command(["autoplay"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(_, m: types.Message):
    if len(m.command) > 1:
        arg = m.command[1].lower()
        if arg in ["enable", "on"]:
            await db.set_autoplay(m.chat.id, True)
            return await m.reply_text(m.lang["autoplay_on"].format(m.from_user.mention))
        elif arg in ["disable", "off"]:
            await db.set_autoplay(m.chat.id, False)
            queue.clear_autoplay_history(m.chat.id)
            return await m.reply_text(
                m.lang["autoplay_off"].format(m.from_user.mention)
            )

    state = await db.get_autoplay(m.chat.id)
    text = (
        "<b>Autoplay Control</b>\n\n"
        "When autoplay is enabled, the bot will automatically play recommended songs "
        "from supported platforms when the queue is empty."
    )
    return await m.reply_text(text, reply_markup=autoplay_markup(state))


@app.on_callback_query(filters.regex(r"^autoplay_toggle$") & ~app.bl_users)
@can_manage_vc
async def _autoplay_callback(_, cb: types.CallbackQuery):
    chat_id = cb.message.chat.id
    current_state = await db.get_autoplay(chat_id)
    new_state = not current_state
    await db.set_autoplay(chat_id, new_state)

    if not new_state:
        queue.clear_autoplay_history(chat_id)

    status_str = "enabled" if new_state else "disabled"
    await cb.answer(f"Autoplay has been {status_str}.", show_alert=False)

    text = (
        "<b>Autoplay Control</b>\n\n"
        "When autoplay is enabled, the bot will automatically play recommended songs "
        "from supported platforms when the queue is empty."
    )
    try:
        await cb.edit_message_text(text, reply_markup=autoplay_markup(new_state))
    except Exception:
        pass
