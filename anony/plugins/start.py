# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from pyrogram import enums, filters, types

from anony import Bot, app, config, db, lang
from anony.helpers import buttons, utils


@Bot.on_message(filters.command(["help"]) & filters.private & ~filters.bl_users)
@lang.language()
async def _help(client, m: types.Message):
    await m.reply_text(
        text=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
        quote=True,
    )


@Bot.on_message(filters.command(["start"]))
@lang.language()
async def start(client, message: types.Message):
    if message.from_user.id in client.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, client.name)
        if private
        else message.lang["start_gp"].format(client.name)
    )

    key = buttons.start_key(message.lang, private, username=client.username, owner_id=client.owner)
    await message.reply_photo(
        photo=config.START_IMG,
        caption=_text,
        reply_markup=key,
        quote=not private,
    )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message, client=client)
        await db.add_user(message.from_user.id)
    else:
        if await db.is_chat(message.chat.id):
            return
        await utils.send_log(message, True, client=client)
        await db.add_chat(message.chat.id)


@Bot.on_message(filters.command(["playmode", "settings"]) & filters.group & ~filters.bl_users)
@lang.language()
async def settings(client, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    thumbnail = await db.get_thumb_mode(message.chat.id)
    autoplay = await db.get_autoplay(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply_text(
        text=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang,
            admin_only,
            cmd_delete,
            autoplay,
            thumbnail,
            _language,
            message.chat.id,
        ),
        quote=True,
    )


@Bot.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(client, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == client.id:
            if await db.is_chat(message.chat.id):
                return
            await utils.send_log(message, True, client=client)
            await db.add_chat(message.chat.id)
