"""Prompt 构建：翻译含目标语言，总结含要点数。"""

from __future__ import annotations

from adaagent.services.prompt import build_summarize_messages, build_translate_messages


def test_translate_prompt_has_target_lang() -> None:
    system, user = build_translate_messages("Hello", "en", "zh", "Professional")
    assert "Chinese (Simplified)" in system
    assert "Professional" in system
    assert user == "Hello"


def test_summarize_prompt_has_counts() -> None:
    system, user = build_summarize_messages("long text", key_points_count=3, word_limit=120, tone="Technical")
    assert "3 key points" in system or "exactly 3" in user
    assert "120 words" in system
    assert "long text" in user
