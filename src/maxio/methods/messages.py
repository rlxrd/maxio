from __future__ import annotations

from typing import Any

from maxio.enums import TextFormat
from maxio.keyboards import InlineKeyboard
from maxio.methods._helpers import message_body, normalize_attachments
from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.message import Message, MessageList, NewMessageLink, SendMessageResult


class SendMessage(MaxMethod[Message]):
    """Send a message to a chat or user."""

    text: str | None = None
    chat_id: int | None = None
    user_id: int | None = None
    attachments: list[Any] | None = None
    keyboard: InlineKeyboard | None = None
    link: NewMessageLink | None = None
    notify: bool = True
    format: TextFormat | str | None = None
    disable_link_preview: bool | None = None

    def build_request(self) -> MaxRequest:
        if self.chat_id is None and self.user_id is None:
            raise ValueError("chat_id or user_id is required")
        return MaxRequest(
            http_method="POST",
            api_path="/messages",
            params={
                "chat_id": self.chat_id,
                "user_id": self.user_id,
                "disable_link_preview": self.disable_link_preview,
            },
            json_body=message_body(
                self.text,
                normalize_attachments(self.attachments, self.keyboard),
                self.link,
                self.notify,
                self.format,
            ),
        )

    def parse_response(self, data: Any) -> Message:
        return SendMessageResult.model_validate(data).message


class EditMessage(MaxMethod[bool]):
    """Edit an existing message."""

    message_id: str
    text: str | None = None
    attachments: list[Any] | None = None
    keyboard: InlineKeyboard | None = None
    link: NewMessageLink | None = None
    notify: bool = True
    format: TextFormat | str | None = None

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="PUT",
            api_path="/messages",
            params={"message_id": self.message_id},
            json_body=message_body(
                self.text,
                normalize_attachments(self.attachments, self.keyboard),
                self.link,
                self.notify,
                self.format,
            ),
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class DeleteMessage(MaxMethod[bool]):
    """Delete a message by its ID."""

    message_id: str

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="DELETE",
            api_path="/messages",
            params={"message_id": self.message_id},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class GetMessage(MaxMethod[Message]):
    """Fetch a single message by its ID."""

    message_id: str

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/messages/{self.message_id}")

    def parse_response(self, data: Any) -> Message:
        return Message.model_validate(data)


class GetMessages(MaxMethod[list[Message]]):
    """Fetch a list of messages from a chat."""

    chat_id: int | None = None
    message_ids: list[str] | None = None
    from_time: int | None = None
    to_time: int | None = None
    count: int = 50

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="GET",
            api_path="/messages",
            params={
                "chat_id": self.chat_id,
                "message_ids": ",".join(self.message_ids) if self.message_ids else None,
                "from": self.from_time,
                "to": self.to_time,
                "count": self.count,
            },
        )

    def parse_response(self, data: Any) -> list[Message]:
        return MessageList.model_validate(data).messages
