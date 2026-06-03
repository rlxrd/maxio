from __future__ import annotations

from typing import Any

from maxio.enums import ChatAction
from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.chat import Chat, ChatList
from maxio.types.member import ChatMember, ChatMemberList
from maxio.types.message import Message


class GetChats(MaxMethod[ChatList]):

    count: int = 50
    marker: int | None = None

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="GET",
            api_path="/chats",
            params={"count": self.count, "marker": self.marker},
        )

    def parse_response(self, data: Any) -> ChatList:
        return ChatList.model_validate(data if isinstance(data, dict) else {})


class GetChat(MaxMethod[Chat]):
    """Get details of a specific chat by its ID."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/chats/{self.chat_id}")

    def parse_response(self, data: Any) -> Chat:
        return Chat.model_validate(data)


class UpdateChat(MaxMethod[Chat]):
    """Update group chat information (title, icon, etc.)."""

    chat_id: int
    title: str | None = None
    icon: dict[str, Any] | None = None
    pin: str | None = None
    notify: bool | None = None

    def build_request(self) -> MaxRequest:
        body: dict[str, Any] = {}
        if self.title is not None:
            body["title"] = self.title
        if self.icon is not None:
            body["icon"] = self.icon
        if self.pin is not None:
            body["pin"] = self.pin
        if self.notify is not None:
            body["notify"] = self.notify
        return MaxRequest(
            http_method="PATCH",
            api_path=f"/chats/{self.chat_id}",
            json_body=body,
        )

    def parse_response(self, data: Any) -> Chat:
        return Chat.model_validate(data)


class DeleteChat(MaxMethod[bool]):
    """Delete a group chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="DELETE", api_path=f"/chats/{self.chat_id}")

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class SendChatAction(MaxMethod[bool]):
    """Send a typing or activity indicator to a chat."""

    chat_id: int
    action: ChatAction | str

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="POST",
            api_path=f"/chats/{self.chat_id}/actions",
            json_body={"action": str(self.action)},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class GetPinnedMessage(MaxMethod[Message | None]):
    """Get the pinned message in a chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/chats/{self.chat_id}/pin")

    def parse_response(self, data: Any) -> Message | None:
        if not data:
            return None
        return Message.model_validate(data)


class PinMessage(MaxMethod[bool]):
    """Pin a message in a chat."""

    chat_id: int
    message_id: str
    notify: bool = True

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="PUT",
            api_path=f"/chats/{self.chat_id}/pin",
            json_body={"message_id": self.message_id, "notify": self.notify},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class UnpinMessage(MaxMethod[bool]):
    """Unpin the pinned message in a chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="DELETE", api_path=f"/chats/{self.chat_id}/pin")

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class GetChatMembers(MaxMethod[ChatMemberList]):
    """List members of a chat with pagination."""

    chat_id: int
    count: int = 50
    marker: int | None = None
    user_ids: list[int] | None = None

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="GET",
            api_path=f"/chats/{self.chat_id}/members",
            params={
                "count": self.count,
                "marker": self.marker,
                "user_ids": ",".join(str(i) for i in self.user_ids) if self.user_ids else None,
            },
        )

    def parse_response(self, data: Any) -> ChatMemberList:
        return ChatMemberList.model_validate(data)


class AddChatMembers(MaxMethod[bool]):
    """Add one or more users to a chat."""

    chat_id: int
    user_ids: list[int]

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="POST",
            api_path=f"/chats/{self.chat_id}/members",
            json_body={"user_ids": self.user_ids},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class RemoveChatMember(MaxMethod[bool]):
    """Remove a user from a chat."""

    chat_id: int
    user_id: int
    block: bool = False

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="DELETE",
            api_path=f"/chats/{self.chat_id}/members",
            params={"user_id": self.user_id, "block": self.block},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class GetBotChatMembership(MaxMethod[ChatMember]):
    """Check the bot's own membership status in a chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/chats/{self.chat_id}/members/me")

    def parse_response(self, data: Any) -> ChatMember:
        return ChatMember.model_validate(data)


class LeaveChat(MaxMethod[bool]):
    """Remove the bot from a chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="DELETE", api_path=f"/chats/{self.chat_id}/members/me")

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class GetChatAdmins(MaxMethod[list[ChatMember]]):
    """List administrators of a chat."""

    chat_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/chats/{self.chat_id}/members/admins")

    def parse_response(self, data: Any) -> list[ChatMember]:
        members = data.get("members", []) if isinstance(data, dict) else []
        return [ChatMember.model_validate(m) for m in members]


class AddChatAdmin(MaxMethod[bool]):
    """Grant admin rights to a chat member."""

    chat_id: int
    user_id: int
    permissions: list[str] | None = None

    def build_request(self) -> MaxRequest:
        admin: dict[str, Any] = {"user_id": self.user_id}
        if self.permissions is not None:
            admin["permissions"] = self.permissions
        return MaxRequest(
            http_method="POST",
            api_path=f"/chats/{self.chat_id}/members/admins",
            json_body={"admins": [admin]},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class RemoveChatAdmin(MaxMethod[bool]):
    """Revoke admin rights from a chat member."""

    chat_id: int
    user_id: int

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="DELETE",
            api_path=f"/chats/{self.chat_id}/members/admins/{self.user_id}",
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True
