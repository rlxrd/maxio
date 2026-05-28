from __future__ import annotations

from typing import Any, NamedTuple, Protocol, runtime_checkable


class StorageKey(NamedTuple):
    user_id: int
    chat_id: int | None


@runtime_checkable
class BaseStorage(Protocol):
    async def get_state(self, key: StorageKey) -> str | None: ...
    async def set_state(self, key: StorageKey, state: str | None) -> None: ...
    async def get_data(self, key: StorageKey) -> dict[str, Any]: ...
    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None: ...
    async def clear(self, key: StorageKey) -> None: ...


class MemoryStorage:
    """In-memory хранилище. Состояние теряется при рестарте бота."""

    def __init__(self) -> None:
        self._states: dict[StorageKey, str] = {}
        self._data: dict[StorageKey, dict[str, Any]] = {}

    async def get_state(self, key: StorageKey) -> str | None:
        return self._states.get(key)

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        if state is None:
            self._states.pop(key, None)
        else:
            self._states[key] = state

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        return dict(self._data.get(key, {}))

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        if data:
            self._data[key] = dict(data)
        else:
            self._data.pop(key, None)

    async def clear(self, key: StorageKey) -> None:
        self._states.pop(key, None)
        self._data.pop(key, None)
