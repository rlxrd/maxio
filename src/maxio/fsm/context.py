from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from maxio.fsm.states import State
from maxio.fsm.storage import BaseStorage, StorageKey

current_fsm_context: ContextVar[FSMContext | None] = ContextVar(
    "current_fsm_context", default=None
)


class FSMContext:
    """FSM context for a single user/chat slot. Injected into handlers by type annotation."""

    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self._storage = storage
        self._key = key

    async def get_state(self) -> str | None:
        """Return the current FSM state key, or ``None`` if not set."""
        return await self._storage.get_state(self._key)

    async def set_state(self, state: State | str | None) -> None:
        """Set the FSM state. Pass ``None`` to clear it."""
        key = state.key if isinstance(state, State) else state
        await self._storage.set_state(self._key, key)

    async def get_data(self) -> dict[str, Any]:
        """Return a copy of the stored FSM data dict."""
        return await self._storage.get_data(self._key)

    async def set_data(self, data: dict[str, Any]) -> None:
        """Replace the FSM data dict entirely."""
        await self._storage.set_data(self._key, data)

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        """Merge keyword arguments into the FSM data dict and return the result."""
        data = await self._storage.get_data(self._key)
        data.update(kwargs)
        await self._storage.set_data(self._key, data)
        return data

    async def clear(self) -> None:
        """Reset both state and data."""
        await self._storage.clear(self._key)
