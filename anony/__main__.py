# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import signal
import importlib
from contextlib import suppress

from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt)
from anony.plugins import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()

async def main():
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    # Boot clones
    clones = await db.get_clones()
    for clone in clones:
        try:
            from anony.core.bot import Bot as BotClass
            from anony.core.userbot import Userbot as UserbotClass

            clone_bot = BotClass(bot_token=clone["bot_token"], owner_id=clone["owner_id"])
            await clone_bot.boot()

            clone_userbot = UserbotClass(session=clone["session"])
            await clone_userbot.boot()

            await anon.boot_clone(clone_userbot, clone_bot)
            logger.info(f"Clone @{clone_bot.username} booted successfully.")
        except Exception as e:
            logger.error(f"Failed to boot clone: {e}")

    await idle()
    asyncio.create_task(stop())


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
