from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """str-based enum: значение сравнивается и сериализуется как обычная строка."""

    def __str__(self) -> str:
        return str(self.value)


class UpdateType(StrEnum):
    MESSAGE_CREATED = "message_created"
    MESSAGE_CALLBACK = "message_callback"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_REMOVED = "message_removed"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    BOT_STARTED = "bot_started"
    CHAT_TITLE_CHANGED = "chat_title_changed"
    MESSAGE_CHAT_CREATED = "message_chat_created"


class ChatType(StrEnum):
    DIALOG = "dialog"
    CHAT = "chat"
    CHANNEL = "channel"


class ChatStatus(StrEnum):
    ACTIVE = "active"
    REMOVED = "removed"
    LEFT = "left"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class TextFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"


class ButtonType(StrEnum):
    CALLBACK = "callback"
    LINK = "link"
    REQUEST_CONTACT = "request_contact"
    REQUEST_GEO_LOCATION = "request_geo_location"
    CHAT = "chat"
    MESSAGE = "message"


class Intent(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    DEFAULT = "default"


class MessageLinkType(StrEnum):
    FORWARD = "forward"
    REPLY = "reply"


class UploadType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
