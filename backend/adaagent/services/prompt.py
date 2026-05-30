"""
翻译 / 总结 Prompt 构建。

承接 linguist_service 的 system prompt 逻辑（多语言、语调、要点数、字数上限），
但产出 (system, user) 二元组供统一的流式 LLM 调用层使用。
"""

from __future__ import annotations

from adaagent.linguist_service import lang_display


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
2. Maintain technical terms, punctuation, layout, and line breaks where appropriate.
3. If the input is in the target language already, optimize it slightly or return it as-is."""

    return system, text


def build_summarize_messages(
    text: str,
    key_points_count: int = 5,
    word_limit: int = 250,
    tone: str = "Professional",
) -> tuple[str, str]:
    """构建总结的 (system, user)，与 SummarizationView 参数对齐。"""
    system = f"""You are a high-level technical analyst and document compression system.
Summarize the provided content into a cohesive overview and an ordered list of precisely key insights.
Respond strictly in JSON format with keys "overview" (string) and "keyPoints" (array of strings).
Use a '{tone}' style when summarizing. Output must match the text's dominant language.
The overview must be at most {word_limit} words.
Provide exactly {key_points_count} key points in keyPoints."""

    user = f"""Perform summarization under these parameters:
- Key points count: exactly {key_points_count} bullet points.
- Word limit for overview: maximum {word_limit} words.
- Tone style: {tone}

Here is the text to summarize:
{text}

Respond with valid JSON only: {{"overview": "...", "keyPoints": ["...", ...]}}"""

    return system, user
