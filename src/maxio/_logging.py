from __future__ import annotations

import logging
import re

# access_token=<токен> в query и Authorization: <токен> в заголовках.
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


class TokenMaskingFilter(logging.Filter):
    """Прячет токен (`access_token=...`, `Authorization: ...`) в записях лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _mask(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: _mask(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            else:
                record.args = tuple(
                    _mask(a) if isinstance(a, str) else a for a in record.args
                )
        return True


def install_token_masking(logger_name: str = "httpx") -> None:
    """Однократно повесить маскирующий фильтр на указанный логгер."""
    logger = logging.getLogger(logger_name)
    if any(getattr(f, _FILTER_FLAG, False) for f in logger.filters):
        return
    flt = TokenMaskingFilter()
    setattr(flt, _FILTER_FLAG, True)
    logger.addFilter(flt)
