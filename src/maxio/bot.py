from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import httpx

from maxio._logging import install_token_masking
from maxio.enums import ChatAction, TextFormat, UploadType
from maxio.exceptions import MaxApiError, MaxError
from maxio.keyboards import InlineKeyboard
from maxio.types.chat import Chat, ChatList
from maxio.types.member import ChatMember, ChatMemberList
from maxio.types.message import Message, MessageList, NewMessageLink, SendMessageResult
from maxio.types.subscription import SubscriptionList
from maxio.types.update import UpdateList
from maxio.types.user import BotInfo
from maxio.types.video import VideoInfo


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


def _message_body(
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


def _success(data: Any) -> bool:
    return bool(data.get("success", True)) if isinstance(data, dict) else True


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

    BASE_URL = "https://platform-api.max.ru"

    def __init__(
        self,
        token: str,
        *,
        timeout: float = 100.0,
    ) -> None:
        self.token = token
        install_token_masking()
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
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
        query = {k: v for k, v in (params or {}).items() if v is not None}
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
        """Send a message to a chat or user.

        Exactly one of ``chat_id`` or ``user_id`` must be provided.
        """
        if chat_id is None and user_id is None:
            raise ValueError("chat_id or user_id is required")
        data = await self._request(
            "POST",
            "/messages",
            params={
                "chat_id": chat_id,
                "user_id": user_id,
                "disable_link_preview": disable_link_preview,
            },
            json=_message_body(
                text,
                _normalize_attachments(attachments, keyboard),
                link,
                notify,
                format,
            ),
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
        """Edit an existing message. Returns ``True`` on success."""
        data = await self._request(
            "PUT",
            "/messages",
            params={"message_id": message_id},
            json=_message_body(
                text,
                _normalize_attachments(attachments, keyboard),
                link,
                notify,
                format,
            ),
        )
        return _success(data)

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message by its ID. Returns ``True`` on success."""
        data = await self._request("DELETE", "/messages", params={"message_id": message_id})
        return _success(data)

    async def get_message(self, message_id: str) -> Message:
        """Fetch a single message by its ID."""
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
        callback_id: str,
        *,
        notification: str | None = None,
        text: str | None = None,
        attachments: list[Any] | None = None,
        keyboard: InlineKeyboard | None = None,
        format: TextFormat | str | None = None,
    ) -> bool:
        """Answer an inline button callback. Returns ``True`` on success."""
        body: dict[str, Any] = {}
        if notification is not None:
            body["notification"] = notification
        message_attachments = _normalize_attachments(attachments, keyboard)
        if text is not None or message_attachments is not None:
            body["message"] = _message_body(text, message_attachments, None, True, format)
        data = await self._request(
            "POST", "/answers", params={"callback_id": callback_id}, json=body
        )
        return _success(data)

    async def get_chats(
        self,
        *,
        count: int = 50,
        marker: int | None = None,
    ) -> ChatList:
        """Return a paginated list of chats the bot participates in."""
        data = await self._request("GET", "/chats", params={"count": count, "marker": marker})
        return ChatList.model_validate(data if isinstance(data, dict) else {})

    async def get_chat(self, chat_id: int) -> Chat:
        """Get details of a specific chat."""
        data = await self._request("GET", f"/chats/{chat_id}")
        return Chat.model_validate(data)

    async def update_chat(
        self,
        chat_id: int,
        *,
        title: str | None = None,
        icon: dict[str, Any] | None = None,
        notify: bool | None = None,
    ) -> Chat:
        """Update chat title, icon or notification settings."""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if icon is not None:
            body["icon"] = icon
        if notify is not None:
            body["notify"] = notify
        data = await self._request("PATCH", f"/chats/{chat_id}", json=body)
        return Chat.model_validate(data)

    async def delete_chat(self, chat_id: int) -> bool:
        """Delete a group chat. Returns ``True`` on success."""
        data = await self._request("DELETE", f"/chats/{chat_id}")
        return _success(data)

    async def send_chat_action(
        self,
        chat_id: int,
        action: ChatAction | str,
    ) -> bool:
        """Send a typing/activity indicator to a chat."""
        data = await self._request(
            "POST", f"/chats/{chat_id}/actions", json={"action": str(action)}
        )
        return _success(data)

    async def get_pinned_message(self, chat_id: int) -> Message | None:
        """Return the pinned message in a chat, or ``None`` if not set."""
        data = await self._request("GET", f"/chats/{chat_id}/pin")
        if not isinstance(data, dict) or data.get("message") is None:
            return None
        return Message.model_validate(data["message"])

    async def pin_message(
        self,
        chat_id: int,
        message_id: str,
        *,
        notify: bool = True,
    ) -> bool:
        """Pin a message in a chat."""
        data = await self._request(
            "PUT",
            f"/chats/{chat_id}/pin",
            json={"message_id": message_id, "notify": notify},
        )
        return _success(data)

    async def unpin_message(self, chat_id: int) -> bool:
        """Unpin the pinned message in a chat."""
        data = await self._request("DELETE", f"/chats/{chat_id}/pin")
        return _success(data)

    async def get_chat_members(
        self,
        chat_id: int,
        *,
        count: int = 50,
        marker: int | None = None,
        user_ids: list[int] | None = None,
    ) -> ChatMemberList:
        """List members of a chat with pagination."""
        data = await self._request(
            "GET",
            f"/chats/{chat_id}/members",
            params={
                "count": count,
                "marker": marker,
                "user_ids": ",".join(str(i) for i in user_ids) if user_ids else None,
            },
        )
        return ChatMemberList.model_validate(data)

    async def add_chat_members(self, chat_id: int, user_ids: list[int]) -> bool:
        """Add users to a chat."""
        data = await self._request(
            "POST",
            f"/chats/{chat_id}/members",
            json={"user_ids": user_ids},
        )
        return _success(data)

    async def remove_chat_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        block: bool = False,
    ) -> bool:
        """Remove a user from a chat."""
        data = await self._request(
            "DELETE",
            f"/chats/{chat_id}/members",
            params={"user_id": user_id, "block": block},
        )
        return _success(data)

    async def get_bot_chat_membership(self, chat_id: int) -> ChatMember:
        """Check the bot's own membership status in a chat."""
        data = await self._request("GET", f"/chats/{chat_id}/members/me")
        return ChatMember.model_validate(data)

    async def leave_chat(self, chat_id: int) -> bool:
        """Remove the bot from a chat."""
        data = await self._request("DELETE", f"/chats/{chat_id}/members/me")
        return _success(data)

    async def get_chat_admins(
        self,
        chat_id: int,
        *,
        count: int = 50,
        marker: int | None = None,
    ) -> list[ChatMember]:
        """List administrators of a chat."""
        data = await self._request(
            "GET",
            f"/chats/{chat_id}/members/admins",
            params={"count": count, "marker": marker},
        )
        members = data.get("members", []) if isinstance(data, dict) else []
        return [ChatMember.model_validate(m) for m in members]

    async def get_chat_by_link(self, chat_link: str) -> Chat:
        """Get chat or channel info by its public link (e.g. ``@channelname``)."""
        data = await self._request("GET", f"/chats/{chat_link}")
        return Chat.model_validate(data)

    async def add_chat_admin(
        self,
        chat_id: int,
        user_id: int,
        *,
        permissions: list[str] | None = None,
    ) -> bool:
        """Grant admin rights to a chat member."""
        admin: dict[str, Any] = {"user_id": user_id}
        if permissions is not None:
            admin["permissions"] = permissions
        data = await self._request(
            "POST",
            f"/chats/{chat_id}/members/admins",
            json={"admins": [admin]},
        )
        return _success(data)

    async def remove_chat_admin(self, chat_id: int, user_id: int) -> bool:
        """Revoke admin rights from a chat member."""
        data = await self._request("DELETE", f"/chats/{chat_id}/members/admins/{user_id}")
        return _success(data)

    async def get_subscriptions(self) -> SubscriptionList:
        """List all active webhook subscriptions."""
        data = await self._request("GET", "/subscriptions")
        return SubscriptionList.model_validate(data)

    async def subscribe(
        self,
        url: str,
        *,
        update_types: list[str] | None = None,
        version: str | None = None,
        secret: str | None = None,
    ) -> bool:
        """Subscribe to bot events via webhook. Returns ``True`` on success."""
        body: dict[str, Any] = {"url": url}
        if update_types is not None:
            body["update_types"] = update_types
        if version is not None:
            body["version"] = version
        if secret is not None:
            body["secret"] = secret
        data = await self._request("POST", "/subscriptions", json=body)
        return _success(data)

    async def unsubscribe(self, url: str) -> bool:
        """Remove a webhook subscription by URL."""
        data = await self._request("DELETE", "/subscriptions", params={"url": url})
        return _success(data)

    async def get_video_info(self, video_token: str) -> VideoInfo:
        """Fetch metadata for an uploaded video."""
        data = await self._request("GET", f"/videos/{video_token}")
        return VideoInfo.model_validate(data)

    async def get_updates(
        self,
        *,
        limit: int = 100,
        timeout: int = 30,
        marker: int | None = None,
        types: list[str] | None = None,
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
        file: bytes | IO[bytes] | Path,
        upload_type: UploadType | str,
        *,
        filename: str | None = None,
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

        endpoint = await self._request("POST", "/uploads", params={"type": str(upload_type)})
        if not isinstance(endpoint, dict) or "url" not in endpoint:
            raise MaxError("Failed to get upload URL")
        upload_url: str = endpoint["url"]
        token_from_endpoint: str | None = endpoint.get("token")

        response = await self._client.post(upload_url, files={"data": (fname, file_data)})
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
