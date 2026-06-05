from __future__ import annotations

import logging
import re
from typing import Any

_PATTERNS = (
    re.compile(r"(access_token=)[^&\s\"']+"),
    re.compile(r"(Authorization['\"]?\s*[:=]\s*['\"]?)[^\s,'\"}]+", re.IGNORECASE),
)

_REPLACEMENT = r"\g<1>***"

_FILTER_FLAG = "_maxio_token_mask"


def _mask(text: str) -> str:
    for pattern in _PATTERNS:
        text = pattern.sub(_REPLACEMENT, text)
    return text


def _mask_arg(a: Any) -> Any:
    """Mask token in a log argument regardless of its type.

    httpx passes URL objects (not plain str) as log record args — converting
    to str first ensures the token is always redacted.
    """
    if isinstance(a, str):
        return _mask(a)
    s = str(a)
    masked = _mask(s)
    return masked if masked != s else a


class TokenMaskingFilter(logging.Filter):
    """Masks bot token (``access_token=...``, ``Authorization: ...``) in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _mask(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _mask_arg(v) for k, v in record.args.items()}
            else:
                record.args = tuple(_mask_arg(a) for a in record.args)
        return True


def install_token_masking(*logger_names: str) -> None:
    """Attach a token-masking filter to the given loggers (no-op if already installed).

    Defaults to both ``httpx`` and ``httpcore`` so DEBUG-level URL logs are
    also masked.
    """
    for name in logger_names or ("httpx", "httpcore"):
        lg = logging.getLogger(name)
        if any(getattr(f, _FILTER_FLAG, False) for f in lg.filters):
            continue
        flt = TokenMaskingFilter()
        setattr(flt, _FILTER_FLAG, True)
        lg.addFilter(flt)
