from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from maxio.types.callback import Callback
from maxio.types.chat import Chat
from maxio.types.message import Message
from maxio.types.user import User


class Update(BaseModel):
    """Единая модель апдейта для всех типов событий MAX.

    Конкретный тип определяется полем `update_type`; относящиеся к нему поля
    заполняются, остальные остаются `None`. Это сознательно плоская модель
    (вместо 11 подклассов) — для v0.1 этого достаточно, а диспетчер маршрутизирует
    по `update_type`.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    update_type: str
    timestamp: int | None = None

    # message_created / message_edited / message_callback
    message: Message | None = None
    # message_callback
    callback: Callback | None = None
    user_locale: str | None = None

    # события с участником/ботом/чатом
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
    updates: list[Update]
    marker: int | None = None
