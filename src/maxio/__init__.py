from __future__ import annotations

from maxio import media
from maxio.app import MaxBot
from maxio.bot import Bot
from maxio.enums import (
    ButtonType,
    ChatStatus,
    ChatType,
    Intent,
    MessageLinkType,
    TextFormat,
    UpdateType,
    UploadType,
)
from maxio.exceptions import MaxApiError, MaxError
from maxio.filters import CallbackPayload, Command, Filter, HasMedia
from maxio.fsm import (
    BaseStorage,
    FSMContext,
    MemoryStorage,
    State,
    StateFilter,
    StatesGroup,
    StorageKey,
)
from maxio.keyboards import Button, InlineKeyboard
from maxio.magic import F, MagicFilter
from maxio.middleware import (
    CallNextInner,
    CallNextOuter,
    HandlerKwargs,
    InnerMiddlewareFn,
    OuterMiddlewareFn,
)
from maxio.router import Router
from maxio.types import (
    Attachment,
    BotInfo,
    Callback,
    Chat,
    Message,
    Update,
    UpdateList,
    User,
)

__version__ = "0.4.0"

__all__ = [
    "MaxBot",
    "Router",
    "FSMContext",
    "StateFilter",
    "State",
    "StatesGroup",
    "BaseStorage",
    "MemoryStorage",
    "StorageKey",
    "CallNextOuter",
    "CallNextInner",
    "HandlerKwargs",
    "OuterMiddlewareFn",
    "InnerMiddlewareFn",
    "Bot",
    "Button",
    "InlineKeyboard",
    "Command",
    "CallbackPayload",
    "Command",
    "Filter",
    "HasMedia",
    "F",
    "MagicFilter",
    "media",
    "MaxError",
    "MaxApiError",
    "Attachment",
    "BotInfo",
    "Callback",
    "Chat",
    "Message",
    "Update",
    "UpdateList",
    "User",
    "ButtonType",
    "ChatStatus",
    "ChatType",
    "Intent",
    "MessageLinkType",
    "TextFormat",
    "UpdateType",
    "UploadType",
]
