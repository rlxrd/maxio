from __future__ import annotations

from pathlib import Path
from typing import IO, Annotated, Any, TypeVar

import httpx

from maxio._docs import Doc
from maxio._logging import install_token_masking
from maxio.enums import ChatAction, TextFormat, UploadType
from maxio.exceptions import MaxApiError, MaxError
from maxio.keyboards import InlineKeyboard
from maxio.methods import (
    AddChatAdmin,
    AddChatMembers,
    AnswerCallback,
    DeleteChat,
    DeleteMessage,
    EditMessage,
    GetBotChatMembership,
    GetChat,
    GetChatAdmins,
    GetChatMembers,
    GetChats,
    GetMe,
    GetMessage,
    GetMessages,
    GetPinnedMessage,
    GetSubscriptions,
    GetUpdates,
    GetVideoInfo,
    LeaveChat,
    MaxMethod,
    PinMessage,
    RemoveChatAdmin,
    RemoveChatMember,
    SendChatAction,
    SendMessage,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UpdateChat,
)
from maxio.types.chat import Chat
from maxio.types.member import ChatMember, ChatMemberList
from maxio.types.message import Message, NewMessageLink
from maxio.types.subscription import Subscription, SubscriptionList
from maxio.types.update import UpdateList
from maxio.types.user import BotInfo
from maxio.types.video import VideoInfo

T = TypeVar("T")

DEFAULT_BASE_URL = "https://botapi.max.ru"


class Bot:
    """Async MAX Bot API client built on top of httpx.

    Acts as the executor for :class:`~maxio.methods.base.MaxMethod` instances.
    Each high-level method (``send_message``, ``edit_message``, …) constructs
    the corresponding method object and delegates to :meth:`__call__`.

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

    async def __call__(self, method: MaxMethod[T]) -> T:
        """Execute a :class:`~maxio.methods.base.MaxMethod` and return the parsed result."""
        req = method.build_request()
        data = await self._request(
            req.http_method,
            req.api_path,
            params=req.params,
            json=req.json_body,
        )
        return method.parse_response(data)

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
        return await self(GetMe())

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
        return await self(SendMessage(
            text=text,
            chat_id=chat_id,
            user_id=user_id,
            attachments=attachments,
            keyboard=keyboard,
            link=link,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        ))

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
        return await self(EditMessage(
            message_id=message_id,
            text=text,
            attachments=attachments,
            keyboard=keyboard,
            link=link,
            notify=notify,
            format=format,
        ))

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message by its ID. Returns ``True`` on success."""
        return await self(DeleteMessage(message_id=message_id))

    async def get_message(self, message_id: str) -> Message:
        """Fetch a single message by its ID."""
        return await self(GetMessage(message_id=message_id))

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
        return await self(GetMessages(
            chat_id=chat_id,
            message_ids=message_ids,
            from_time=from_time,
            to_time=to_time,
            count=count,
        ))

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
        return await self(AnswerCallback(
            callback_id=callback_id,
            notification=notification,
            text=text,
            attachments=attachments,
            keyboard=keyboard,
            format=format,
        ))

    async def get_chats(
        self,
        *,
        count: int = 50,
        marker: int | None = None,
    ) -> list[Chat]:
        """Return a list of chats the bot participates in."""
        return await self(GetChats(count=count, marker=marker))

    async def get_chat(self, chat_id: int) -> Chat:
        """Get details of a specific chat."""
        return await self(GetChat(chat_id=chat_id))

    async def update_chat(
        self,
        chat_id: int,
        *,
        title: str | None = None,
        icon: dict[str, Any] | None = None,
        notify: bool | None = None,
    ) -> Chat:
        """Update chat title, icon or notification settings."""
        return await self(UpdateChat(chat_id=chat_id, title=title, icon=icon, notify=notify))

    async def delete_chat(self, chat_id: int) -> bool:
        """Delete a group chat. Returns ``True`` on success."""
        return await self(DeleteChat(chat_id=chat_id))

    async def send_chat_action(
        self,
        chat_id: int,
        action: ChatAction | str,
    ) -> bool:
        """Send a typing/activity indicator to a chat."""
        return await self(SendChatAction(chat_id=chat_id, action=action))

    async def get_pinned_message(self, chat_id: int) -> Message | None:
        """Return the pinned message in a chat, or ``None`` if not set."""
        return await self(GetPinnedMessage(chat_id=chat_id))

    async def pin_message(
        self,
        chat_id: int,
        message_id: str,
        *,
        notify: bool = True,
    ) -> bool:
        """Pin a message in a chat."""
        return await self(PinMessage(chat_id=chat_id, message_id=message_id, notify=notify))

    async def unpin_message(self, chat_id: int) -> bool:
        """Unpin the pinned message in a chat."""
        return await self(UnpinMessage(chat_id=chat_id))

    async def get_chat_members(
        self,
        chat_id: int,
        *,
        count: int = 50,
        marker: int | None = None,
        user_ids: list[int] | None = None,
    ) -> ChatMemberList:
        """List members of a chat with pagination."""
        return await self(GetChatMembers(
            chat_id=chat_id, count=count, marker=marker, user_ids=user_ids
        ))

    async def add_chat_members(self, chat_id: int, user_ids: list[int]) -> bool:
        """Add users to a chat."""
        return await self(AddChatMembers(chat_id=chat_id, user_ids=user_ids))

    async def remove_chat_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        block: bool = False,
    ) -> bool:
        """Remove a user from a chat."""
        return await self(RemoveChatMember(chat_id=chat_id, user_id=user_id, block=block))

    async def get_bot_chat_membership(self, chat_id: int) -> ChatMember:
        """Check the bot's own membership status in a chat."""
        return await self(GetBotChatMembership(chat_id=chat_id))

    async def leave_chat(self, chat_id: int) -> bool:
        """Remove the bot from a chat."""
        return await self(LeaveChat(chat_id=chat_id))

    async def get_chat_admins(self, chat_id: int) -> list[ChatMember]:
        """List administrators of a chat."""
        return await self(GetChatAdmins(chat_id=chat_id))

    async def add_chat_admin(self, chat_id: int, user_id: int) -> bool:
        """Grant admin rights to a chat member."""
        return await self(AddChatAdmin(chat_id=chat_id, user_id=user_id))

    async def remove_chat_admin(self, chat_id: int, user_id: int) -> bool:
        """Revoke admin rights from a chat member."""
        return await self(RemoveChatAdmin(chat_id=chat_id, user_id=user_id))

    async def get_subscriptions(self) -> SubscriptionList:
        """List all active webhook subscriptions."""
        return await self(GetSubscriptions())

    async def subscribe(
        self,
        url: str,
        *,
        update_types: list[str] | None = None,
        version: str | None = None,
    ) -> Subscription:
        """Subscribe to bot events via webhook."""
        return await self(Subscribe(url=url, update_types=update_types, version=version))

    async def unsubscribe(self, url: str) -> bool:
        """Remove a webhook subscription by URL."""
        return await self(Unsubscribe(url=url))

    async def get_video_info(self, video_token: str) -> VideoInfo:
        """Fetch metadata for an uploaded video."""
        return await self(GetVideoInfo(video_token=video_token))

    async def get_updates(
        self,
        *,
        limit: int = 100,
        timeout: int = 30,
        marker: int | None = None,
        types: list[str] | None = None,
    ) -> UpdateList:
        """Long-poll the API for new updates."""
        return await self(GetUpdates(limit=limit, timeout=timeout, marker=marker, types=types))

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
