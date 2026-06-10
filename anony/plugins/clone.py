# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import re
from pyrogram import filters, types, Client, enums
from pyrogram.errors import TokenInvalid, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, FloodWait

from anony import Bot, app, db, lang, logger
from anony.core.bot import Bot as BotClass
from anony.core.userbot import Userbot

# Simple storage for clone state
clone_states = {}

@Bot.on_message(filters.command(["clone"]) & filters.private & ~filters.bl_users)
@lang.language()
async def clone_bot(client, message: types.Message):
    await message.reply_text(
        "To clone the bot, please provide your **Bot Token** from @BotFather."
    )
    clone_states[message.from_user.id] = {"step": "token"}

@Bot.on_message(filters.private & ~filters.bl_users, group=1)
async def clone_input_handler(client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in clone_states:
        return

    state = clone_states[user_id]
    step = state.get("step")

    if step == "token":
        token = message.text.strip()
        if not re.match(r"\d+:[a-zA-Z0-9_-]+", token):
            return await message.reply_text("Invalid Bot Token. Please try again.")

        state["token"] = token
        state["step"] = "session"
        await message.reply_text(
            "Now please provide your **String Session**.\n"
            "You can generate it using @SessionGenBot or any other session generator."
        )

    elif step == "session":
        session = message.text.strip()
        token = state.get("token")

        msg = await message.reply_text("Cloning your bot... please wait.")

        try:
            # Try to start the cloned bot to verify
            clone_bot = BotClass(bot_token=token, owner_id=user_id)
            await clone_bot.start()

            # Try to start the cloned assistant
            clone_userbot = Userbot(session=session)
            await clone_userbot.one.start()

            # If both started successfully, save to DB
            await db.add_clone(token, session, user_id)

            await msg.edit_text(
                f"Successfully cloned! Your bot @{clone_bot.me.username} is now running.\n"
                f"You are the owner of this clone."
            )

            await clone_bot.stop()
            await clone_userbot.one.stop()

        except TokenInvalid:
            await msg.edit_text("The Bot Token you provided is invalid.")
        except Exception as e:
            await msg.edit_text(f"An error occurred during cloning: {str(e)}")
        finally:
            if user_id in clone_states:
                del clone_states[user_id]

@Bot.on_message(filters.command(["clones"]))
@lang.language()
async def list_clones(client, message: types.Message):
    if message.from_user.id != client.owner:
        return
    clones = await db.get_clones()
    if not clones:
        return await message.reply_text("No clones found.")

    text = "**List of Clones:**\n\n"
    for i, clone in enumerate(clones, 1):
        text += f"{i}. Bot Token: `{clone['bot_token']}`\n   Owner ID: `{clone['owner_id']}`\n\n"

    await message.reply_text(text)

@Bot.on_message(filters.command(["delclone"]) & filters.private & ~filters.bl_users)
@lang.language()
async def delete_clone(client, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /delclone [bot_token]")

    token = message.command[1]
    clones = await db.get_clones()
    clone = next((c for c in clones if c['bot_token'] == token), None)

    if not clone:
        return await message.reply_text("Clone not found.")

    if clone['owner_id'] != message.from_user.id and message.from_user.id not in client.sudoers:
        return await message.reply_text("You are not the owner of this clone.")

    deleted = await db.rm_clone(token)
    if deleted:
        await message.reply_text("Clone deleted successfully. It will stop on next restart.")
    else:
        await message.reply_text("Failed to delete clone.")
