from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from maxio.enums import ChatType, MessageLinkType, TextFormat
from maxio.types.attachment import (
    Attachment,
    AudioAttachmentPayload,
    FileAttachmentPayload,
    PhotoAttachmentPayload,
    VideoAttachmentPayload,
)
from maxio.types.user import User

if TYPE_CHECKING:
    from maxio.keyboards import InlineKeyboard


class Recipient(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    chat_id: int | None = None
    chat_type: ChatType | None = None
    user_id: int | None = None


class MessageBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    mid: str
    seq: int | None = None
    text: str | None = None
    attachments: list[Attachment] | None = None


class LinkedMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: MessageLinkType
    sender: User | None = None
    chat_id: int | None = None
    message: MessageBody | None = None


class NewMessageLink(BaseModel):
    type: MessageLinkType
    mid: str


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    recipient: Recipient
    timestamp: int
    sender: User | None = None
    link: LinkedMessage | None = None
    body: MessageBody | None = None
    url: str | None = None

    @property
    def text(self) -> str | None:
        return self.body.text if self.body else None

    @property
    def mid(self) -> str | None:
        return self.body.mid if self.body else None

    @property
    def attachments(self) -> list[Attachment]:
        return self.body.attachments or [] if self.body else []

    @property
    def photos(self) -> list[PhotoAttachmentPayload]:
        return [p for a in self.attachments if (p := a.as_image()) is not None]

    @property
    def videos(self) -> list[VideoAttachmentPayload]:
        return [p for a in self.attachments if (p := a.as_video()) is not None]

    @property
    def audio(self) -> list[AudioAttachmentPayload]:
        return [p for a in self.attachments if (p := a.as_audio()) is not None]

    @property
    def files(self) -> list[FileAttachmentPayload]:
        return [p for a in self.attachments if (p := a.as_file()) is not None]

    @property
    def chat_id(self) -> int | None:
        return self.recipient.chat_id

    @property
    def from_user(self) -> User | None:
        return self.sender

    async def answer(
        self,
        text: str | None = None,
        *,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        notify: bool = True,
        format: TextFormat | str | None = None,
    ) -> Message:
        """Отправить новое сообщение в тот же чат/диалог."""
        from maxio._runtime import get_current_bot

        return await get_current_bot().send_message(
            text,
            chat_id=self.recipient.chat_id,
            user_id=None if self.recipient.chat_id else self.recipient.user_id,
            attachments=attachments,
            keyboard=keyboard,
            notify=notify,
            format=format,
        )

    async def reply(
        self,
        text: str | None = None,
        *,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        notify: bool = True,
        format: TextFormat | str | None = None,
    ) -> Message:
        """Ответить на это сообщение (с цитированием)."""
        from maxio._runtime import get_current_bot

        if self.mid is None:
            raise ValueError("Невозможно ответить на сообщение без mid")
        return await get_current_bot().send_message(
            text,
            chat_id=self.recipient.chat_id,
            user_id=None if self.recipient.chat_id else self.recipient.user_id,
            attachments=attachments,
            keyboard=keyboard,
            link=NewMessageLink(type=MessageLinkType.REPLY, mid=self.mid),
            notify=notify,
            format=format,
        )


class SendMessageResult(BaseModel):
    message: Message


class MessageList(BaseModel):
    messages: list[Message]
