# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
import asyncio
from collections import defaultdict
from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
from pyrogram.errors import (ChatSendMediaForbidden, ChatSendPhotosForbidden,
                             MessageIdInvalid)
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import (app, config, db, lang, logger,
                   queue, thumb, userbot, yt)
from anony.helpers import Media, Track, buttons


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []
        self.restarting = defaultdict(int)
        self.bots = {}

    async def pause(self, chat_id: int, bot_id: int = None, client_bot= None) -> bool:
        client = await db.get_assistant(chat_id, bot_id=bot_id, client_bot=client_bot)
        await db.playing(chat_id, paused=True)

        media = queue.get_current(chat_id)
        if media and media.played_at:
            media.time += int(time.time() - media.played_at)
            media.played_at = None

        return await client.pause(chat_id)

    async def resume(self, chat_id: int, bot_id: int = None, client_bot= None) -> bool:
        client = await db.get_assistant(chat_id, bot_id=bot_id, client_bot=client_bot)
        await db.playing(chat_id, paused=False)

        media = queue.get_current(chat_id)
        if media:
            media.played_at = time.time()

        return await client.resume(chat_id)

    async def stop(self, chat_id: int, client_bot= None) -> None:
        _bot = client_bot or app
        client = await db.get_assistant(chat_id, bot_id=_bot.id, client_bot=_bot)
        media = queue.get_current(chat_id)
        if media and media.message_id:
            try:
                await _bot.delete_messages(chat_id, media.message_id)
            except Exception:
                pass
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
        client= None,
    ) -> None:
        self.restarting[chat_id] += 1
        if await db.get_call(chat_id):
            await asyncio.sleep(0.5)

        _bot = client or app
        client = await db.get_assistant(chat_id, bot_id=_bot.id, client_bot=_bot)
        _lang = await lang.get_lang(chat_id)
        _thumb_mode = await db.get_thumb_mode(chat_id)
        _thumb = (
            (
                await thumb.generate(media)
                if isinstance(media, Track)
                else config.DEFAULT_THUMB
            )
            if config.THUMB_GEN and _thumb_mode
            else None
        )

        if not media.file_path:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        ffmpeg_params = (
            (f"-ss {seek_time} " if seek_time > 1 else "")
            + ("-vn" if not media.video else "")
        ).strip()

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=ffmpeg_params or None,
        )

        try:
            if seek_time:
                await client.play(chat_id, stream)
            elif await db.get_call(chat_id):
                try:
                    logger.info(f"Changing stream for {chat_id} with params: {ffmpeg_params}")
                    await client.change_stream(chat_id, stream)
                except Exception as e:
                    logger.error(f"Error in change_stream: {e}")
                    await client.play(chat_id, stream)
            else:
                await client.play(chat_id, stream)

            media.played_at = time.time()
            if seek_time:
                media.time = seek_time
            else:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                try:
                    if _thumb:
                        await message.edit_media(
                            media=InputMediaPhoto(
                                media=_thumb,
                                caption=text,
                            ),
                            reply_markup=keyboard,
                        )
                    else:
                        await message.edit_text(text, reply_markup=keyboard)
                except Exception:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    if _thumb:
                        sent = await _bot.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    else:
                        sent = await _bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    media.message_id = sent.id
        except FileNotFoundError:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_rtmp"])
        finally:
            await asyncio.sleep(5)
            self.restarting[chat_id] -= 1


    async def replay(self, chat_id: int, client_bot= None) -> None:
        _bot = client_bot or app
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if media and media.message_id:
            try:
                await _bot.delete_messages(chat_id, media.message_id)
            except Exception:
                pass
        _lang = await lang.get_lang(chat_id)
        msg = await _bot.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media, client=_bot)


    async def play_next(self, chat_id: int, client_bot= None) -> None:
        _bot = client_bot or app
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        current = queue.get_current(chat_id)
        if current and current.message_id:
            try:
                await _bot.delete_messages(chat_id, current.message_id)
            except Exception:
                pass

        media = queue.get_next(chat_id)
        if not media:
            if await db.get_autoplay(chat_id):
                if current and isinstance(current, Track):
                    # Set max duration for autoplay tracks based on current song
                    # but capped at 15 minutes to avoid extremely long tracks
                    max_duration = min(int(current.duration_sec * 1.5), 900)
                    media = await yt.get_related(
                        current.id, video=current.video, max_duration=max_duration
                    )
                    if media:
                        queue.add(chat_id, media)
                    else:
                        return await self.stop(chat_id, client_bot=_bot)
                else:
                    return await self.stop(chat_id, client_bot=_bot)
            else:
                return await self.stop(chat_id, client_bot=_bot)

        _lang = await lang.get_lang(chat_id)
        msg = None
        if media.message_id:
            try:
                msg = await _bot.get_messages(chat_id, media.message_id)
                if not msg or not msg.id or msg.empty:
                    msg = None
                else:
                    try:
                        await msg.edit_text(_lang["play_next"])
                    except Exception:
                        pass
            except Exception:
                msg = None

        if not msg:
            msg = await _bot.send_message(chat_id=chat_id, text=_lang["play_next"])

        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.play_next(chat_id, client_bot=_bot)
                if msg:
                    try:
                        return await msg.edit_text(
                            _lang["error_no_file"].format(config.SUPPORT_CHAT)
                        )
                    except Exception:
                        pass
                return

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media, client=_bot)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls, client_bot= None) -> None:
        @client.on_update()
        async def update_handler(c: PyTgCalls, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    if self.restarting.get(update.chat_id):
                        return
                    _bot = client_bot or self.bots.get(c.app.me.id)
                    await self.play_next(update.chat_id, client_bot=_bot)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")

    async def boot_clone(self, ub: Userbot, bot) -> None:
        client = PyTgCalls(ub.one, cache_duration=100)
        await client.start()
        self.clients.append(client)
        self.bots[ub.one.me.id] = bot
        await self.decorators(client, client_bot=bot)
