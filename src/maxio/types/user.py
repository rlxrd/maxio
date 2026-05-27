from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    name: str | None = None
    is_bot: bool = False
    last_activity_time: int | None = None

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts) or self.name or self.username or str(self.user_id)


class BotInfo(User):
    description: str | None = None
    avatar_url: str | None = None
    full_avatar_url: str | None = None
