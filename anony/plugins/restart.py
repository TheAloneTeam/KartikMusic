# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import sys
import shutil
import asyncio

from pyrogram import filters, types

from anony import Bot, app, db, lang, stop


@Bot.on_message(filters.command(["logs"]))
@lang.language()
async def _logs(client, m: types.Message):
    if m.from_user.id not in client.sudoers:
        return
    sent = await m.reply_text(m.lang["log_fetch"])
    if not os.path.exists("log.txt"):
        return await sent.edit_text(m.lang["log_not_found"])
    await sent.edit_media(
        media=types.InputMediaDocument(
            media="log.txt",
            caption=m.lang["log_sent"].format(client.name),
        )
    )


@Bot.on_message(filters.command(["logger"]))
@lang.language()
async def _logger(client, m: types.Message):
    if m.from_user.id not in client.sudoers:
        return
    if len(m.command) < 2:
        return await m.reply_text(m.lang["logger_usage"].format(m.command[0]))
    if m.command[1] not in ("on", "off"):
        return await m.reply_text(m.lang["logger_usage"].format(m.command[0]))

    if m.command[1] == "on":
        await db.set_logger(True)
        await m.reply_text(m.lang["logger_on"])
    else:
        await db.set_logger(False)
        await m.reply_text(m.lang["logger_off"])


@Bot.on_message(filters.command(["restart"]))
@lang.language()
async def _restart(client, m: types.Message):
    if m.from_user.id not in client.sudoers:
        return
    if client.id != app.id:
        return await m.reply_text("Only the main bot can be restarted.")
    sent = await m.reply_text(m.lang["restarting"])

    for directory in ["cache", "downloads"]:
        shutil.rmtree(directory, ignore_errors=True)

    await sent.edit_text(m.lang["restarted"])
    task = asyncio.create_task(stop())
    await task

    try: os.remove("log.txt")
    except Exception: pass

    os.execl(sys.executable, sys.executable, "-m", "anony")
