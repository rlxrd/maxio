from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maxio.bot import Bot

# Текущий Bot активного апдейта. Диспетчер выставляет его перед вызовом хэндлера,
# чтобы методы-сахар (Message.answer, Callback.answer) работали без явной передачи бота.
current_bot: ContextVar[Bot] = ContextVar("current_bot")


def get_current_bot() -> Bot:
    try:
        return current_bot.get()
    except LookupError as exc:  # pragma: no cover - защитная ветка
        raise RuntimeError(
            "Нет активного Bot в контексте. Методы answer()/reply() доступны "
            "только внутри обработчика апдейта."
        ) from exc
