from __future__ import annotations

from typing import Any

from maxio.methods.base import MaxMethod, MaxRequest
from maxio.types.video import VideoInfo


class GetVideoInfo(MaxMethod[VideoInfo]):
    """Fetch metadata for an uploaded video by its token."""

    video_token: str

    def build_request(self) -> MaxRequest:
        return MaxRequest(http_method="GET", api_path=f"/videos/{self.video_token}")

    def parse_response(self, data: Any) -> VideoInfo:
        return VideoInfo.model_validate(data)
