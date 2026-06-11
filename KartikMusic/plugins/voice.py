# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of KartikMusic

import os
import asyncio
import speech_recognition as sr
from pydub import AudioSegment
from pyrogram import filters, types, enums

from KartikMusic import app, lang, yt, config, db, logger
from KartikMusic.helpers.play_helper import stream_media, check_assistant_and_join

# Initialize recognizer
recognizer = sr.Recognizer()

def convert_to_wav(file_path, wav_path):
    audio = AudioSegment.from_file(file_path)
    audio.export(wav_path, format="wav")

def transcribe_audio(wav_path):
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)

@app.on_message(filters.voice & filters.group & ~app.bl_users)
@lang.language()
async def voice_play_hndlr(_, m: types.Message):
    # Supergroup check
    chat_id = m.chat.id
    if m.chat.type != enums.ChatType.SUPERGROUP:
        return

    # Ignore voice messages longer than 15 seconds to save resources
    if m.voice.duration > 15:
        return

    # Download
    file_path = await m.download()
    if not file_path:
        return

    wav_path = file_path.replace(".ogg", ".wav")
    try:
        # Blocking operations moved to thread
        await asyncio.to_thread(convert_to_wav, file_path, wav_path)
        text = await asyncio.to_thread(transcribe_audio, wav_path)
    except sr.UnknownValueError:
        # Could not understand audio
        return
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(wav_path): os.remove(wav_path)

    text = text.lower().strip()

    video = False
    query = ""

    # Matching keywords
    if text.startswith("vplay "):
        video = True
        query = text[6:].strip()
    elif text.startswith("play "):
        query = text[5:].strip()
    elif text.startswith("v play "):
        video = True
        query = text[7:].strip()
    elif text.startswith("v-play "):
        video = True
        query = text[7:].strip()
    else:
        return

    if not query:
        return

    # Valid play request
    sent = await m.reply_text(m.lang["voice_searching"])
    setattr(sent, "lang", m.lang)

    # Permission/Assistant checks
    play_mode = await db.get_play_mode(chat_id)
    if play_mode:
        adminlist = await db.get_admins(chat_id)
        if (
            m.from_user.id not in adminlist
            and not await db.is_auth(chat_id, m.from_user.id)
            and m.from_user.id not in app.sudoers
        ):
            return await sent.edit_text(m.lang["play_admin"])

    if not await check_assistant_and_join(chat_id, sent):
        return

    # Transcription feedback
    await sent.edit_text(m.lang["voice_transcribed"].format(text))
    await asyncio.sleep(1)
    await sent.edit_text(m.lang["play_searching"])

    # Search
    track = await yt.search(query, sent.id, video=video)
    if not track:
        return await sent.edit_text(
            m.lang["play_not_found"].format(config.SUPPORT_CHAT)
        )

    # Play
    await stream_media(chat_id, sent, track, m.from_user.mention, video)
