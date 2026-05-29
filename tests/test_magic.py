from __future__ import annotations

from typing import Any

import pytest

from conftest import message_callback, message_created
from maxio import F, MaxBot, Message
from maxio.types.update import Update


def upd(data: dict[str, Any]) -> Update:
    return Update.model_validate(data)


def msg(text: str = "привет", attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = message_created(text)
    if attachments is not None:
        data["message"]["body"]["attachments"] = attachments
    return data


# --- F.text ---

@pytest.mark.asyncio
async def test_text_truthy() -> None:
    assert await F.text.check(upd(msg("привет"))) is True


@pytest.mark.asyncio
async def test_text_falsy_when_no_message() -> None:
    u = upd({"update_type": "bot_started", "timestamp": 1,
             "user": {"user_id": 1, "name": "T", "is_bot": False}, "chat_id": 1})
    assert await F.text.check(u) is False


@pytest.mark.asyncio
async def test_text_eq() -> None:
    assert await (F.text == "привет").check(upd(msg("привет")))
    assert not await (F.text == "пока").check(upd(msg("привет")))


@pytest.mark.asyncio
async def test_text_ne() -> None:
    assert await (F.text != "пока").check(upd(msg("привет")))
    assert not await (F.text != "привет").check(upd(msg("привет")))


@pytest.mark.asyncio
async def test_text_startswith() -> None:
    assert await F.text.startswith("/").check(upd(msg("/start")))
    assert not await F.text.startswith("/").check(upd(msg("привет")))


@pytest.mark.asyncio
async def test_text_endswith() -> None:
    assert await F.text.endswith("!").check(upd(msg("привет!")))
    assert not await F.text.endswith("!").check(upd(msg("привет")))


@pytest.mark.asyncio
async def test_text_contains() -> None:
    assert await F.text.contains("вет").check(upd(msg("привет")))
    assert not await F.text.contains("пока").check(upd(msg("привет")))


@pytest.mark.asyncio
async def test_text_in() -> None:
    flt = F.text.in_("да", "нет")
    assert await flt.check(upd(msg("да")))
    assert await flt.check(upd(msg("нет")))
    assert not await flt.check(upd(msg("может")))


@pytest.mark.asyncio
async def test_text_not_in() -> None:
    flt = F.text.not_in_("да", "нет")
    assert await flt.check(upd(msg("может")))
    assert not await flt.check(upd(msg("да")))


# --- F.data (callback payload) ---

@pytest.mark.asyncio
async def test_data_eq() -> None:
    assert await (F.data == "ping").check(upd(message_callback("ping")))
    assert not await (F.data == "ping").check(upd(message_callback("pong")))


@pytest.mark.asyncio
async def test_data_falsy_when_no_callback() -> None:
    assert not await F.data.check(upd(msg()))


@pytest.mark.asyncio
async def test_data_in() -> None:
    flt = F.data.in_("buy", "sell")
    assert await flt.check(upd(message_callback("buy")))
    assert not await flt.check(upd(message_callback("hold")))


# --- F.photo / F.video / F.audio / F.file ---

@pytest.mark.asyncio
async def test_photo_true() -> None:
    u = upd(msg(attachments=[{"type": "image", "payload": {"token": "t"}}]))
    assert await F.photo.check(u)
    assert await F.image.check(u)


@pytest.mark.asyncio
async def test_photo_false_wrong_type() -> None:
    u = upd(msg(attachments=[{"type": "video", "payload": {"token": "t"}}]))
    assert not await F.photo.check(u)


@pytest.mark.asyncio
async def test_video_true() -> None:
    u = upd(msg(attachments=[{"type": "video", "payload": {"token": "t"}}]))
    assert await F.video.check(u)


@pytest.mark.asyncio
async def test_audio_true() -> None:
    u = upd(msg(attachments=[{"type": "audio", "payload": {"token": "t"}}]))
    assert await F.audio.check(u)


@pytest.mark.asyncio
async def test_file_and_document() -> None:
    u = upd(msg(attachments=[{"type": "file", "payload": {"token": "t"}}]))
    assert await F.file.check(u)
    assert await F.document.check(u)


@pytest.mark.asyncio
async def test_media_false_no_attachments() -> None:
    assert not await F.photo.check(upd(msg()))
    assert not await F.video.check(upd(msg()))


# --- комбинаторы ---

@pytest.mark.asyncio
async def test_and() -> None:
    flt = (F.text == "привет") & F.text
    assert await flt.check(upd(msg("привет")))
    assert not await flt.check(upd(msg("пока")))


@pytest.mark.asyncio
async def test_or() -> None:
    flt = (F.text == "да") | (F.text == "нет")
    assert await flt.check(upd(msg("да")))
    assert await flt.check(upd(msg("нет")))
    assert not await flt.check(upd(msg("может")))


@pytest.mark.asyncio
async def test_not() -> None:
    flt = ~(F.text == "стоп")
    assert await flt.check(upd(msg("привет")))
    assert not await flt.check(upd(msg("стоп")))


# --- полный путь без шортката ---

@pytest.mark.asyncio
async def test_full_path() -> None:
    assert await (F.message.sender.user_id == 5).check(upd(msg()))
    assert not await (F.message.sender.user_id == 99).check(upd(msg()))


# --- использование как декоратор хэндлера ---

@pytest.mark.asyncio
async def test_f_as_handler_filter() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(F.text == "старт")
    async def handler(message: Message) -> None:
        calls.append(message.text or "")

    await app.feed_update(Update.model_validate(msg("старт")))
    await app.feed_update(Update.model_validate(msg("стоп")))
    assert calls == ["старт"]
    await app.bot.aclose()
