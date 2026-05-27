from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Attachment(BaseModel):
    """Обобщённое входящее вложение. Конкретные поля payload зависят от `type`
    и доступны через `model_extra` (extra='allow')."""

    model_config = ConfigDict(extra="allow")

    type: str
    payload: dict[str, Any] | None = None
