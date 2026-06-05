from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VideoInfo(BaseModel):
    """Metadata for an uploaded video returned by ``GET /videos/{videoToken}``."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    token: str | None = None
    urls: dict[str, str] | None = None
    thumbnail: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
