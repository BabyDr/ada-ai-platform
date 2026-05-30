"""Prompt 构建：翻译含目标语言，总结含要点数。"""

from __future__ import annotations

from adaworks.services.prompt import build_summarize_messages, build_translate_messages


def test_translate_prompt_has_target_lang() -> None:
    system, user = build_translate_messages("Hello", "en", "zh", "Professional")
    assert "Chinese (Simplified)" in system
    assert "MUST be written entirely in 'Chinese (Simplified)'" in system
    assert "Professional" in system
    assert user == "<source_text>\nHello\n</source_text>"


def test_translate_prompt_same_language_returns_as_is() -> None:
    system, _ = build_translate_messages("风格和他人个天人合一还一塌糊涂呢", "auto", "zh", "Professional")
    assert "return it as-is" in system
    assert "Never output in any other language" in system


def test_summarize_prompt_points_mode() -> None:
    system, user = build_summarize_messages("long text", key_points_count=3, word_limit=120, tone="Technical")
    assert "exactly 3 key points" in system
    assert "120 words each" in user or "120 words" in user
    assert "<source_document>" in user
    assert "long text" in user


def test_summarize_prompt_words_mode() -> None:
    system, user = build_summarize_messages("long text", word_limit=200, tone="Professional", summary_mode="words")
    assert "overview-only" in user
    assert "200 words" in system
    assert "keyPoints" in user and "[]" in user
