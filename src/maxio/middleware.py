from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from maxio.types.update import Update

Handler = Callable[..., Awaitable[Any]]

CallNextOuter = Callable[[], Awaitable[bool]]
OuterMiddlewareFn = Callable[[Update, CallNextOuter], Awaitable[bool]]

CallNextInner = Callable[[], Awaitable[None]]
InnerMiddlewareFn = Callable[[Handler, dict[str, Any], CallNextInner], Awaitable[None]]


@dataclass(slots=True)
class _OuterReg:
    update_types: frozenset[str]
    fn: OuterMiddlewareFn


@dataclass(slots=True)
class _InnerReg:
    update_types: frozenset[str]
    fn: InnerMiddlewareFn
