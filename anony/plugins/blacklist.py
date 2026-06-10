# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, app, db, lang


@Bot.on_message(filters.command(["blacklist", "unblacklist", "whitelist"]))
@lang.language()
async def _blacklist(client, m: types.Message):
    if m.from_user.id not in client.sudoers:
        return
    if len(m.command) < 2:
        return await m.reply_text(m.lang["bl_usage"].format(m.command[0]))

    try:
        chat_id = m.command[1]
        if not str(chat_id).startswith("@"):
            chat_id = int(chat_id)
        else:
            chat_id = (await client.get_chat(chat_id)).id
    except Exception:
        return await m.reply_text(m.lang["bl_invalid"])

    if m.command[0] == "blacklist":
        if chat_id in (await db.get_blacklisted(client.id, chat=True)) or chat_id in client.bl_users:
            return await m.reply_text(m.lang["bl_already"])
        if not str(chat_id).startswith("-100"):
            client.bl_users.add(chat_id)
        await db.add_blacklist(chat_id, bot_id=client.id)
        await m.reply_text(m.lang["bl_added"])
    else:
        if chat_id not in (await db.get_blacklisted(client.id, chat=True)) and chat_id not in client.bl_users:
            return await m.reply_text(m.lang["bl_not"])
        if not str(chat_id).startswith("-100"):
            client.bl_users.discard(chat_id)
        await db.del_blacklist(chat_id, bot_id=client.id)
        await m.reply_text(m.lang["bl_removed"])
