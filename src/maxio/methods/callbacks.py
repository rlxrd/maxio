from __future__ import annotations

from typing import Any

from maxio.enums import TextFormat
from maxio.keyboards import InlineKeyboard
from maxio.methods._helpers import message_body, normalize_attachments
from maxio.methods.base import MaxMethod, MaxRequest


class AnswerCallback(MaxMethod[bool]):
    """Answer an inline button callback."""

    callback_id: str
    notification: str | None = None
    text: str | None = None
    attachments: list[Any] | None = None
    keyboard: InlineKeyboard | None = None
    format: TextFormat | str | None = None

    def build_request(self) -> MaxRequest:
        body: dict[str, Any] = {}
        if self.notification is not None:
            body["notification"] = self.notification
        atts = normalize_attachments(self.attachments, self.keyboard)
        if self.text is not None or atts is not None:
            body["message"] = message_body(self.text, atts, None, True, self.format)
        return MaxRequest(
            http_method="POST",
            api_path="/answers",
            params={"callback_id": self.callback_id},
            json_body=body,
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True
