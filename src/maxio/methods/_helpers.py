from __future__ import annotations

from typing import TYPE_CHECKING, Any

from maxio.enums import TextFormat
from maxio.types.message import NewMessageLink

if TYPE_CHECKING:
    from maxio.keyboards import InlineKeyboard


def normalize_attachments(
    attachments: list[Any] | None,
    keyboard: InlineKeyboard | None,
) -> list[dict[str, Any]] | None:
    """Merge attachment list and keyboard into a single API attachment list."""
    result: list[dict[str, Any]] = []
    for item in attachments or []:
        result.append(item.as_attachment() if hasattr(item, "as_attachment") else item)
    if keyboard is not None:
        result.append(keyboard.as_attachment())
    return result or None


def message_body(
    text: str | None,
    attachments: list[dict[str, Any]] | None,
    link: NewMessageLink | None,
    notify: bool,
    format: TextFormat | str | None,
) -> dict[str, Any]:
    """Build the JSON body for send/edit message requests."""
    body: dict[str, Any] = {"notify": notify}
    if text is not None:
        body["text"] = text
    if attachments is not None:
        body["attachments"] = attachments
    if link is not None:
        body["link"] = link.model_dump()
    if format is not None:
        body["format"] = str(format)
    return body
