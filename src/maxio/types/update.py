from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from maxio.types.callback import Callback
from maxio.types.chat import Chat
from maxio.types.message import Message
from maxio.types.user import User


class Update(BaseModel):
    """Unified update model for all MAX event types.

    The specific event type is determined by ``update_type``; related fields are
    populated while the rest remain ``None``. This intentionally flat model avoids
    11 subclasses — the dispatcher routes purely by ``update_type``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    update_type: str
    timestamp: int | None = None

    message: Message | None = None
    callback: Callback | None = None
    user_locale: str | None = None

    user: User | None = None
    chat_id: int | None = None
    user_id: int | None = None
    message_id: str | None = None
    chat: Chat | None = None
    title: str | None = None
    payload: str | None = None
    start_payload: str | None = None
    is_channel: bool | None = None
    inviter_id: int | None = None
    admin_id: int | None = None


class UpdateList(BaseModel):
    """Response wrapper for the long-polling ``/updates`` endpoint."""

    updates: list[Update]
    marker: int | None = None
