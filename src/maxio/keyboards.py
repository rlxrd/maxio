from __future__ import annotations

from typing import Any

from maxio.enums import ButtonType, Intent

ButtonDict = dict[str, Any]


class Button:
    """Фабрики inline-кнопок. Каждый метод возвращает готовый dict для API."""

    @staticmethod
    def callback(
        text: str,
        payload: str,
        *,
        intent: Intent | str = Intent.DEFAULT,
    ) -> ButtonDict:
        return {
            "type": ButtonType.CALLBACK.value,
            "text": text,
            "payload": payload,
            "intent": str(intent),
        }

    @staticmethod
    def link(text: str, url: str) -> ButtonDict:
        return {"type": ButtonType.LINK.value, "text": text, "url": url}

    @staticmethod
    def request_contact(text: str) -> ButtonDict:
        return {"type": ButtonType.REQUEST_CONTACT.value, "text": text}

    @staticmethod
    def request_geo_location(text: str, *, quick: bool = False) -> ButtonDict:
        return {
            "type": ButtonType.REQUEST_GEO_LOCATION.value,
            "text": text,
            "quick": quick,
        }

    @staticmethod
    def message(text: str) -> ButtonDict:
        return {"type": ButtonType.MESSAGE.value, "text": text}

    @staticmethod
    def chat(
        text: str,
        chat_title: str,
        *,
        chat_description: str | None = None,
        start_payload: str | None = None,
    ) -> ButtonDict:
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
    """Билдер inline-клавиатуры. Преобразуется в attachment типа inline_keyboard."""

    def __init__(self) -> None:
        self._rows: list[list[ButtonDict]] = []

    def row(self, *buttons: ButtonDict) -> InlineKeyboard:
        """Добавить новый ряд из переданных кнопок."""
        self._rows.append(list(buttons))
        return self

    def add(self, *buttons: ButtonDict) -> InlineKeyboard:
        """Добавить кнопки в последний ряд (создаёт ряд, если его нет)."""
        if not self._rows:
            self._rows.append([])
        self._rows[-1].extend(buttons)
        return self

    def as_attachment(self) -> ButtonDict:
        return {
            "type": "inline_keyboard",
            "payload": {"buttons": self._rows},
        }
