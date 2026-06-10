# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time

from pyrogram import filters, types

from anony import Bot, app, db, lang
from anony.helpers import admin_check, is_admin, utils


@Bot.on_message(filters.command(["auth", "unauth"]) & filters.group & ~filters.bl_users)
@lang.language()
@admin_check
async def _auth(client, m: types.Message):
    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if m.command[0] == "auth":
        if await is_admin(m.chat.id, user.id):
            return await m.reply_text(m.lang["auth_is_admin"])

        await db.add_auth(m.chat.id, user.id)
        await m.reply_text(m.lang["auth_added"].format(user.mention))
    else:
        await db.rm_auth(m.chat.id, user.id)
        await m.reply_text(m.lang["auth_removed"].format(user.mention))


@Bot.on_message(filters.command(["authlist"]) & filters.group & ~filters.bl_users)
@lang.language()
@admin_check
async def _authlist(client, m: types.Message):
    auth = await db._get_auth(m.chat.id)
    if not auth:
        return await m.reply_text(m.lang["auth_empty"])

    auth_txt = m.lang["auth_list"].format(m.chat.title)
    for i, user in enumerate(auth, start=1):
        auth_txt += f"\n{i}. <a href=tg://user?id={user}>{user}</a>"
    await m.reply_text(auth_txt)


rel_hist = {}

@Bot.on_message(filters.command(["admincache", "reload"]) & filters.group & ~filters.bl_users)
@lang.language()
async def _admincache(client, m: types.Message):
    if m.from_user.id in rel_hist:
        if time.time() < rel_hist[m.from_user.id]:
            return await m.reply_text(m.lang["admin_cache_wait"])

    rel_hist[m.from_user.id] = time.time() + 600
    sent = await m.reply_text(m.lang["admin_cache_reloading"])
    await db.get_admins(m.chat.id, reload=True)
    await sent.edit_text(m.lang["admin_cache_reloaded"])
