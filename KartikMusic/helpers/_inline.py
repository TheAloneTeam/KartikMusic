# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of KartikMusic


import random
from pyrogram import enums, types

from KartikMusic import app, config, lang
from KartikMusic.core.lang import lang_codes


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup

    def ikb(self, text: str, **kwargs) -> types.InlineKeyboardButton:
        styles = [
            enums.ButtonStyle.DANGER,
            enums.ButtonStyle.PRIMARY,
            enums.ButtonStyle.SUCCESS,
            enums.ButtonStyle.DEFAULT,
        ]
        return types.InlineKeyboardButton(
            text=text, style=random.choice(styles), **kwargs
        )

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
        more: bool = False,
        autoplay: bool = None,
        thumb: bool = None,
        lang: dict = None,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(
                [self.ikb(text=timer, callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            if more:
                _on = "Enabled ✅"
                _off = "Disabled ❌"
                keyboard.append(
                    [
                        self.ikb(text="Autoplay", callback_data="help autoplay"),
                        self.ikb(text=_on if autoplay else _off, callback_data=f"controls cautoplay {chat_id}"),
                    ]
                )
                keyboard.append(
                    [
                        self.ikb(text="Thumbnail", callback_data="help thumb"),
                        self.ikb(text=_on if thumb else _off, callback_data=f"controls cthumb {chat_id}"),
                    ]
                )
                keyboard.append(
                    [self.ikb(text="Back ⬅️", callback_data=f"controls back {chat_id}")]
                )
            else:
                keyboard.append(
                    [
                        self.ikb(text="▷", callback_data=f"controls resume {chat_id}"),
                        self.ikb(text="II", callback_data=f"controls pause {chat_id}"),
                        self.ikb(text="⥁", callback_data=f"controls replay {chat_id}"),
                        self.ikb(text="‣‣I", callback_data=f"controls skip {chat_id}"),
                        self.ikb(text="▢", callback_data=f"controls stop {chat_id}"),
                    ]
                )
                keyboard.append(
                    [
                        self.ikb(text="-20s", callback_data=f"controls seek {chat_id} -20"),
                        self.ikb(text="More", callback_data=f"controls more {chat_id}"),
                        self.ikb(text="+20s", callback_data=f"controls seek {chat_id} 20"),
                    ]
                )
                keyboard.append(
                    [
                        self.ikb(text=lang["add_mee"] if lang else "Add Me", url=f"https://t.me/{app.username}?startgroup=true"),
                        self.ikb(text="Close ✘", callback_data=f"controls close {chat_id}"),
                    ]
                )
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text=_lang["back"], callback_data="help back"),
                    self.ikb(text=_lang["cancel"], callback_data="help close"),
                ]
            ]
        else:
            rows = [
                [
                    self.ikb(
                        text=_lang["add_me"],
                        url=f"https://t.me/{app.username}?startgroup=true",
                    )
                ]
            ]
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo", "thumb", "vclog", "autoplay"]
            buttons = [
                self.ikb(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
                for i, cb in enumerate(cbs)
            ]
            rows += [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
            rows.append(
                [
                    self.ikb(text=_lang["back"], callback_data="help home"),
                    self.ikb(text=_lang["cancel"], callback_data="help close"),
                ]
            )

        return self.ikm(rows)

    def song_markup(self, vid_id: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="Audio 🎵", callback_data=f"song_download audio {vid_id}"),
                    self.ikb(text="Video 🎬", callback_data=f"song_download video {vid_id}"),
                ],
                [
                    self.ikb(text="Close ✘", callback_data="help close"),
                ],
            ]
        )

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}"
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self,
        lang: dict,
        admin_only: bool,
        cmd_delete: bool,
        autoplay: bool,
        vclogger: bool,
        thumbnail: bool,
        language: str,
        chat_id: int,
    ) -> types.InlineKeyboardMarkup:
        _on = "Enabled ✅"
        _off = "Disabled ❌"
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=_on if admin_only else _off, callback_data="settings play"
                    ),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=_on if cmd_delete else _off,
                        callback_data="settings delete",
                    ),
                ],
                [
                    self.ikb(
                        text=lang["autoplay"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=_on if autoplay else _off, callback_data="settings autoplay"
                    ),
                ],
                [
                    self.ikb(
                        text=lang["vclogger"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=_on if vclogger else _off, callback_data="settings vclog"
                    ),
                ],
                [
                    self.ikb(
                        text=lang["thumbnail"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=_on if thumbnail else _off, callback_data="settings thumb"
                    ),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
            [self.ikb(text=lang["help"], callback_data="help")],
            [
                self.ikb(text=lang["support"], url=config.SUPPORT_CHAT),
                self.ikb(text=lang["channel"], url=config.SUPPORT_CHANNEL),
            ],
        ]
        if private:
            rows += [
                [
                    self.ikb(
                        text="Owner",
                        user_id=config.OWNER_ID,
                    )
                ]
            ]
        else:
            rows += [[self.ikb(text=lang["language"], callback_data="language")]]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
