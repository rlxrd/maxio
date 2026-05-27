from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from maxio._runtime import current_bot
from maxio.bot import Bot
from maxio.enums import UpdateType
from maxio.filters import Filter, FilterFunc, apply_filter
from maxio.injection import resolve_kwargs
from maxio.types.callback import Callback
from maxio.types.chat import Chat
from maxio.types.message import Message
from maxio.types.update import Update
from maxio.types.user import BotInfo, User

logger = logging.getLogger("maxio")

Handler = Callable[..., Awaitable[Any]]


@dataclass(slots=True)
class _Registration:
    update_types: frozenset[str]
    filters: tuple[Filter | FilterFunc, ...]
    fn: Handler


class MaxBot:
    """Приложение-бот: хэндлеры регистрируются декораторами,
    а их аргументы внедряются по аннотациям типов."""

    def __init__(self, token: str, **bot_kwargs: Any) -> None:
        self.bot = Bot(token, **bot_kwargs)
        self._handlers: list[_Registration] = []
        self._running = False
        self.me: BotInfo | None = None

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

    def event(
        self,
        *update_types: str,
        filters: tuple[Filter | FilterFunc, ...] = (),
    ) -> Callable[[Handler], Handler]:
        """Подписка на произвольные типы событий. Без аргументов ловит любые апдейты."""
        return self._register(tuple(str(t) for t in update_types), filters)

    # --- диспетчеризация ---

    def _build_context(self, update: Update) -> dict[type, Any]:
        ctx: dict[type, Any] = {Bot: self.bot, Update: update}
        if update.message is not None:
            ctx[Message] = update.message
            if update.message.sender is not None:
                ctx[User] = update.message.sender
        if update.callback is not None:
            update.callback.message = update.message
            ctx[Callback] = update.callback
            if update.callback.user is not None:
                ctx[User] = update.callback.user
        if update.user is not None:
            ctx[User] = update.user
        if update.chat is not None:
            ctx[Chat] = update.chat
        return ctx

    async def _passes_filters(
        self,
        filters: tuple[Filter | FilterFunc, ...],
        update: Update,
    ) -> bool:
        for flt in filters:
            if not await apply_filter(flt, update):
                return False
        return True

    async def feed_update(self, update: Update) -> bool:
        """Прогнать один апдейт через хэндлеры. Возвращает True, если сработал хэндлер."""
        context = self._build_context(update)
        token = current_bot.set(self.bot)
        try:
            for handler in self._handlers:
                if handler.update_types and update.update_type not in handler.update_types:
                    continue
                if not await self._passes_filters(handler.filters, update):
                    continue
                kwargs = resolve_kwargs(handler.fn, context)
                await handler.fn(**kwargs)
                return True
        finally:
            current_bot.reset(token)
        return False

    # --- long polling ---

    async def start_polling(
        self,
        *,
        timeout: int = 30,
        limit: int = 100,
        types: list[str] | None = None,
    ) -> None:
        self.me = await self.bot.get_me()
        logger.info("Бот запущен: @%s (id=%s)", self.me.username, self.me.user_id)
        marker: int | None = None
        self._running = True
        try:
            while self._running:
                try:
                    result = await self.bot.get_updates(
                        limit=limit, timeout=timeout, marker=marker, types=types
                    )
                except Exception:
                    logger.exception("Ошибка при получении апдейтов, повтор через 3с")
                    await asyncio.sleep(3)
                    continue
                for update in result.updates:
                    try:
                        await self.feed_update(update)
                    except Exception:
                        logger.exception(
                            "Ошибка в обработчике апдейта %s", update.update_type
                        )
                if result.marker is not None:
                    marker = result.marker
        finally:
            await self.bot.aclose()

    def stop(self) -> None:
        self._running = False

    def run(self, **kwargs: Any) -> None:
        try:
            asyncio.run(self.start_polling(**kwargs))
        except KeyboardInterrupt:
            logger.info("Остановка по Ctrl+C")
