from __future__ import annotations

import json
import logging

import httpx
import pytest
import respx

from conftest import message_payload
from maxio import Bot, InlineKeyboard, MaxApiError
from maxio._logging import TokenMaskingFilter
from maxio.keyboards import Button


@respx.mock
async def test_send_message_query_vs_body() -> None:
    route = respx.post("https://botapi.max.ru/messages").mock(
        return_value=httpx.Response(200, json={"message": message_payload("ответ")})
    )
    bot = Bot("TOKEN")
    msg = await bot.send_message("hi", chat_id=10)

    request = route.calls.last.request
    assert request.url.params["chat_id"] == "10"
    assert request.url.params["access_token"] == "TOKEN"
    assert request.headers["Authorization"] == "TOKEN"

    body = json.loads(request.content)
    assert body["text"] == "hi"
    assert body["notify"] is True
    assert "chat_id" not in body  # идентификатор уходит в query, не в тело

    assert msg.text == "ответ"
    await bot.aclose()


@respx.mock
async def test_send_message_with_keyboard() -> None:
    route = respx.post("https://botapi.max.ru/messages").mock(
        return_value=httpx.Response(200, json={"message": message_payload()})
    )
    bot = Bot("TOKEN")
    kb = InlineKeyboard().row(Button.callback("Жми", "x"))
    await bot.send_message("t", chat_id=1, keyboard=kb)

    body = json.loads(route.calls.last.request.content)
    assert body["attachments"][0]["type"] == "inline_keyboard"
    assert body["attachments"][0]["payload"]["buttons"][0][0]["payload"] == "x"
    await bot.aclose()


def _make_record(msg: str, *args: object) -> logging.LogRecord:
    return logging.LogRecord("httpx", logging.INFO, __file__, 0, msg, args, None)


def test_token_masking_filter_hides_token_in_url() -> None:
    flt = TokenMaskingFilter()
    record = _make_record(
        'HTTP Request: GET %s "%s"',
        "https://botapi.max.ru/updates?access_token=SECRET&limit=100",
        "HTTP/1.1 200 OK",
    )
    flt.filter(record)
    rendered = record.getMessage()
    assert "SECRET" not in rendered
    assert "access_token=***" in rendered


def test_token_masking_filter_hides_authorization() -> None:
    flt = TokenMaskingFilter()
    record = _make_record("headers: Authorization: SECRET, host: x")
    flt.filter(record)
    rendered = record.getMessage()
    assert "SECRET" not in rendered
    assert "Authorization: ***" in rendered


async def test_send_message_requires_target() -> None:
    bot = Bot("TOKEN")
    with pytest.raises(ValueError):
        await bot.send_message("hi")
    await bot.aclose()


@respx.mock
async def test_api_error_raised() -> None:
    respx.get("https://botapi.max.ru/me").mock(
        return_value=httpx.Response(401, json={"code": "verify.token", "message": "bad token"})
    )
    bot = Bot("TOKEN")
    with pytest.raises(MaxApiError) as exc:
        await bot.get_me()
    assert exc.value.status_code == 401
    assert exc.value.code == "verify.token"
    await bot.aclose()
