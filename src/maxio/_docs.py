from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Doc:
    """Short documentation metadata for ``typing.Annotated`` parameters."""

    text: str
