from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from maxio.fsm.states import State
from maxio.fsm.storage import BaseStorage, StorageKey

current_fsm_context: ContextVar[FSMContext | None] = ContextVar(
    "current_fsm_context", default=None
)


class FSMContext:
    """Контекст FSM для одного пользователя/чата. Инжектируется в хэндлер по типу."""

    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self._storage = storage
        self._key = key

    async def get_state(self) -> str | None:
        return await self._storage.get_state(self._key)

    async def set_state(self, state: State | str | None) -> None:
        key = state.key if isinstance(state, State) else state
        await self._storage.set_state(self._key, key)

    async def get_data(self) -> dict[str, Any]:
        return await self._storage.get_data(self._key)

    async def set_data(self, data: dict[str, Any]) -> None:
        await self._storage.set_data(self._key, data)

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        data = await self._storage.get_data(self._key)
        data.update(kwargs)
        await self._storage.set_data(self._key, data)
        return data

    async def clear(self) -> None:
        """Сбросить состояние и данные."""
        await self._storage.clear(self._key)
