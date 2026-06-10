# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import Bot, app, db, lang
from anony.helpers import utils


@Bot.on_message(filters.command(["addsudo", "delsudo", "rmsudo"]))
@lang.language()
async def _sudo(client, m: types.Message):
    if m.from_user.id != client.owner:
        return
    user = await utils.extract_user(m, client=client)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if m.command[0] == "addsudo":
        if user.id in client.sudoers:
            return await m.reply_text(m.lang["sudo_already"].format(user.mention))

        client.sudoers.add(user.id)
        await db.add_sudo(user.id, bot_id=client.id)
        await m.reply_text(m.lang["sudo_added"].format(user.mention))
    else:
        if user.id not in client.sudoers:
            return await m.reply_text(m.lang["sudo_not"].format(user.mention))

        client.sudoers.discard(user.id)
        await db.del_sudo(user.id, bot_id=client.id)
        await m.reply_text(m.lang["sudo_removed"].format(user.mention))


o_mention = None

@Bot.on_message(filters.command(["listsudo", "sudolist"]))
@lang.language()
async def _listsudo(client, m: types.Message):
    global o_mention
    sent = await m.reply_text(m.lang["sudo_fetching"])

    if not o_mention or o_mention.startswith("@"): # simple check if it needs refresh or is static
        o_mention = (await client.get_users(client.owner)).mention
    txt = m.lang["sudo_owner"].format(o_mention)
    sudoers = await db.get_sudoers(bot_id=client.id)
    if sudoers:
        txt += m.lang["sudo_users"]

    for user_id in sudoers:
        try:
            user = (await client.get_users(user_id)).mention
            txt += f"\n- {user}"
        except Exception:
            continue

    await sent.edit_text(txt)
