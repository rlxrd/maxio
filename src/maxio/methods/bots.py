from __future__ import annotations

from typing import Any

from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.user import BotInfo


class GetMe(MaxMethod[BotInfo]):
    """Fetch information about the bot itself."""

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path="/me")

    def parse_response(self, data: Any) -> BotInfo:
        return BotInfo.model_validate(data)
