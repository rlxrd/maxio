from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from maxio.enums import TextFormat
from maxio.types.message import Message
from maxio.types.user import User

if TYPE_CHECKING:
    from maxio.keyboards import InlineKeyboard


class Callback(BaseModel):
    """Сырой объект callback из апдейта (без исходного сообщения)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    callback_id: str
    timestamp: int | None = None
    payload: str | None = None
    user: User | None = None


class CallbackQuery(BaseModel):
    """Нажатие inline-кнопки. Объединяет данные `Callback` и исходное сообщение."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    callback_id: str
    timestamp: int | None = None
    payload: str | None = None
    user: User | None = None
    message: Message | None = None

    @property
    def from_user(self) -> User | None:
        return self.user

    async def answer(
        self,
        notification: str | None = None,
        *,
        text: str | None = None,
        keyboard: InlineKeyboard | None = None,
        attachments: list[Any] | None = None,
        format: TextFormat | str | None = None,
    ) -> bool:
        """Ответить на нажатие: показать всплывающее уведомление и/или изменить сообщение."""
        from maxio._runtime import get_current_bot

        return await get_current_bot().answer_callback(
            self.callback_id,
            notification=notification,
            text=text,
            keyboard=keyboard,
            attachments=attachments,
            format=format,
        )
