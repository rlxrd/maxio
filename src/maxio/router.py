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
    """Реестр хэндлеров, подключаемый к MaxBot через include_routers."""

    def __init__(self) -> None:
        self._handlers: list[_Registration] = []
        self._outer: list[_OuterReg] = []
        self._inner: list[_InnerReg] = []

    # --- регистрация хэндлеров ---

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
        return self._register((UpdateType.MESSAGE_CREATED.value,), filters)

    def message_edited(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.MESSAGE_EDITED.value,), filters)

    def callback(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.MESSAGE_CALLBACK.value,), filters)

    def bot_started(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.BOT_STARTED.value,), filters)

    def bot_added(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.BOT_ADDED.value,), filters)

    def bot_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.BOT_REMOVED.value,), filters)

    def user_added(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.USER_ADDED.value,), filters)

    def user_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.USER_REMOVED.value,), filters)

    def message_removed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.MESSAGE_REMOVED.value,), filters)

    def chat_created(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.MESSAGE_CHAT_CREATED.value,), filters)

    def chat_title_changed(self, *filters: Filter | FilterFunc) -> Callable[[Handler], Handler]:
        return self._register((UpdateType.CHAT_TITLE_CHANGED.value,), filters)

    def event(
        self,
        *update_types: str,
        filters: tuple[Filter | FilterFunc, ...] = (),
    ) -> Callable[[Handler], Handler]:
        """Подписка на произвольные типы событий. Без аргументов ловит любые апдейты."""
        return self._register(tuple(str(t) for t in update_types), filters)

    # --- регистрация middleware ---

    def outer_middleware(self, mw: OuterMiddlewareFn, *update_types: str) -> None:
        """Добавить outer middleware. Без update_types — для всех типов апдейтов."""
        self._outer.append(_OuterReg(frozenset(str(t) for t in update_types), mw))

    def inner_middleware(self, mw: InnerMiddlewareFn, *update_types: str) -> None:
        """Добавить inner middleware. Без update_types — для всех типов апдейтов."""
        self._inner.append(_InnerReg(frozenset(str(t) for t in update_types), mw))
