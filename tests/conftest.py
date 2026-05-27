from __future__ import annotations

from typing import Any


def message_payload(text: str = "привет", chat_id: int | None = 10) -> dict[str, Any]:
    return {
        "recipient": {"chat_id": chat_id, "chat_type": "chat", "user_id": None},
        "timestamp": 123,
        "sender": {"user_id": 5, "first_name": "Иван", "is_bot": False},
        "body": {"mid": "mid-1", "seq": 1, "text": text, "attachments": None},
    }


def message_created(text: str = "привет", chat_id: int | None = 10) -> dict[str, Any]:
    return {
        "update_type": "message_created",
        "timestamp": 123,
        "message": message_payload(text, chat_id),
    }


def message_callback(payload: str = "ping") -> dict[str, Any]:
    return {
        "update_type": "message_callback",
        "timestamp": 1,
        "callback": {
            "callback_id": "cb-1",
            "payload": payload,
            "timestamp": 1,
            "user": {"user_id": 5, "first_name": "Иван", "is_bot": False},
        },
        "message": message_payload("кнопка"),
    }
