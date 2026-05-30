"""任务输入校验：长度、控制字符、token 估算、上游错误文案脱敏。"""

from __future__ import annotations

import re
import unicodedata

MAX_CHARS = 50_000
MAX_TOKENS = 8_000

# C0/C1 控制字符（保留 \t \n \r）
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_SECRET_RE = re.compile(r"sk-[a-zA-Z0-9]{8,}")


def normalize_text(text: str) -> str:
    """Unicode NFC 规范化。"""
    return unicodedata.normalize("NFC", text)


def validate_text(text: str) -> str:
    """
    校验并规范化用户文本。

    Raises:
        ValueError: 空文本、超长、含非法控制字符。
    """
    normalized = normalize_text(text)
    if not normalized.strip():
        raise ValueError("params.text is required")
    if len(normalized) > MAX_CHARS:
        raise ValueError(f"params.text exceeds maximum length of {MAX_CHARS} characters")
    if _CONTROL_CHAR_RE.search(normalized):
        raise ValueError("params.text contains invalid control characters")
    if estimate_tokens(normalized) > MAX_TOKENS:
        raise ValueError(f"params.text exceeds estimated token limit of {MAX_TOKENS}")
    return normalized


def estimate_tokens(text: str) -> int:
    """粗估 token 数（无 tiktoken 时 len/4）。"""
    return max(1, len(text) // 4)


def sanitize_upstream_message(status_code: int, body: str = "") -> str:
    """上游 LLM 错误 → 用户可读文案，不含 Key 片段（#39）。"""
    safe_body = _SECRET_RE.sub("[REDACTED]", body[:200])
    if status_code in (401, 403):
        return "模型服务不可用，请检查配置"
    if status_code in (429, 502, 503):
        return "服务繁忙，请稍后重试"
    if safe_body and len(safe_body) < 120 and "REDACTED" not in safe_body:
        return "模型服务异常，请稍后重试"
    return "模型服务异常，请稍后重试"
