from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from maxio.bot import Bot

T = TypeVar("T")


class MaxRequest(BaseModel):
    """Serialized HTTP request produced by a :class:`MaxMethod`."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    http_method: str
    api_path: str
    params: dict[str, Any] | None = None
    json_body: dict[str, Any] | None = None


class MaxMethod(BaseModel, Generic[T]):
    """Base Pydantic model for every MAX Bot API method.

    Subclasses define request fields, implement :meth:`build_request` to
    produce the raw HTTP call, and :meth:`parse_response` to validate the
    API response into the correct return type.

    Example:
        ```python
        result = await SendMessage(text="hi", chat_id=42).emit(bot)
        # or inside a handler (bot injected from context):
        result = await SendMessage(text="hi", chat_id=42)
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def build_request(self) -> MaxRequest:
        """Return the HTTP request data for this method."""
        raise NotImplementedError

    def parse_response(self, data: Any) -> T:  # noqa: ARG002
        """Validate and convert raw API response data into the return type."""
        raise NotImplementedError

    async def emit(self, bot: Bot) -> T:
        """Execute this method using *bot* and return the parsed result."""
        return await bot(self)

    def __await__(self):
        from maxio._runtime import get_current_bot
        return self.emit(get_current_bot()).__await__()
