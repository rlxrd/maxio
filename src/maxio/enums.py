from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String-based enum: values compare and serialize as plain strings."""

    def __str__(self) -> str:
        return str(self.value)


class UpdateType(StrEnum):
    """All event types delivered by the MAX Bot API long-polling endpoint."""

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
    """Type of a MAX chat."""

    DIALOG = "dialog"
    CHAT = "chat"
    CHANNEL = "channel"


class ChatStatus(StrEnum):
    """Membership status of the bot in a chat."""

    ACTIVE = "active"
    REMOVED = "removed"
    LEFT = "left"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class TextFormat(StrEnum):
    """Markup format for outgoing message text."""

    MARKDOWN = "markdown"
    HTML = "html"


class ButtonType(StrEnum):
    """Inline button interaction type."""

    CALLBACK = "callback"
    LINK = "link"
    REQUEST_CONTACT = "request_contact"
    REQUEST_GEO_LOCATION = "request_geo_location"
    CHAT = "chat"
    MESSAGE = "message"


class Intent(StrEnum):
    """Visual intent (color) of a callback button."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    DEFAULT = "default"


class MessageLinkType(StrEnum):
    """Relationship between a linked message and the current one."""

    FORWARD = "forward"
    REPLY = "reply"


class UploadType(StrEnum):
    """Media type for the file upload endpoint."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class ChatAction(StrEnum):
    """Typing/activity indicator action sent via ``POST /chats/{chatId}/actions``."""

    TYPING_ON = "typing_on"
    TYPING_OFF = "typing_off"
    SENDING_PHOTO = "sending_photo"
    SENDING_VIDEO = "sending_video"
    SENDING_AUDIO = "sending_audio"
    SENDING_FILE = "sending_file"
    MARK_SEEN = "mark_seen"


class ChatMemberRole(StrEnum):
    """Role of a member inside a chat."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
