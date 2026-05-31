from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

from annotated_doc import Doc

from maxio._runtime import current_bot
from maxio.bot import Bot
from maxio.filters import Filter, FilterFunc, apply_filter
from maxio.fsm.context import FSMContext, current_fsm_context
from maxio.fsm.storage import BaseStorage, MemoryStorage, StorageKey
from maxio.injection import resolve_kwargs
from maxio.middleware import (
    CallNextInner,
    CallNextOuter,
    Handler,
    HandlerKwargs,
    InnerMiddlewareFn,
    OuterMiddlewareFn,
)
from maxio.router import Router, _Registration
from maxio.types.callback import Callback
from maxio.types.chat import Chat
from maxio.types.message import Message
from maxio.types.update import Update
from maxio.types.user import BotInfo, User

logger = logging.getLogger("maxio")


def _storage_key(update: Update) -> StorageKey | None:
    user_id: int | None = None
    chat_id: int | None = update.chat_id
    if update.message is not None:
        if update.message.sender is not None:
            user_id = update.message.sender.user_id
        if chat_id is None:
            chat_id = update.message.recipient.chat_id
    elif update.callback is not None and update.callback.user is not None:
        user_id = update.callback.user.user_id
        if chat_id is None and update.message is not None:
            chat_id = update.message.recipient.chat_id
    elif update.user is not None:
        user_id = update.user.user_id
    if user_id is None:
        return None
    return StorageKey(user_id=user_id, chat_id=chat_id)


class MaxBot(Router):
    """Main bot application. Register handlers with decorators; arguments are injected by type.

    Example:
        ```python
        from maxio import MaxBot, Message

        bot = MaxBot("your-token")

        @bot.message()
        async def echo(message: Message) -> None:
            await message.answer(message.text)

        bot.run()
        ```
    """

    def __init__(
        self,
        token: Annotated[
            str,
            Doc(
                """
                MAX Bot API access token.

                Obtain it from the BotFather in the MAX messenger.
                """
            ),
        ],
        *,
        storage: Annotated[
            BaseStorage | None,
            Doc(
                """
                FSM state storage backend.

                Defaults to ``MemoryStorage`` when not provided.
                """
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc(
                """
                HTTP request timeout in seconds forwarded to ``Bot``.
                """
            ),
        ] = 100.0,
        mask_token_in_logs: Annotated[
            bool,
            Doc(
                """
                Replace the token with ``***`` in all log output.

                Enabled by default to prevent accidental token leaks.
                """
            ),
        ] = True,
    ) -> None:
        super().__init__()
        self.bot = Bot(
            token,
            timeout=timeout,
            mask_token_in_logs=mask_token_in_logs,
        )
        self._storage: BaseStorage = storage if storage is not None else MemoryStorage()
        self._routers: list[Router] = []
        self._running = False
        self.me: BotInfo | None = None

    def include_routers(self, *routers: Router) -> None:
        """Mount routers onto this application.

        App-level handlers are checked first, then routers in the order they are added.
        """
        self._routers.extend(routers)

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
        key = _storage_key(update)
        if key is not None:
            ctx[FSMContext] = FSMContext(self._storage, key)
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

    async def _find_handler(self, update: Update) -> tuple[_Registration, Router] | None:
        for source in (self, *self._routers):
            for reg in source._handlers:
                if reg.update_types and update.update_type not in reg.update_types:
                    continue
                if not await self._passes_filters(reg.filters, update):
                    continue
                return reg, source
        return None

    @staticmethod
    def _wrap_outer(
        fn: OuterMiddlewareFn,
        nxt: CallNextOuter,
        context: dict[type, Any],
    ) -> CallNextOuter:
        async def step() -> bool:
            mw_ctx = {**context, CallNextOuter: nxt}
            mw_kwargs = resolve_kwargs(fn, mw_ctx)
            return await fn(**mw_kwargs)
        return CallNextOuter(step)

    @staticmethod
    def _wrap_inner(
        fn: InnerMiddlewareFn,
        nxt: CallNextInner,
        handler_fn: Handler,
        handler_kwargs: dict[str, Any],
        context: dict[type, Any],
    ) -> CallNextInner:
        async def step() -> None:
            mw_ctx = {
                **context,
                CallNextInner: nxt,
                HandlerKwargs: HandlerKwargs(handler_kwargs),
            }
            mw_kwargs = resolve_kwargs(fn, mw_ctx)
            await fn(**mw_kwargs)
        return CallNextInner(step)

    async def _dispatch_core(self, update: Update, context: dict[type, Any]) -> bool:
        result = await self._find_handler(update)
        if result is None:
            return False

        reg, owner = result
        handler_fn = reg.fn
        kwargs = resolve_kwargs(handler_fn, context)

        async def call_handler() -> None:
            await handler_fn(**kwargs)

        inner_chain = CallNextInner(call_handler)
        if owner is not self:
            router_inner = [
                m.fn for m in owner._inner
                if not m.update_types or update.update_type in m.update_types
            ]
            for ifn in reversed(router_inner):
                inner_chain = self._wrap_inner(ifn, inner_chain, handler_fn, kwargs, context)
        app_inner = [
            m.fn for m in self._inner
            if not m.update_types or update.update_type in m.update_types
        ]
        for ifn in reversed(app_inner):
            inner_chain = self._wrap_inner(ifn, inner_chain, handler_fn, kwargs, context)

        async def run_inner() -> bool:
            await inner_chain()
            return True

        router_outer_chain = CallNextOuter(run_inner)
        if owner is not self:
            router_outer = [
                m.fn for m in owner._outer
                if not m.update_types or update.update_type in m.update_types
            ]
            for ofn in reversed(router_outer):
                router_outer_chain = self._wrap_outer(ofn, router_outer_chain, context)

        return await router_outer_chain()

    async def feed_update(self, update: Update) -> bool:
        """Run a single update through all middleware and handlers.

        Returns ``True`` if a handler was found and executed.
        """
        context = self._build_context(update)
        token_bot = current_bot.set(self.bot)
        token_fsm = current_fsm_context.set(context.get(FSMContext))
        try:
            async def core() -> bool:
                return await self._dispatch_core(update, context)

            app_outer = [
                m.fn for m in self._outer
                if not m.update_types or update.update_type in m.update_types
            ]
            outer_chain = CallNextOuter(core)
            for ofn in reversed(app_outer):
                outer_chain = self._wrap_outer(ofn, outer_chain, context)

            return await outer_chain()
        finally:
            current_bot.reset(token_bot)
            current_fsm_context.reset(token_fsm)

    async def start_polling(
        self,
        *,
        timeout: Annotated[int, Doc("Long-poll server timeout in seconds.")] = 30,
        limit: Annotated[int, Doc("Maximum updates per request.")] = 100,
        types: Annotated[list[str] | None, Doc("Filter by update types.")] = None,
    ) -> None:
        """Start the long-polling loop. Runs until :meth:`stop` is called or interrupted."""
        self.me = await self.bot.get_me()
        logger.info("Bot started: @%s (id=%s)", self.me.username, self.me.user_id)
        marker: int | None = None
        self._running = True
        try:
            while self._running:
                try:
                    result = await self.bot.get_updates(
                        limit=limit, timeout=timeout, marker=marker, types=types
                    )
                except Exception:
                    logger.exception("Error fetching updates, retrying in 3s")
                    await asyncio.sleep(3)
                    continue
                for update in result.updates:
                    try:
                        await self.feed_update(update)
                    except Exception:
                        logger.exception(
                            "Unhandled error in handler for update %s", update.update_type
                        )
                if result.marker is not None:
                    marker = result.marker
        finally:
            await self.bot.aclose()

    def stop(self) -> None:
        """Signal the polling loop to stop after the current iteration."""
        self._running = False

    def run(self, **kwargs: Any) -> None:
        """Start long-polling (blocking). Stops cleanly on ``KeyboardInterrupt``."""
        try:
            asyncio.run(self.start_polling(**kwargs))
        except KeyboardInterrupt:
            logger.info("Stopped by Ctrl+C")
