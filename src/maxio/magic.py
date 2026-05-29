from __future__ import annotations

from typing import Any

from maxio.types.update import Update


def _has_attachment(update: Update, media_type: str) -> bool:
    if update.message is None:
        return False
    return any(a.type == media_type for a in update.message.attachments)


_SHORTCUTS: dict[str, Any] = {
    "text":         lambda u: u.message.text if u.message else None,
    "data":         lambda u: u.callback.payload if u.callback else None,
    "payload":      lambda u: u.payload,
    "start_payload": lambda u: u.start_payload,
    "photo":        lambda u: _has_attachment(u, "image"),
    "image":        lambda u: _has_attachment(u, "image"),
    "video":        lambda u: _has_attachment(u, "video"),
    "audio":        lambda u: _has_attachment(u, "audio"),
    "file":         lambda u: _has_attachment(u, "file"),
    "document":     lambda u: _has_attachment(u, "file"),
}


def _resolve(update: Update, path: tuple[str, ...]) -> Any:
    if not path:
        return update
    obj: Any = _SHORTCUTS[path[0]](update) if path[0] in _SHORTCUTS else update
    start = 1 if path[0] in _SHORTCUTS else 0
    for attr in path[start:]:
        if obj is None:
            return None
        obj = getattr(obj, attr, None)
    return obj


class _BaseFilter:
    async def check(self, update: Update) -> bool:
        raise NotImplementedError

    def __and__(self, other: _BaseFilter) -> _AndFilter:
        return _AndFilter(self, other)

    def __or__(self, other: _BaseFilter) -> _OrFilter:
        return _OrFilter(self, other)

    def __invert__(self) -> _NotFilter:
        return _NotFilter(self)


class _OpFilter(_BaseFilter):
    __slots__ = ("_path", "_op", "_value")

    def __init__(self, path: tuple[str, ...], op: str, value: Any) -> None:
        self._path = path
        self._op = op
        self._value = value

    async def check(self, update: Update) -> bool:
        v = _resolve(update, self._path)
        if self._op == "==":
            return bool(v == self._value)
        if self._op == "!=":
            return bool(v != self._value)
        if self._op == "in":
            return v in self._value
        if self._op == "not_in":
            return v not in self._value
        if self._op == "startswith":
            return isinstance(v, str) and v.startswith(self._value)
        if self._op == "endswith":
            return isinstance(v, str) and v.endswith(self._value)
        if self._op == "contains":
            return v is not None and self._value in v
        return False


class _AndFilter(_BaseFilter):
    __slots__ = ("_a", "_b")

    def __init__(self, a: _BaseFilter, b: _BaseFilter) -> None:
        self._a, self._b = a, b

    async def check(self, update: Update) -> bool:
        return await self._a.check(update) and await self._b.check(update)


class _OrFilter(_BaseFilter):
    __slots__ = ("_a", "_b")

    def __init__(self, a: _BaseFilter, b: _BaseFilter) -> None:
        self._a, self._b = a, b

    async def check(self, update: Update) -> bool:
        return await self._a.check(update) or await self._b.check(update)


class _NotFilter(_BaseFilter):
    __slots__ = ("_f",)

    def __init__(self, f: _BaseFilter) -> None:
        self._f = f

    async def check(self, update: Update) -> bool:
        return not await self._f.check(update)


class MagicFilter(_BaseFilter):
    """Ленивый фильтр-выражение. Используй корневой объект F."""

    __slots__ = ("_path",)

    def __init__(self, path: tuple[str, ...] = ()) -> None:
        self._path = path

    def __getattr__(self, name: str) -> MagicFilter:
        return MagicFilter(self._path + (name,))

    def __eq__(self, other: object) -> _OpFilter:  # type: ignore[override]
        return _OpFilter(self._path, "==", other)

    def __ne__(self, other: object) -> _OpFilter:  # type: ignore[override]
        return _OpFilter(self._path, "!=", other)

    __hash__ = None  # type: ignore[assignment]

    def in_(self, *values: Any) -> _OpFilter:
        return _OpFilter(self._path, "in", values)

    def not_in_(self, *values: Any) -> _OpFilter:
        return _OpFilter(self._path, "not_in", values)

    def startswith(self, prefix: str) -> _OpFilter:
        return _OpFilter(self._path, "startswith", prefix)

    def endswith(self, suffix: str) -> _OpFilter:
        return _OpFilter(self._path, "endswith", suffix)

    def contains(self, substr: str) -> _OpFilter:
        return _OpFilter(self._path, "contains", substr)

    async def check(self, update: Update) -> bool:
        return bool(_resolve(update, self._path))


F = MagicFilter()
