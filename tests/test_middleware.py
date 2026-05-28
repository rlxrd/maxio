from __future__ import annotations

from typing import Any

from conftest import message_callback, message_created
from maxio import MaxBot, Message, Router, Update
from maxio.enums import UpdateType


async def test_outer_runs_around_handler() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(update: Update, call_next: Any) -> bool:
        calls.append("before")
        result = await call_next()
        calls.append("after")
        return result

    app.outer_middleware(mw)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["before", "handler", "after"]
    await app.bot.aclose()


async def test_outer_can_abort() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(update: Update, call_next: Any) -> bool:
        calls.append("aborted")
        return False

    app.outer_middleware(mw)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    result = await app.feed_update(Update.model_validate(message_created()))
    assert result is False
    assert calls == ["aborted"]
    await app.bot.aclose()


async def test_outer_onion_order() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def first(update: Update, call_next: Any) -> bool:
        calls.append("first_in")
        result = await call_next()
        calls.append("first_out")
        return result

    async def second(update: Update, call_next: Any) -> bool:
        calls.append("second_in")
        result = await call_next()
        calls.append("second_out")
        return result

    app.outer_middleware(first)
    app.outer_middleware(second)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["first_in", "second_in", "handler", "second_out", "first_out"]
    await app.bot.aclose()


async def test_outer_filtered_by_update_type() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(update: Update, call_next: Any) -> bool:
        calls.append("mw")
        return await call_next()

    app.outer_middleware(mw, UpdateType.MESSAGE_CREATED)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["mw", "handler"]

    calls.clear()
    # message_callback — mw не сработает (тип не совпадает)
    await app.feed_update(Update.model_validate(message_callback()))
    assert calls == []
    await app.bot.aclose()


async def test_inner_runs_around_handler() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("inner_before")
        await call_next()
        calls.append("inner_after")

    app.inner_middleware(mw)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["inner_before", "handler", "inner_after"]
    await app.bot.aclose()


async def test_inner_receives_resolved_kwargs() -> None:
    app = MaxBot("TOKEN")
    received: dict[str, Any] = {}

    async def mw(handler: Any, kwargs: dict[str, Any], call_next: Any) -> None:
        received.update(kwargs)
        await call_next()

    app.inner_middleware(mw)

    @app.message()
    async def handler(message: Message) -> None:
        pass

    await app.feed_update(Update.model_validate(message_created("тест")))
    assert "message" in received
    assert received["message"].text == "тест"
    await app.bot.aclose()


async def test_inner_can_skip_handler() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("inner")

    app.inner_middleware(mw)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    result = await app.feed_update(Update.model_validate(message_created()))
    assert result is True
    assert calls == ["inner"]
    await app.bot.aclose()


async def test_inner_filtered_by_update_type() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def mw(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("inner")
        await call_next()

    app.inner_middleware(mw, UpdateType.MESSAGE_CALLBACK)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    # message_created — inner не сработает
    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["handler"]
    await app.bot.aclose()


async def test_outer_and_inner_combined() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    async def outer(update: Update, call_next: Any) -> bool:
        calls.append("outer_in")
        result = await call_next()
        calls.append("outer_out")
        return result

    async def inner(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("inner_in")
        await call_next()
        calls.append("inner_out")

    app.outer_middleware(outer)
    app.inner_middleware(inner)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["outer_in", "inner_in", "handler", "inner_out", "outer_out"]
    await app.bot.aclose()


async def test_router_outer_middleware() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    async def mw(update: Update, call_next: Any) -> bool:
        calls.append("router_outer_in")
        result = await call_next()
        calls.append("router_outer_out")
        return result

    router.outer_middleware(mw)

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["router_outer_in", "handler", "router_outer_out"]
    await app.bot.aclose()


async def test_router_outer_not_called_for_app_handler() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    async def router_mw(update: Update, call_next: Any) -> bool:
        calls.append("router_mw")
        return await call_next()

    router.outer_middleware(router_mw)

    @app.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    # router.outer не вызвался — хэндлер принадлежит app, не роутеру
    assert calls == ["handler"]
    await app.bot.aclose()


async def test_app_outer_and_router_outer_order() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    async def app_outer(update: Update, call_next: Any) -> bool:
        calls.append("app_outer_in")
        result = await call_next()
        calls.append("app_outer_out")
        return result

    async def router_outer(update: Update, call_next: Any) -> bool:
        calls.append("router_outer_in")
        result = await call_next()
        calls.append("router_outer_out")
        return result

    app.outer_middleware(app_outer)
    router.outer_middleware(router_outer)

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == [
        "app_outer_in",
        "router_outer_in",
        "handler",
        "router_outer_out",
        "app_outer_out",
    ]
    await app.bot.aclose()


async def test_app_inner_and_router_inner_order() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    async def app_inner(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("app_inner_in")
        await call_next()
        calls.append("app_inner_out")

    async def router_inner(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("router_inner_in")
        await call_next()
        calls.append("router_inner_out")

    app.inner_middleware(app_inner)
    router.inner_middleware(router_inner)

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("handler")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == [
        "app_inner_in",
        "router_inner_in",
        "handler",
        "router_inner_out",
        "app_inner_out",
    ]
    await app.bot.aclose()


async def test_full_stack_order() -> None:
    """app.outer → router.outer → app.inner → router.inner → handler"""
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    async def ao(update: Update, call_next: Any) -> bool:
        calls.append("ao")
        r = await call_next()
        calls.append("/ao")
        return r

    async def ro(update: Update, call_next: Any) -> bool:
        calls.append("ro")
        r = await call_next()
        calls.append("/ro")
        return r

    async def ai(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("ai")
        await call_next()
        calls.append("/ai")

    async def ri(handler: Any, kwargs: Any, call_next: Any) -> None:
        calls.append("ri")
        await call_next()
        calls.append("/ri")

    app.outer_middleware(ao)
    router.outer_middleware(ro)
    app.inner_middleware(ai)
    router.inner_middleware(ri)

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("h")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == ["ao", "ro", "ai", "ri", "h", "/ri", "/ai", "/ro", "/ao"]
    await app.bot.aclose()
