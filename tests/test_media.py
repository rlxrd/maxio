from __future__ import annotations

import httpx
import respx

from conftest import message_created
from maxio import HasMedia, MaxBot, Message, Update
from maxio import media as m
from maxio.types.attachment import (
    Attachment,
)

# ---------------------------------------------------------------------------
# Attachment payload парсинг
# ---------------------------------------------------------------------------

def test_attachment_as_image() -> None:
    att = Attachment(type="image", payload={"token": "tok", "url": "https://img", "photo_id": 1})
    img = att.as_image()
    assert img is not None
    assert img.token == "tok"
    assert img.url == "https://img"
    assert img.photo_id == 1


def test_attachment_as_image_wrong_type() -> None:
    att = Attachment(type="file", payload={"token": "tok"})
    assert att.as_image() is None


def test_attachment_as_video() -> None:
    att = Attachment(type="video", payload={
        "token": "vtok", "url": "https://video", "duration": 30, "width": 1280, "height": 720
    })
    vid = att.as_video()
    assert vid is not None
    assert vid.token == "vtok"
    assert vid.duration == 30


def test_attachment_as_audio() -> None:
    att = Attachment(
        type="audio", payload={"token": "atok", "url": "https://audio", "duration": 60}
    )
    aud = att.as_audio()
    assert aud is not None
    assert aud.duration == 60


def test_attachment_as_file() -> None:
    att = Attachment(type="file", payload={
        "token": "ftok", "url": "https://file", "filename": "doc.pdf", "size": 1024
    })
    f = att.as_file()
    assert f is not None
    assert f.filename == "doc.pdf"
    assert f.size == 1024


def test_attachment_as_file_no_payload() -> None:
    att = Attachment(type="file", payload=None)
    assert att.as_file() is None


# ---------------------------------------------------------------------------
# Message.photos / videos / audio / files
# ---------------------------------------------------------------------------

def _message_with_attachments(*atts: dict) -> dict:
    base = message_created()
    base["message"]["body"]["attachments"] = list(atts)
    return base


def test_message_photos() -> None:
    data = _message_with_attachments(
        {"type": "image", "payload": {"token": "t1", "url": "https://img1"}},
        {"type": "image", "payload": {"token": "t2", "url": "https://img2"}},
    )
    update = Update.model_validate(data)
    assert update.message is not None
    photos = update.message.photos
    assert len(photos) == 2
    assert photos[0].token == "t1"
    assert photos[1].token == "t2"


def test_message_files() -> None:
    data = _message_with_attachments(
        {"type": "file", "payload": {"token": "ft", "filename": "a.zip", "size": 512, "url": "u"}}
    )
    update = Update.model_validate(data)
    assert update.message is not None
    files = update.message.files
    assert len(files) == 1
    assert files[0].filename == "a.zip"


def test_message_attachments_empty() -> None:
    update = Update.model_validate(message_created())
    assert update.message is not None
    assert update.message.photos == []
    assert update.message.files == []


# ---------------------------------------------------------------------------
# media фабрики
# ---------------------------------------------------------------------------

def test_media_image() -> None:
    att = m.image("tok123")
    assert att == {"type": "image", "payload": {"token": "tok123"}}


def test_media_video() -> None:
    att = m.video("vtok")
    assert att["type"] == "video"
    assert att["payload"]["token"] == "vtok"


def test_media_audio() -> None:
    assert m.audio("atok")["type"] == "audio"


def test_media_file() -> None:
    assert m.file("ftok")["type"] == "file"


# ---------------------------------------------------------------------------
# HasMedia фильтр
# ---------------------------------------------------------------------------

async def test_has_media_matches_type() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(HasMedia("image"))
    async def handler(message: Message) -> None:
        calls.append("image")

    data = _message_with_attachments(
        {"type": "image", "payload": {"token": "t", "url": "u"}}
    )
    await app.feed_update(Update.model_validate(data))
    assert calls == ["image"]
    await app.bot.aclose()


async def test_has_media_no_match() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(HasMedia("video"))
    async def handler(message: Message) -> None:
        calls.append("video")

    data = _message_with_attachments(
        {"type": "image", "payload": {"token": "t", "url": "u"}}
    )
    await app.feed_update(Update.model_validate(data))
    assert calls == []
    await app.bot.aclose()


async def test_has_media_any() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(HasMedia())
    async def handler(message: Message) -> None:
        calls.append("any")

    data = _message_with_attachments(
        {"type": "audio", "payload": {"token": "t", "url": "u"}}
    )
    await app.feed_update(Update.model_validate(data))
    assert calls == ["any"]
    await app.bot.aclose()


async def test_has_media_no_attachments() -> None:
    app = MaxBot("TOKEN")
    calls: list[str] = []

    @app.message(HasMedia())
    async def handler(message: Message) -> None:
        calls.append("hit")

    await app.feed_update(Update.model_validate(message_created()))
    assert calls == []
    await app.bot.aclose()


# ---------------------------------------------------------------------------
# Bot.upload
# ---------------------------------------------------------------------------

@respx.mock
async def test_upload_image() -> None:
    # Шаг 1: POST /uploads → upload endpoint
    respx.post("https://botapi.max.ru/uploads").mock(
        return_value=httpx.Response(200, json={"url": "https://upload.max.ru/img"})
    )
    # Шаг 2: POST на upload URL → token
    respx.post("https://upload.max.ru/img").mock(
        return_value=httpx.Response(200, json={"token": "image_token_123"})
    )

    from maxio import Bot
    from maxio.enums import UploadType

    bot = Bot("TOKEN")
    token = await bot.upload(b"fake_image_data", UploadType.IMAGE, filename="photo.jpg")
    assert token == "image_token_123"
    await bot.aclose()


@respx.mock
async def test_upload_video_token_from_endpoint() -> None:
    """Для video токен приходит сразу из /uploads (без второго ответа)."""
    respx.post("https://botapi.max.ru/uploads").mock(
        return_value=httpx.Response(200, json={
            "url": "https://upload.max.ru/vid",
            "token": "video_token_456",
        })
    )
    respx.post("https://upload.max.ru/vid").mock(
        return_value=httpx.Response(200, json={})
    )

    from maxio import Bot
    from maxio.enums import UploadType

    bot = Bot("TOKEN")
    token = await bot.upload(b"fake_video_data", UploadType.VIDEO, filename="video.mp4")
    assert token == "video_token_456"
    await bot.aclose()
