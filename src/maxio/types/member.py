from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from maxio.enums import ChatMemberRole


class ChatMember(BaseModel):
    """A user's membership record inside a chat."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    name: str | None = None
    is_bot: bool = False
    role: ChatMemberRole | str | None = None
    last_activity_time: int | None = None
    join_time: int | None = None
    invited_by_user_id: int | None = None
    permissions: list[str] | None = None


class ChatMemberList(BaseModel):
    """Paginated response from ``GET /chats/{chatId}/members``."""

    model_config = ConfigDict(extra="allow")

    members: list[ChatMember] = []
    marker: int | None = None
