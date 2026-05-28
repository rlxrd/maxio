from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PhotoAttachmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    photo_id: int | None = None
    token: str | None = None
    url: str | None = None


class VideoAttachmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    token: str | None = None
    url: str | None = None
    thumbnail: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None


class AudioAttachmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    token: str | None = None
    url: str | None = None
    duration: int | None = None
    transcription: str | None = None


class FileAttachmentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    token: str | None = None
    url: str | None = None
    filename: str | None = None
    size: int | None = None


class Attachment(BaseModel):
    """Входящее вложение. Конкретный payload парсится через as_image/video/audio/file."""

    model_config = ConfigDict(extra="allow")

    type: str
    payload: dict[str, Any] | None = None

    def as_image(self) -> PhotoAttachmentPayload | None:
        if self.type != "image" or self.payload is None:
            return None
        return PhotoAttachmentPayload.model_validate(self.payload)

    def as_video(self) -> VideoAttachmentPayload | None:
        if self.type != "video" or self.payload is None:
            return None
        return VideoAttachmentPayload.model_validate(self.payload)

    def as_audio(self) -> AudioAttachmentPayload | None:
        if self.type != "audio" or self.payload is None:
            return None
        return AudioAttachmentPayload.model_validate(self.payload)

    def as_file(self) -> FileAttachmentPayload | None:
        if self.type != "file" or self.payload is None:
            return None
        return FileAttachmentPayload.model_validate(self.payload)
