"""日志敏感信息脱敏（#34）。"""

from __future__ import annotations

import re
from typing import Any

_SK_RE = re.compile(r"sk-[a-zA-Z0-9]{8,}")
_BEARER_RE = re.compile(r"Bearer\s+\S+", re.IGNORECASE)
_COOKIE_RE = re.compile(r"Cookie:\s*\S+", re.IGNORECASE)


def redact_secrets(text: str) -> str:
    """脱敏 API Key / Bearer / Cookie 片段。"""
    out = _SK_RE.sub("[REDACTED]", text)
    out = _BEARER_RE.sub("Bearer [REDACTED]", out)
    out = _COOKIE_RE.sub("Cookie: [REDACTED]", out)
    return out


def sanitize_log_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """对日志写入字段做截断 + 脱敏。"""
    cleaned = dict(payload)
    for key in ("input", "output", "error"):
        if key in cleaned and isinstance(cleaned[key], str):
            cleaned[key] = redact_secrets(cleaned[key][:800 if key != "input" else 500])
    return cleaned
