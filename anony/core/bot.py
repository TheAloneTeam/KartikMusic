# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import pyrogram
from pyrogram import handlers, filters

from anony import config, logger

async def bl_filter(_, client, update):
    if not update.from_user:
        return False
    return update.from_user.id in client.bl_users

async def sudo_filter(_, client, update):
    if not update.from_user:
        return False
    return update.from_user.id in client.sudoers

filters.bl_users = filters.create(bl_filter)
filters.sudo_users = filters.create(sudo_filter)

class Bot(pyrogram.Client):
    _handlers = []

    def __init__(self, bot_token: str = None, owner_id: int = None):
        super().__init__(
            name="anony" if not bot_token else f"bot_{bot_token.split(':')[0]}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token or config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        )
        self.owner = owner_id or config.OWNER_ID
        self.logger = config.LOGGER_ID
        self.bl_users = set()
        self.sudoers = {self.owner}
        self.clones_assistants = {}

        for handler, group in self._handlers:
            self.add_handler(handler, group)

    @classmethod
    def on_message(cls, filters=None, group=0):
        def decorator(func):
            cls._handlers.append((handlers.MessageHandler(func, filters), group))
            return func
        return decorator

    @classmethod
    def on_callback_query(cls, filters=None, group=0):
        def decorator(func):
            cls._handlers.append((handlers.CallbackQueryHandler(func, filters), group))
            return func
        return decorator

    @classmethod
    def on_inline_query(cls, filters=None, group=0):
        def decorator(func):
            cls._handlers.append((handlers.InlineQueryHandler(func, filters), group))
            return func
        return decorator

    @classmethod
    def on_edited_message(cls, filters=None, group=0):
        def decorator(func):
            cls._handlers.append((handlers.EditedMessageHandler(func, filters), group))
            return func
        return decorator

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        from anony import db
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        self.sudoers.update(await db.get_sudoers(self.id))
        self.bl_users.update(await db.get_blacklisted(self.id))

        try:
            await self.send_message(self.logger, "Bot Started")
            get = await self.get_chat_member(self.logger, self.id)
            if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
                logger.warning(f"Bot @{self.username} is not an admin in logger group.")
        except Exception as ex:
            logger.warning(f"Bot @{self.username} failed to access the log group: {self.logger}\nReason: {ex}")

        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await super().stop()
        logger.info("Bot stopped.")
