#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import time
from collections import defaultdict

from ntgcalls import (
    ConnectionError,
    ConnectionNotFound,
    RTMPStreamingUnsupported,
    TelegramServerError,
)
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from KartikMusic import app, config, db, lang, logger, queue, thumb, userbot, yt
from KartikMusic.helpers import Media, Track, buttons


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []
        self.restarting = defaultdict(int)
        self.prefetch_tasks = {}

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)

        media = queue.get_current(chat_id)
        if media and media.played_at:
            media.time += int(time.time() - media.played_at)
            media.played_at = None

        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)

        media = queue.get_current(chat_id)
        if media:
            media.played_at = time.time()

        return await client.resume(chat_id)

    async def _prepare_next(self, chat_id: int) -> None:
        try:
            while await db.get_call(chat_id):
                if not await db.get_autoplay(chat_id):
                    await asyncio.sleep(10)
                    continue

                media = queue.get_current(chat_id)
                if not media or not media.duration_sec:
                    break

                played_sec = media.time
                if media.played_at:
                    played_sec += int(time.time() - media.played_at)

                remaining = media.duration_sec - played_sec

                if remaining <= 15:
                    next_media = queue.get_next(chat_id, check=True)
                    if not next_media and await db.get_autoplay(chat_id):
                        if isinstance(media, Track):
                            max_duration = min(int(media.duration_sec * 1.5), 900)
                            next_media = await yt.get_related(
                                media.id, video=media.video, max_duration=max_duration
                            )
                            if next_media:
                                queue.add(chat_id, next_media)

                    if next_media and not next_media.file_path:
                        next_media.file_path = await yt.download(
                            next_media.id, video=next_media.video
                        )
                    break

                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in prefetch for {chat_id}: {e}")
        finally:
            self.prefetch_tasks.pop(chat_id, None)

    async def stop(self, chat_id: int) -> None:
        if task := self.prefetch_tasks.pop(chat_id, None):
            task.cancel()

        client = await db.get_assistant(chat_id)
        media = queue.get_current(chat_id)
        if media and media.message_id:
            try:
                await app.delete_messages(chat_id, media.message_id)
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
    ) -> None:
        if task := self.prefetch_tasks.pop(chat_id, None):
            task.cancel()

        self.restarting[chat_id] += 1
        if await db.get_call(chat_id):
            await asyncio.sleep(0.5)
        client = await db.get_assistant(chat_id)
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
                keyboard = buttons.controls(chat_id, lang=_lang)
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
                        sent = await app.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    else:
                        sent = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    media.message_id = sent.id

            self.prefetch_tasks[chat_id] = asyncio.create_task(
                self._prepare_next(chat_id)
            )
        except FileNotFoundError:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (asyncio.TimeoutError, TimeoutError):
            await message.edit_text(_lang["error_tg_server"])
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

    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if media and media.message_id:
            try:
                await app.delete_messages(chat_id, media.message_id)
            except Exception:
                pass
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)

    async def play_next(self, chat_id: int, skip_user: str = None) -> None:
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        _lang = await lang.get_lang(chat_id)
        current = queue.get_current(chat_id)
        if current and current.message_id:
            try:
                await app.delete_messages(chat_id, current.message_id)
            except Exception:
                pass

        media = queue.get_next(chat_id)
        if not media:
            if await db.get_autoplay(chat_id):
                if current and isinstance(current, Track):
                    msg = None
                    if skip_user:
                        msg = await app.send_message(
                            chat_id, _lang["autoplay_skip"].format(skip_user)
                        )
                    else:
                        msg = await app.send_message(chat_id, _lang["autoplay_next"])

                    # Set max duration for autoplay tracks based on current song
                    # but capped at 15 minutes to avoid extremely long tracks
                    # Use existing next item if it was pre-fetched
                    media = queue.get_current(chat_id)
                    if not media:
                        max_duration = min(int(current.duration_sec * 1.5), 900)
                        media = await yt.get_related(
                            current.id, video=current.video, max_duration=max_duration
                        )
                        if media:
                            queue.add(chat_id, media)

                    if media:
                        # Re-fetch from queue in case it was just added to ensure
                        # we have the object that might have file_path set by prefetcher
                        media = queue.get_current(chat_id)

                        if not media.file_path:
                            media.file_path = await yt.download(
                                media.id, video=media.video
                            )
                            if not media.file_path:
                                await self.stop(chat_id)
                                try:
                                    return await msg.edit_text(
                                        _lang["error_no_file"].format(
                                            config.SUPPORT_CHAT
                                        )
                                    )
                                except Exception:
                                    pass
                                return

                        media.message_id = msg.id
                        return await self.play_media(chat_id, msg, media)
                    else:
                        await self.stop(chat_id)
                        if msg:
                            return await msg.edit_text(_lang["queue_finished"])
                        return await app.send_message(chat_id, _lang["queue_finished"])
                else:
                    await self.stop(chat_id)
                    return await app.send_message(chat_id, _lang["queue_finished"])
            else:
                await self.stop(chat_id)
                if skip_user:
                    await app.send_message(
                        chat_id, _lang["play_skipped"].format(skip_user)
                    )
                return await app.send_message(chat_id, _lang["queue_finished"])

        # If we reached here, media was already retrieved by queue.get_next above

        msg = None
        if media.message_id:
            try:
                msg = await app.get_messages(chat_id, media.message_id)
                if not msg or not msg.id or msg.empty:
                    msg = None
                else:
                    try:
                        text = (
                            _lang["play_skipped"].format(skip_user)
                            + "\n\n"
                            + _lang["play_next"]
                            if skip_user
                            else _lang["play_next"]
                        )
                        await msg.edit_text(text)
                    except Exception:
                        pass
            except Exception:
                msg = None

        if not msg:
            text = (
                _lang["play_skipped"].format(skip_user) + "\n\n" + _lang["play_next"]
                if skip_user
                else _lang["play_next"]
            )
            msg = await app.send_message(chat_id=chat_id, text=text)

        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                if msg:
                    try:
                        await msg.edit_text(
                            _lang["error_no_file"].format(config.SUPPORT_CHAT)
                        )
                    except Exception:
                        pass
                return await self.play_next(chat_id)

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)

    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)

    async def _delete_msg(self, message: Message, delay: int = 2):
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception:
            pass

    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.UpdatedGroupCallParticipant):
                if not await db.get_vclogger(update.chat_id):
                    return
                try:
                    user = await app.get_users(update.participant.user_id)
                except Exception:
                    return

                _lang = await lang.get_lang(update.chat_id)
                if update.action == types.GroupCallParticipant.Action.JOINED:
                    text = _lang["vclog_joined"].format(user.mention, user.id)
                elif update.action == types.GroupCallParticipant.Action.LEFT:
                    text = _lang["vclog_left"].format(user.mention, user.id)
                else:
                    return

                try:
                    sent = await app.send_message(update.chat_id, text)
                    asyncio.create_task(self._delete_msg(sent))
                except Exception:
                    pass

            elif isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    if self.restarting.get(update.chat_id):
                        return
                    await self.play_next(update.chat_id)
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
