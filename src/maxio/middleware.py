from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

Handler = Callable[..., Awaitable[Any]]


class CallNextOuter:
    """Вызов следующего шага в outer middleware."""

    __slots__ = ("_fn",)

    def __init__(self, fn: Callable[[], Awaitable[bool]]) -> None:
        self._fn = fn

    async def __call__(self) -> bool:
        return await self._fn()


class CallNextInner:
    """Вызов следующего шага в inner middleware."""

    __slots__ = ("_fn",)

    def __init__(self, fn: Callable[[], Awaitable[None]]) -> None:
        self._fn = fn

    async def __call__(self) -> None:
        await self._fn()


class HandlerKwargs(dict):  # type: ignore[type-arg]
    """Разрешённые аргументы хэндлера — инжектируются в inner middleware по типу."""


OuterMiddlewareFn = Callable[..., Awaitable[bool]]
InnerMiddlewareFn = Callable[..., Awaitable[None]]


@dataclass(slots=True)
class _OuterReg:
    update_types: frozenset[str]
    fn: OuterMiddlewareFn


@dataclass(slots=True)
class _InnerReg:
    update_types: frozenset[str]
    fn: InnerMiddlewareFn
