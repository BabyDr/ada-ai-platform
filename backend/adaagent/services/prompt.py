"""
翻译 / 总结 Prompt 构建。

承接 linguist_service 的 system prompt 逻辑（多语言、语调、要点数、字数上限），
但产出 (system, user) 二元组供统一的流式 LLM 调用层使用。
"""

from __future__ import annotations

from adaagent.linguist_service import lang_display
from adaagent.services.prompt_security import (
    SUMMARIZE_ANTI_INJECTION,
    TRANSLATE_ANTI_INJECTION,
    detect_output_language,
    language_output_rule,
    wrap_source_document,
    wrap_source_text,
)

# 供 summary_parser 等模块沿用
__all__ = [
    "build_translate_messages",
    "build_summarize_messages",
    "detect_output_language",
]


def build_translate_messages(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "zh",
    tone: str = "Professional",
) -> tuple[str, str]:
    """构建多语言翻译的 (system, user)；source_lang 可为 auto。"""
    source_text = lang_display(source_lang) if source_lang != "auto" else "Detect automatically"
    target_text = lang_display(target_lang)

    system = f"""You are a professional linguistic translation engine.
Translate the user input text from '{source_text}' to '{target_text}'.
The tone of translation must be '{tone}'.
Strict rules:
1. Translate only. Do not add any conversational context, meta text, or chat responses.
2. Output MUST be written entirely in '{target_text}'. Never output in any other language.
3. Maintain technical terms, punctuation, layout, and line breaks where appropriate.
4. If the input is already in '{target_text}', return it as-is without translating to another language.
{TRANSLATE_ANTI_INJECTION}"""

    return system, wrap_source_text(text)


def build_summarize_messages(
    text: str,
    key_points_count: int = 3,
    word_limit: int = 250,
    tone: str = "Professional",
    summary_mode: str = "points",
) -> tuple[str, str]:
    """构建总结的 (system, user)，与 SummarizationView 参数对齐。"""
    output_lang = detect_output_language(text)
    lang_rule = language_output_rule(output_lang)
    wrapped = wrap_source_document(text)

    if summary_mode == "words":
        system = f"""You are a high-level technical analyst and document compression system.
Summarize the provided content into a single cohesive overview (no bullet points).
Respond strictly in JSON format with keys "overview" (string) and "keyPoints" (empty array).
Use a '{tone}' style when summarizing.
{lang_rule}
The overview must be at most {word_limit} words.
{SUMMARIZE_ANTI_INJECTION}"""

        user = f"""Perform summarization under these parameters:
- Mode: overview-only summary within a word budget.
- Word limit for overview: maximum {word_limit} words.
- Tone style: {tone}

{wrapped}

Respond with valid JSON only: {{"overview": "...", "keyPoints": []}}"""
        return system, user

    system = f"""You are a high-level technical analyst and document compression system.
Summarize the provided content into a concise overview and an ordered list of key insights.
Respond strictly in JSON format with keys "overview" (string) and "keyPoints" (array of strings).
Use a '{tone}' style when summarizing.
{lang_rule}
Provide exactly {key_points_count} key points in keyPoints.
Each key point must be at most {word_limit} words.
The overview should be a brief lead-in (2–3 sentences).
{SUMMARIZE_ANTI_INJECTION}"""

    user = f"""Perform summarization under these parameters:
- Mode: key points summary.
- Key points count: exactly {key_points_count} bullet points.
- Word limit per key point: maximum {word_limit} words each.
- Tone style: {tone}

{wrapped}

Respond with valid JSON only: {{"overview": "...", "keyPoints": ["...", ...]}}"""

    return system, user
