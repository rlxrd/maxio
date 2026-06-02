from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from maxio.enums import UpdateType
from maxio.filters import Filter, FilterFunc
from maxio.middleware import (
    Handler,
    InnerMiddlewareFn,
    OuterMiddlewareFn,
    _InnerReg,
    _OuterReg,
)


@dataclass(slots=True)
class _Registration:
    update_types: frozenset[str]
    filters: tuple[Filter | FilterFunc, ...]
    fn: Handler


class Router:
    """Registry of handlers that can be mounted onto ``MaxBot`` via ``include_routers``.

    Example:
        ```python
        from maxio import Router, Message

        router = Router()

        @router.message()
        async def echo(message: Message) -> None:
            await message.answer(message.text)
        ```
    """

    def __init__(self) -> None:
        self._handlers: list[_Registration] = []
        self._outer: list[_OuterReg] = []
        self._inner: list[_InnerReg] = []

    def _register(
        self,
        update_types: tuple[str, ...],
        filters: tuple[Filter | FilterFunc, ...],
    ) -> Callable[[Handler], Handler]:
        def decorator(fn: Handler) -> Handler:
            self._handlers.append(
                _Registration(frozenset(str(t) for t in update_types), filters, fn)
            )
            return fn

        return decorator

    def message(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``message_created`` events."""
        return self._register((UpdateType.MESSAGE_CREATED.value,), filters)

    def message_edited(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``message_edited`` events."""
        return self._register((UpdateType.MESSAGE_EDITED.value,), filters)

    def callback(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``message_callback`` events (inline button presses)."""
        return self._register((UpdateType.MESSAGE_CALLBACK.value,), filters)

    def bot_started(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``bot_started`` events."""
        return self._register((UpdateType.BOT_STARTED.value,), filters)

    def bot_added(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``bot_added`` events."""
        return self._register((UpdateType.BOT_ADDED.value,), filters)

    def bot_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``bot_removed`` events."""
        return self._register((UpdateType.BOT_REMOVED.value,), filters)

    def user_added(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``user_added`` events."""
        return self._register((UpdateType.USER_ADDED.value,), filters)

    def user_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``user_removed`` events."""
        return self._register((UpdateType.USER_REMOVED.value,), filters)

    def message_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``message_removed`` events."""
        return self._register((UpdateType.MESSAGE_REMOVED.value,), filters)

    def chat_created(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``message_chat_created`` events."""
        return self._register((UpdateType.MESSAGE_CHAT_CREATED.value,), filters)

    def chat_title_changed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        """Register a handler for ``chat_title_changed`` events."""
        return self._register((UpdateType.CHAT_TITLE_CHANGED.value,), filters)

    def event(
        self,
        *update_types: str,
        filters: tuple[Filter | FilterFunc, ...] = (),
    ) -> Callable[[Handler], Handler]:
        """Subscribe to arbitrary update types. No arguments catches every update."""
        return self._register(tuple(str(t) for t in update_types), filters)

    def outer_middleware(self, mw: OuterMiddlewareFn, *update_types: str) -> None:
        """Register an outer middleware. Without ``update_types`` it applies to all events."""
        self._outer.append(_OuterReg(frozenset(str(t) for t in update_types), mw))

    def inner_middleware(self, mw: InnerMiddlewareFn, *update_types: str) -> None:
        """Register an inner middleware. Without ``update_types`` it applies to all events."""
        self._inner.append(_InnerReg(frozenset(str(t) for t in update_types), mw))
