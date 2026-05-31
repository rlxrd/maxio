from __future__ import annotations


class MaxError(Exception):
    """Base exception for the maxio library."""


class MaxApiError(MaxError):
    """Error returned by the MAX Bot API server."""

    def __init__(
        self,
        status_code: int,
        code: str | None = None,
        message: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        detail = message or code or "unknown error"
        super().__init__(f"[{status_code}] {detail}")
