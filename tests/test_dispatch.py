from __future__ import annotations

import json

import httpx
import pytest
import respx

from conftest import message_callback, message_created
from maxio import Bot, Callback, CallbackPayload, Command, MaxBot, Message, Router, Update
from maxio.exceptions import MaxError


async def test_dispatch_injects_by_type() -> None:
    app = MaxBot("TOKEN")
    seen: dict[str, object] = {}

    @app.message()
    async def handler(message: Message, bot: Bot) -> None:
        seen["text"] = message.text
        seen["bot_is_app_bot"] = bot is app.bot

    handled = await app.feed_update(Update.model_validate(message_created("привет")))

    assert handled is True
    assert seen["text"] == "привет"
    assert seen["bot_is_app_bot"] is True
    await app.bot.aclose()


async def test_unknown_type_raises() -> None:
    app = MaxBot("TOKEN")

    @app.message()
    async def handler(callback: Callback) -> None:  # недоступен для message_created
        pass

    with pytest.raises(MaxError):
        await app.feed_update(Update.model_validate(message_created()))
    await app.bot.aclose()


async def test_command_filter_routing() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(Command("start"))
    async def on_start(message: Message) -> None:
        calls.append("start")

    @app.message()
    async def fallback(message: Message) -> None:
        calls.append("fallback")

    await app.feed_update(Update.model_validate(message_created("/start")))
    await app.feed_update(Update.model_validate(message_created("просто текст")))

    assert calls == ["start", "fallback"]  # first-match wins
    await app.bot.aclose()


@respx.mock
async def test_message_answer_targets_recipient() -> None:
    route = respx.post("https://botapi.max.ru/messages").mock(
        return_value=httpx.Response(200, json={"message": message_created()["message"]})
    )
    app = MaxBot("TOKEN")

    @app.message()
    async def handler(message: Message) -> None:
        await message.answer("ok")

    await app.feed_update(Update.model_validate(message_created(chat_id=42)))

    assert route.calls.last.request.url.params["chat_id"] == "42"
    await app.bot.aclose()


@respx.mock
async def test_callback_dispatch_and_answer() -> None:
    route = respx.post("https://botapi.max.ru/answers").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    app = MaxBot("TOKEN")

    @app.callback(CallbackPayload("ping"))
    async def handler(callback: Callback) -> None:
        await callback.answer(notification="pong")

    handled = await app.feed_update(Update.model_validate(message_callback("ping")))

    assert handled is True
    request = route.calls.last.request
    assert request.url.params["callback_id"] == "cb-1"
    assert json.loads(request.content)["notification"] == "pong"
    await app.bot.aclose()


async def test_router_handles_after_app() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("router")

    handled = await app.feed_update(Update.model_validate(message_created()))

    assert handled is True
    assert calls == ["router"]
    await app.bot.aclose()


async def test_app_takes_priority_over_router() -> None:
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    @app.message()
    async def app_handler(message: Message) -> None:
        calls.append("app")

    @router.message()
    async def router_handler(message: Message) -> None:
        calls.append("router")

    await app.feed_update(Update.model_validate(message_created()))

    assert calls == ["app"]
    await app.bot.aclose()


async def test_routers_checked_in_order() -> None:
    app = MaxBot("TOKEN")
    first = Router()
    second = Router()
    app.include_routers(first, second)
    calls: list[str] = []

    @first.message()
    async def first_handler(message: Message) -> None:
        calls.append("first")

    @second.message()
    async def second_handler(message: Message) -> None:
        calls.append("second")

    await app.feed_update(Update.model_validate(message_created()))

    assert calls == ["first"]
    await app.bot.aclose()


async def test_router_registers_before_include() -> None:
    """Хэндлеры, добавленные в роутер после include_routers, всё равно работают."""
    app = MaxBot("TOKEN")
    router = Router()
    app.include_routers(router)
    calls: list[str] = []

    @router.message()
    async def handler(message: Message) -> None:
        calls.append("late")

    handled = await app.feed_update(Update.model_validate(message_created()))

    assert handled is True
    assert calls == ["late"]
    await app.bot.aclose()


@respx.mock
async def test_callback_message_answer() -> None:
    route = respx.post("https://botapi.max.ru/messages").mock(
        return_value=httpx.Response(200, json={"message": message_created()["message"]})
    )
    app = MaxBot("TOKEN")

    @app.callback()
    async def handler(callback: Callback) -> None:
        assert callback.message is not None
        await callback.message.answer("новое сообщение")

    await app.feed_update(Update.model_validate(message_callback("ping")))

    request = route.calls.last.request
    assert request.url.params["chat_id"] == "10"
    assert json.loads(request.content)["text"] == "новое сообщение"
    await app.bot.aclose()
