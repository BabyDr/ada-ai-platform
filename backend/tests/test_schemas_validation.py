"""Pydantic 任务参数校验测试（#1 #11 #12 #40）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from adaworks.api.schemas import TaskCreateRequest
from adaworks.api.validators import MAX_CHARS, sanitize_upstream_message, validate_text


def test_validate_text_rejects_control_char() -> None:
    with pytest.raises(ValueError, match="control characters"):
        validate_text("hello\x00world")


def test_validate_text_rejects_empty() -> None:
    with pytest.raises(ValueError, match="required"):
        validate_text("   ")


def test_validate_text_rejects_too_long() -> None:
    with pytest.raises(ValueError, match="maximum length"):
        validate_text("x" * (MAX_CHARS + 1))


def test_task_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate(
            {"type": "translate", "params": {"text": "hi"}, "systemPrompt": "evil"},
        )


def test_invalid_tone_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate(
            {"type": "translate", "params": {"text": "hi", "tone": "Evil"}},
        )


def test_invalid_key_points_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate(
            {"type": "summarize", "params": {"text": "hi", "keyPointsCount": 99}},
        )


def test_invalid_source_lang_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate(
            {"type": "translate", "params": {"text": "hi", "sourceLang": "xx-invalid"}},
        )


def test_summarize_defaults_key_points_to_three() -> None:
    req = TaskCreateRequest.model_validate({"type": "summarize", "params": {"text": "hello"}})
    assert req.params["keyPointsCount"] == 3


def test_sanitize_upstream_hides_auth_errors() -> None:
    msg = sanitize_upstream_message(401, "Invalid API key sk-abcdefghijklmnop")
    assert "sk-" not in msg
    assert "配置" in msg
