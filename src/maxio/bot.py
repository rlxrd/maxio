from __future__ import annotations

from pathlib import Path
from typing import IO, Annotated, Any

import httpx
from annotated_doc import Doc

from maxio._logging import install_token_masking
from maxio.enums import TextFormat, UploadType
from maxio.exceptions import MaxApiError, MaxError
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
    """Async MAX Bot API client built on top of httpx.

    Example:
        ```python
        from maxio import Bot

        bot = Bot("your-token")
        await bot.send_message("Hello!", chat_id=12345)
        await bot.aclose()
        ```
    """

    def __init__(
        self,
        token: Annotated[
            str,
            Doc(
                """
                MAX Bot API access token.

                Obtain it from the BotFather in the MAX messenger.
                """
            ),
        ],
        *,
        timeout: Annotated[
            float,
            Doc(
                """
                Default HTTP request timeout in seconds.

                Applied to all API calls. Set this slightly above the long-poll
                ``timeout`` passed to ``get_updates``.
                """
            ),
        ] = 100.0,
        client: Annotated[
            httpx.AsyncClient | None,
            Doc(
                """
                Custom httpx client instead of the default one.

                Useful for injecting a pre-configured or mocked client in tests.
                """
            ),
        ] = None,
        mask_token_in_logs: Annotated[
            bool,
            Doc(
                """
                Replace the token with ``***`` in all log output.

                Enabled by default to prevent accidental token leaks.
                """
            ),
        ] = True,
    ) -> None:
        self.token = token
        if mask_token_in_logs:
            install_token_masking()
        self._client = client or httpx.AsyncClient(
            base_url=DEFAULT_BASE_URL,
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

    async def get_me(self) -> BotInfo:
        """Return information about the bot itself."""
        data = await self._request("GET", "/me")
        return BotInfo.model_validate(data)

    async def send_message(
        self,
        text: Annotated[str | None, Doc("Message text.")] = None,
        *,
        chat_id: Annotated[int | None, Doc("Target chat ID.")] = None,
        user_id: Annotated[int | None, Doc("Target user ID for direct messages.")] = None,
        attachments: Annotated[list[Any] | None, Doc("List of attachment dicts.")] = None,
        keyboard: Annotated[InlineKeyboard | None, Doc("Inline keyboard to attach.")] = None,
        link: Annotated[NewMessageLink | None, Doc("Forward or reply link.")] = None,
        notify: Annotated[bool, Doc("Send a push notification to recipients.")] = True,
        format: Annotated[TextFormat | str | None, Doc("Text markup format.")] = None,
        disable_link_preview: Annotated[bool | None, Doc("Disable link preview.")] = None,
    ) -> Message:
        """Send a message to a chat or user.

        Exactly one of ``chat_id`` or ``user_id`` must be provided.
        """
        if chat_id is None and user_id is None:
            raise ValueError("chat_id or user_id is required")
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
        message_id: Annotated[str, Doc("ID of the message to edit.")],
        text: Annotated[str | None, Doc("New message text.")] = None,
        *,
        attachments: Annotated[list[Any] | None, Doc("New attachment list.")] = None,
        keyboard: Annotated[InlineKeyboard | None, Doc("New inline keyboard.")] = None,
        link: Annotated[NewMessageLink | None, Doc("Forward or reply link.")] = None,
        notify: Annotated[bool, Doc("Send a push notification.")] = True,
        format: Annotated[TextFormat | str | None, Doc("Text markup format.")] = None,
    ) -> bool:
        """Edit an existing message. Returns ``True`` on success."""
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
        """Delete a message by its ID. Returns ``True`` on success."""
        data = await self._request("DELETE", "/messages", params={"message_id": message_id})
        return bool(data.get("success", True)) if isinstance(data, dict) else True

    async def get_message(self, message_id: str) -> Message:
        """Fetch a single message by its ID."""
        data = await self._request("GET", f"/messages/{message_id}")
        return Message.model_validate(data)

    async def get_messages(
        self,
        *,
        chat_id: Annotated[int | None, Doc("Filter by chat ID.")] = None,
        message_ids: Annotated[list[str] | None, Doc("Fetch specific message IDs.")] = None,
        from_time: Annotated[int | None, Doc("Start of time range (Unix ms).")] = None,
        to_time: Annotated[int | None, Doc("End of time range (Unix ms).")] = None,
        count: Annotated[int, Doc("Maximum number of messages to return.")] = 50,
    ) -> list[Message]:
        """Fetch a list of messages from a chat."""
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
        callback_id: Annotated[str, Doc("ID of the callback to answer.")],
        *,
        notification: Annotated[str | None, Doc("Pop-up notification text.")] = None,
        text: Annotated[str | None, Doc("Message text to send with the answer.")] = None,
        attachments: Annotated[list[Any] | None, Doc("Attachments to include.")] = None,
        keyboard: Annotated[InlineKeyboard | None, Doc("Inline keyboard to attach.")] = None,
        format: Annotated[TextFormat | str | None, Doc("Text markup format.")] = None,
    ) -> bool:
        """Answer an inline button callback. Returns ``True`` on success."""
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

    async def get_chats(
        self,
        *,
        count: Annotated[int, Doc("Maximum number of chats to return.")] = 50,
        marker: Annotated[int | None, Doc("Pagination marker from the previous response.")] = None,
    ) -> list[Chat]:
        """Return a list of chats the bot participates in."""
        data = await self._request("GET", "/chats", params={"count": count, "marker": marker})
        chats = data.get("chats", []) if isinstance(data, dict) else []
        return [Chat.model_validate(c) for c in chats]

    async def get_updates(
        self,
        *,
        limit: Annotated[int, Doc("Maximum updates per request.")] = 100,
        timeout: Annotated[int, Doc("Long-poll server timeout in seconds.")] = 30,
        marker: Annotated[int | None, Doc("Sequence marker from the previous response.")] = None,
        types: Annotated[list[str] | None, Doc("Filter by update types.")] = None,
    ) -> UpdateList:
        """Long-poll the API for new updates."""
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

    async def upload(
        self,
        file: Annotated[
            bytes | IO[bytes] | Path,
            Doc("File content as bytes, a file-like object, or a Path."),
        ],
        upload_type: Annotated[
            UploadType | str,
            Doc("Media type: image, video, audio, or file."),
        ],
        *,
        filename: Annotated[
            str | None,
            Doc("Override the filename sent to the server."),
        ] = None,
    ) -> str:
        """Upload a file and return an upload token for use in attachments.

        Two-step process: fetch an upload URL from the API, then POST the file to that URL.
        """
        if isinstance(file, Path):
            file_data: bytes = file.read_bytes()
            fname = filename or file.name
        elif isinstance(file, bytes):
            file_data = file
            fname = filename or "file"
        else:
            file_data = file.read()
            fname = filename or getattr(file, "name", None) or "file"

        endpoint = await self._request(
            "POST", "/uploads", params={"type": str(upload_type)}
        )
        if not isinstance(endpoint, dict) or "url" not in endpoint:
            raise MaxError("Failed to get upload URL")
        upload_url: str = endpoint["url"]
        token_from_endpoint: str | None = endpoint.get("token")

        response = await self._client.post(
            upload_url,
            files={"data": (fname, file_data)},
        )
        try:
            result: Any = response.json()
        except ValueError:
            result = {}
        if response.status_code >= 400:
            raise MaxApiError(response.status_code, None, "File upload failed")

        token: str | None = None
        if isinstance(result, dict):
            token = result.get("token")
        token = token or token_from_endpoint
        if not token:
            raise MaxError("Upload did not return a token")
        return token

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
