from __future__ import annotations

from typing import Any

from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.update import UpdateList


class GetUpdates(MaxMethod[UpdateList]):
    """Long-poll the API for new updates."""

    limit: int = 100
    timeout: int = 30
    marker: int | None = None
    types: list[str] | None = None

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="GET",
            api_path="/updates",
            params={
                "limit": self.limit,
                "timeout": self.timeout,
                "marker": self.marker,
                "types": ",".join(self.types) if self.types else None,
            },
        )

    def parse_response(self, data: Any) -> UpdateList:
        return UpdateList.model_validate(data)
