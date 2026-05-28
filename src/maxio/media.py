from __future__ import annotations

from typing import Any


def image(token: str) -> dict[str, Any]:
    """Вложение-изображение по токену, полученному через Bot.upload()."""
    return {"type": "image", "payload": {"token": token}}


def video(token: str) -> dict[str, Any]:
    """Вложение-видео по токену, полученному через Bot.upload()."""
    return {"type": "video", "payload": {"token": token}}


def audio(token: str) -> dict[str, Any]:
    """Вложение-аудио по токену, полученному через Bot.upload()."""
    return {"type": "audio", "payload": {"token": token}}


def file(token: str) -> dict[str, Any]:
    """Вложение-файл по токену, полученному через Bot.upload()."""
    return {"type": "file", "payload": {"token": token}}
