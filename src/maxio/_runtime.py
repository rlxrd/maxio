from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maxio.bot import Bot

current_bot: ContextVar[Bot] = ContextVar("current_bot")


def get_current_bot() -> Bot:
    """Return the Bot instance active in the current handler context.

    Raises :exc:`RuntimeError` if called outside an update handler.
    """
    try:
        return current_bot.get()
    except LookupError as exc:  # pragma: no cover
        raise RuntimeError(
            "No active Bot in context. answer()/reply() methods are only "
            "available inside an update handler."
        ) from exc
