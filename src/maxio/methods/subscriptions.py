from __future__ import annotations

from typing import Any

from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.subscription import SubscriptionList


class GetSubscriptions(MaxMethod[SubscriptionList]):
    """List all active webhook subscriptions."""

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path="/subscriptions")

    def parse_response(self, data: Any) -> SubscriptionList:
        return SubscriptionList.model_validate(data)


class Subscribe(MaxMethod[bool]):
    """Subscribe to bot events via webhook.

    The ``url`` must be publicly accessible over HTTPS.
    POST /subscriptions returns ``{"success": true}`` on success.
    """

    url: str
    update_types: list[str] | None = None
    version: str | None = None
    secret: str | None = None

    def build_request(self) -> MaxRequest:
        body: dict[str, Any] = {"url": self.url}
        if self.update_types is not None:
            body["update_types"] = self.update_types
        if self.version is not None:
            body["version"] = self.version
        if self.secret is not None:
            body["secret"] = self.secret
        return MaxRequest(http_method="POST", api_path="/subscriptions", json_body=body)

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True


class Unsubscribe(MaxMethod[bool]):
    """Remove a webhook subscription by URL."""

    url: str

    def build_request(self) -> MaxRequest:
        return MaxRequest(
            http_method="DELETE",
            api_path="/subscriptions",
            params={"url": self.url},
        )

    def parse_response(self, data: Any) -> bool:
        return bool(data.get("success", True)) if isinstance(data, dict) else True
