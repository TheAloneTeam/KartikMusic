# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of KartikMusic

from pyrogram import filters, types

from KartikMusic import app, db, lang
from KartikMusic.helpers import admin_check, buttons


@app.on_message(filters.command(["clean", "cmddel", "delcmd", "cmddelete"]) & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def clean_toggle(_, m: types.Message):
    chat_id = m.chat.id
    enabled = await db.get_cmd_delete(chat_id)
    status = m.lang["clean_status_enabled"] if enabled else m.lang["clean_status_disabled"]
    markup = buttons.clean_markup(m.lang, chat_id, enabled)

    if len(m.command) == 1:
        return await m.reply_text(m.lang["clean_usage"].format(status), reply_markup=markup)

    action = m.command[1].lower()
    action_map = {
        "on": True,
        "off": False,
        "enable": True,
        "disable": False,
        "enabled": True,
        "disabled": False,
    }
    if action not in action_map:
        return await m.reply_text(m.lang["clean_usage"].format(status), reply_markup=markup)

    desired = action_map[action]
    if desired == enabled:
        return await m.reply_text(
            m.lang["clean_usage"].format(status),
            reply_markup=buttons.clean_markup(m.lang, chat_id, desired),
        )

    await db.set_cmd_delete(chat_id, desired)
    key = "clean_enabled" if desired else "clean_disabled"
    await m.reply_text(m.lang[key], reply_markup=buttons.clean_markup(m.lang, chat_id, desired))


@app.on_callback_query(filters.regex(r"^clean_tgl\s") & ~app.bl_users)
@lang.language()
@admin_check
async def clean_callback(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    enabled = await db.get_cmd_delete(chat_id)
    desired = not enabled
    await db.set_cmd_delete(chat_id, desired)

    status = query.lang["clean_status_enabled"] if desired else query.lang["clean_status_disabled"]
    await query.edit_message_text(
        query.lang["clean_usage"].format(status),
        reply_markup=buttons.clean_markup(query.lang, chat_id, desired)
    )
    await query.answer(query.lang["clean_enabled"] if desired else query.lang["clean_disabled"])
