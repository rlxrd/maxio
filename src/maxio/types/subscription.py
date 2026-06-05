from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Subscription(BaseModel):
    """Webhook subscription record."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    url: str
    time: int | None = None
    update_types: list[str] | None = None
    version: str | None = None


class SubscriptionList(BaseModel):
    """Response wrapper for ``GET /subscriptions``."""

    model_config = ConfigDict(extra="allow")

    subscriptions: list[Subscription] = []
