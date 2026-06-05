from __future__ import annotations

from typing import Any

from maxio.enums import ButtonType, Intent

ButtonDict = dict[str, Any]


class Button:
    """Factory for inline button dicts. Each method returns a ready-to-use dict for the API."""

    @staticmethod
    def callback(
        text: str,
        payload: str,
        *,
        intent: Intent | str = Intent.DEFAULT,
    ) -> ButtonDict:
        """Create a callback button."""
        return {
            "type": ButtonType.CALLBACK.value,
            "text": text,
            "payload": payload,
            "intent": str(intent),
        }

    @staticmethod
    def link(
        text: str,
        url: str,
    ) -> ButtonDict:
        """Create a link button."""
        return {"type": ButtonType.LINK.value, "text": text, "url": url}

    @staticmethod
    def request_contact(
        text: str,
    ) -> ButtonDict:
        """Create a button that requests the user's contact."""
        return {"type": ButtonType.REQUEST_CONTACT.value, "text": text}

    @staticmethod
    def request_geo_location(
        text: str,
        *,
        quick: bool = False,
    ) -> ButtonDict:
        """Create a button that requests the user's geo location."""
        return {
            "type": ButtonType.REQUEST_GEO_LOCATION.value,
            "text": text,
            "quick": quick,
        }

    @staticmethod
    def message(
        text: str,
    ) -> ButtonDict:
        """Create a button that sends a text message when pressed."""
        return {"type": ButtonType.MESSAGE.value, "text": text}

    @staticmethod
    def chat(
        text: str,
        chat_title: str,
        *,
        chat_description: str | None = None,
        start_payload: str | None = None,
    ) -> ButtonDict:
        """Create a button that opens a new chat."""
        button: ButtonDict = {
            "type": ButtonType.CHAT.value,
            "text": text,
            "chat_title": chat_title,
        }
        if chat_description is not None:
            button["chat_description"] = chat_description
        if start_payload is not None:
            button["start_payload"] = start_payload
        return button


class InlineKeyboard:
    """Builder for inline keyboards. Converts to an ``inline_keyboard`` attachment.

    Example:
        ```python
        kb = (
            InlineKeyboard()
            .row(Button.callback("Yes", "yes"), Button.callback("No", "no"))
        )
        await message.answer("Choose:", keyboard=kb)
        ```
    """

    def __init__(self) -> None:
        self._rows: list[list[ButtonDict]] = []

    def row(self, *buttons: ButtonDict) -> InlineKeyboard:
        """Append a new row containing the given buttons."""
        self._rows.append(list(buttons))
        return self

    def add(self, *buttons: ButtonDict) -> InlineKeyboard:
        """Append buttons to the last row (creates a row if none exist)."""
        if not self._rows:
            self._rows.append([])
        self._rows[-1].extend(buttons)
        return self

    def as_attachment(self) -> ButtonDict:
        """Serialize the keyboard as an API attachment dict."""
        return {
            "type": "inline_keyboard",
            "payload": {"buttons": self._rows},
        }
