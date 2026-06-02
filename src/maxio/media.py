from __future__ import annotations

from typing import Any


def image(token: str) -> dict[str, Any]:
    """Build an image attachment dict from an upload token obtained via ``Bot.upload()``."""
    return {"type": "image", "payload": {"token": token}}


def video(token: str) -> dict[str, Any]:
    """Build a video attachment dict from an upload token obtained via ``Bot.upload()``."""
    return {"type": "video", "payload": {"token": token}}


def audio(token: str) -> dict[str, Any]:
    """Build an audio attachment dict from an upload token obtained via ``Bot.upload()``."""
    return {"type": "audio", "payload": {"token": token}}


def file(token: str) -> dict[str, Any]:
    """Build a file attachment dict from an upload token obtained via ``Bot.upload()``."""
    return {"type": "file", "payload": {"token": token}}
