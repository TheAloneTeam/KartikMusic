#
# Copyright (C) 2025-present by TheAloneTeam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/KartikMusic > project,
# and is released under the "MIT License".
# Please see < https://github.com/TheAloneTeam/KartikMusic/blob/master/LICENSE >
#
# All rights reserved.
#

from collections import defaultdict, deque
from typing import Union

from ._dataclass import Media, Track

MediaItem = Union[Media, Track]


class Queue:
    def __init__(self):
        self.queues: dict[int, deque[MediaItem]] = defaultdict(deque)
        self.autoplay_history: dict[int, list[str]] = defaultdict(list)

    def get_autoplay_history(self, chat_id: int) -> list[str]:
        """Return a copy of the autoplay history for the chat."""
        return list(self.autoplay_history[chat_id])

    def get_last_autoplay_track_id(self, chat_id: int) -> str:
        """Return the ID or URL of the most recently played/queued track."""
        history = self.autoplay_history.get(chat_id)
        if not history:
            return ""
        return history[-1]

    def add_autoplay_history(self, chat_id: int, *track_ids: str) -> None:
        """Add track IDs to the autoplay history for the chat without duplicates."""
        history = self.autoplay_history[chat_id]
        for tid in track_ids:
            if tid and tid not in history:
                history.append(tid)
        if len(history) > 100:
            self.autoplay_history[chat_id] = history[-100:]

    def clear_autoplay_history(self, chat_id: int) -> None:
        """Clear the autoplay history for the chat."""
        if chat_id in self.autoplay_history:
            self.autoplay_history[chat_id].clear()

    def add(self, chat_id: int, item: MediaItem) -> int:
        """Add an item to the queue and return its position (1-based)."""
        self.queues[chat_id].append(item)
        if getattr(item, "user", None) != "Autoplay":
            self.clear_autoplay_history(chat_id)
        return len(self.queues[chat_id]) - 1

    def check_item(self, chat_id: int, item_id: str) -> tuple[int, MediaItem | None]:
        """Check if an item with the given ID exists in the queue."""
        pos, track = next(
            (
                (i, track)
                for i, track in enumerate(list(self.queues[chat_id]))
                if track.id == item_id
            ),
            (-1, None),
        )
        return pos, track

    def force_add(
        self, chat_id: int, item: MediaItem, remove: int | bool = False
    ) -> None:
        """Replace the currently playing item with a new one."""
        self.remove_current(chat_id)
        self.queues[chat_id].appendleft(item)
        if remove:
            self.queues[chat_id].rotate(-remove)
            self.queues[chat_id].popleft()
            self.queues[chat_id].rotate(remove)

    def get_current(self, chat_id: int) -> MediaItem | None:
        """Return the currently playing item (first in queue), if any."""
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_next(self, chat_id: int, check: bool = False) -> MediaItem | None:
        """Remove current item and return the next one, or None if empty."""
        if not self.queues[chat_id]:
            return None
        if check:
            return self.queues[chat_id][1] if len(self.queues[chat_id]) > 1 else None

        removed = self.queues[chat_id].popleft()
        if removed:
            tid = getattr(removed, "id", None) or getattr(removed, "url", None)
            if tid and tid not in self.autoplay_history[chat_id]:
                self.autoplay_history[chat_id].append(tid)
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_queue(self, chat_id: int) -> list[MediaItem]:
        """Return the full queue including the currently playing item."""
        return list(self.queues[chat_id])

    def remove_current(self, chat_id: int) -> MediaItem | None:
        """Remove the currently playing item only (if exists)."""
        if self.queues[chat_id]:
            removed = self.queues[chat_id].popleft()
            if removed:
                tid = getattr(removed, "id", None) or getattr(removed, "url", None)
                if tid and tid not in self.autoplay_history[chat_id]:
                    self.autoplay_history[chat_id].append(tid)
            return removed
        return None

    def clear(self, chat_id: int) -> None:
        """Clear the entire queue."""
        self.queues[chat_id].clear()
        self.clear_autoplay_history(chat_id)
