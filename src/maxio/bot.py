from __future__ import annotations

from typing import Any

import httpx

from maxio._logging import install_token_masking
from maxio.enums import TextFormat
from maxio.exceptions import MaxApiError
from maxio.keyboards import InlineKeyboard
from maxio.types.chat import Chat
from maxio.types.message import (
    Message,
    MessageList,
    NewMessageLink,
    SendMessageResult,
)
from maxio.types.update import UpdateList
from maxio.types.user import BotInfo

DEFAULT_BASE_URL = "https://botapi.max.ru"


def _normalize_attachments(
    attachments: list[Any] | None,
    keyboard: InlineKeyboard | None,
) -> list[dict[str, Any]] | None:
    result: list[dict[str, Any]] = []
    for item in attachments or []:
        result.append(item.as_attachment() if hasattr(item, "as_attachment") else item)
    if keyboard is not None:
        result.append(keyboard.as_attachment())
    return result or None


def _new_message_body(
    text: str | None,
    attachments: list[dict[str, Any]] | None,
    link: NewMessageLink | None,
    notify: bool,
    format: TextFormat | str | None,
) -> dict[str, Any]:
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


class Bot:
    """Асинхронный клиент MAX Bot API поверх httpx."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 100.0,
        client: httpx.AsyncClient | None = None,
        mask_token_in_logs: bool = True,
    ) -> None:
        self.token = token
        if mask_token_in_logs:
            install_token_masking()
        self._client = client or httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": token},
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        query = {"access_token": self.token}
        if params:
            query.update({k: v for k, v in params.items() if v is not None})
        response = await self._client.request(method, path, params=query, json=json)
        try:
            data = response.json()
        except ValueError:
            data = None
        if response.status_code >= 400:
            code = message = None
            if isinstance(data, dict):
                code = data.get("code")
                message = data.get("message") or data.get("error")
            raise MaxApiError(response.status_code, code, message)
        return data

    # --- bots ---

    async def get_me(self) -> BotInfo:
        data = await self._request("GET", "/me")
        return BotInfo.model_validate(data)

    # --- messages ---

    async def send_message(
        self,
        text: str | None = None,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        link: NewMessageLink | None = None,
        notify: bool = True,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> Message:
        if chat_id is None and user_id is None:
            raise ValueError("Нужно указать chat_id или user_id")
        body = _new_message_body(
            text,
            _normalize_attachments(attachments, keyboard),
            link,
            notify,
            format,
        )
        data = await self._request(
            "POST",
            "/messages",
            params={
                "chat_id": chat_id,
                "user_id": user_id,
                "disable_link_preview": disable_link_preview,
            },
            json=body,
        )
        return SendMessageResult.model_validate(data).message

    async def edit_message(
        self,
        message_id: str,
        text: str | None = None,
        *,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        link: NewMessageLink | None = None,
        notify: bool = True,
        format: TextFormat | str | None = None,
    ) -> bool:
        body = _new_message_body(
            text,
            _normalize_attachments(attachments, keyboard),
            link,
            notify,
            format,
        )
        data = await self._request(
            "PUT", "/messages", params={"message_id": message_id}, json=body
        )
        return bool(data.get("success", True)) if isinstance(data, dict) else True

    async def delete_message(self, message_id: str) -> bool:
        data = await self._request("DELETE", "/messages", params={"message_id": message_id})
        return bool(data.get("success", True)) if isinstance(data, dict) else True

    async def get_message(self, message_id: str) -> Message:
        data = await self._request("GET", f"/messages/{message_id}")
        return Message.model_validate(data)

    async def get_messages(
        self,
        *,
        chat_id: int | None = None,
        message_ids: list[str] | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        count: int = 50,
    ) -> list[Message]:
        data = await self._request(
            "GET",
            "/messages",
            params={
                "chat_id": chat_id,
                "message_ids": ",".join(message_ids) if message_ids else None,
                "from": from_time,
                "to": to_time,
                "count": count,
            },
        )
        return MessageList.model_validate(data).messages

    async def answer_callback(
        self,
        callback_id: str,
        *,
        notification: str | None = None,
        text: str | None = None,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        format: TextFormat | str | None = None,
    ) -> bool:
        body: dict[str, Any] = {}
        if notification is not None:
            body["notification"] = notification
        message_attachments = _normalize_attachments(attachments, keyboard)
        if text is not None or message_attachments is not None:
            body["message"] = _new_message_body(text, message_attachments, None, True, format)
        data = await self._request(
            "POST", "/answers", params={"callback_id": callback_id}, json=body
        )
        return bool(data.get("success", True)) if isinstance(data, dict) else True

    # --- chats ---

    async def get_chats(self, *, count: int = 50, marker: int | None = None) -> list[Chat]:
        data = await self._request("GET", "/chats", params={"count": count, "marker": marker})
        chats = data.get("chats", []) if isinstance(data, dict) else []
        return [Chat.model_validate(c) for c in chats]

    # --- updates (long polling) ---

    async def get_updates(
        self,
        *,
        limit: int = 100,
        timeout: int = 30,
        marker: int | None = None,
        types: list[str] | None = None,
    ) -> UpdateList:
        data = await self._request(
            "GET",
            "/updates",
            params={
                "limit": limit,
                "timeout": timeout,
                "marker": marker,
                "types": ",".join(types) if types else None,
            },
        )
        return UpdateList.model_validate(data)

    async def aclose(self) -> None:
        await self._client.aclose()
