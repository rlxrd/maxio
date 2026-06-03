from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from maxio.enums import ChatStatus, ChatType
from maxio.types.user import User


class Image(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: str | None = None


class Chat(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    chat_id: int
    type: ChatType
    status: ChatStatus | None = None
    title: str | None = None
    icon: Image | None = None
    last_event_time: int | None = None
    participants_count: int | None = None
    owner_id: int | None = None
    is_public: bool = False
    link: str | None = None
    description: str | None = None
    dialog_with_user: User | None = None
    messages_count: int | None = None


class ChatList(BaseModel):
    model_config = ConfigDict(extra="allow")

    chats: list[Chat] = []
    marker: int | None = None
