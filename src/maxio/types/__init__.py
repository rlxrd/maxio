from __future__ import annotations

from maxio.types.attachment import (
    Attachment,
    AudioAttachmentPayload,
    FileAttachmentPayload,
    PhotoAttachmentPayload,
    VideoAttachmentPayload,
)
from maxio.types.callback import Callback
from maxio.types.chat import Chat, ChatList, Image
from maxio.types.member import ChatMember, ChatMemberList
from maxio.types.message import (
    LinkedMessage,
    Message,
    MessageBody,
    MessageList,
    NewMessageLink,
    Recipient,
    SendMessageResult,
)
from maxio.types.subscription import Subscription, SubscriptionList
from maxio.types.update import Update, UpdateList
from maxio.types.user import BotInfo, User
from maxio.types.video import VideoInfo

__all__ = [
    "Attachment",
    "PhotoAttachmentPayload",
    "VideoAttachmentPayload",
    "AudioAttachmentPayload",
    "FileAttachmentPayload",
    "BotInfo",
    "Callback",
    "Chat",
    "ChatList",
    "ChatMember",
    "ChatMemberList",
    "Image",
    "LinkedMessage",
    "Message",
    "MessageBody",
    "MessageList",
    "NewMessageLink",
    "Recipient",
    "SendMessageResult",
    "Subscription",
    "SubscriptionList",
    "Update",
    "UpdateList",
    "User",
    "VideoInfo",
]
