# Copyright (C) 2026 by Kartike Mishra, < https://github.com/meowkingm >.
# Consolidated AloneAPI SDK client module.
# Re-exports AllSupport, AloneAPI, UniversalAPI, and default instance from all_support.

from all_support import (
    AllSupport,
    AloneAPI,
    UniversalAPI,
    all_support,
    API_URL,
    API_KEY,
    DEFAULT_API_URL,
    DEFAULT_API_KEY,
)

__all__ = [
    "AllSupport",
    "AloneAPI",
    "UniversalAPI",
    "all_support",
    "API_URL",
    "API_KEY",
    "DEFAULT_API_URL",
    "DEFAULT_API_KEY",
]
