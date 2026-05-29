"""
Linguist AI 翻译 / 总结服务（智谱 GLM，非流式）。

供 /api/translate、/api/summarize 调用；日志存于进程内内存。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from adaagent.env_secrets import read_first_secret
from adaagent.glm_agent import DEFAULT_GLM_BASE, DEFAULT_GLM_MODEL

# 与 linguist-ai 一致的初始 mock 日志
_SEED_LOGS: list[dict[str, Any]] = [
    {
        "id": "log-1",
        "timestamp": "10:42 AM",
        "date": "Oct 24",
        "type": "translation",
        "input": "Translate user manual from EN to FR, ensuring technical accuracy and clear terminology for machinery operations.",
        "output": "Traduire le manuel d'utilisation de l'anglais vers le français, en garantissant l'exactitude technique et une terminologie claire pour le fonctionnement des machines.",
        "duration": "1.2s",
        "status": "success",
        "details": {"sourceLang": "English", "targetLang": "French", "tone": "Technical"},
    },
    {
        "id": "log-2",
        "timestamp": "09:15 AM",
        "date": "Oct 24",
        "type": "summarization",
        "input": "Project Serene kick-off meeting notes:\n- Standardized 8px margin spacing for visual harmony.\n- Integrated high-vibrancy primary green for interaction feedback.",
        "output": json.dumps(
            {
                "overview": "Standardizing custom design and technical specs of Project Serene including layouts, primary color integration, typography pairing, and backend port settings.",
                "keyPoints": [
                    "Minimalism architecture configured with an 8px technical layout rhythm.",
                    "Interactive indicators rendered dynamically using the high-vibrancy brand green.",
                    "Precision typography pairing Geist (display) with JetBrains Mono (coding data).",
                    "Framework stack standardizes on full-stack React and Express at standard Port 3000.",
                ],
            }
        ),
        "duration": "2.4s",
        "status": "success",
        "details": {"keyPointsCount": 4, "wordLimit": 150, "tone": "Professional"},
    },
    {
        "id": "log-3",
        "timestamp": "08:30 AM",
        "date": "Oct 24",
        "type": "translation",
        "input": "Analyze sentiment of customer feedback batch #4092 regarding the newly deployed translations latency.",
        "output": "Generating response...",
        "duration": "--",
        "status": "processing",
        "details": {"sourceLang": "English", "targetLang": "Chinese (Simplified)", "tone": "Professional"},
    },
    {
        "id": "log-4",
        "timestamp": "Yesterday",
        "date": "Oct 23",
        "type": "translation",
        "input": "Convert legacy codebase comments to modern docstrings...",
        "output": "Error: Input exceeded maximum token limit (8k)...",
        "duration": "0.4s",
        "status": "failed",
        "error": "Input exceeded maximum token limit (8k)",
        "details": {"sourceLang": "Detect Language", "targetLang": "English", "tone": "Technical"},
    },
    {
        "id": "log-5",
        "timestamp": "Yesterday",
        "date": "Oct 23",
        "type": "summarization",
        "input": "Linguist AI Launch Strategy: 1. Target professional localization engineers. 2. Highlight server-side secure credentials.",
        "output": json.dumps(
            {
                "overview": "Launch strategy for Linguist AI emphasizing structural safety, clean visuals, and localized precision.",
                "keyPoints": [
                    "Focus on key localization and translation professionals during early deployment.",
                    "Highlight security advantage of full-stack server-side isolation of credentials.",
                    "Standardize layouts using premium bento container grids to guide focus.",
                ],
            }
        ),
        "duration": "3.1s",
        "status": "success",
        "details": {"keyPointsCount": 3, "wordLimit": 250, "tone": "Conversational"},
    },
]

logs_db: list[dict[str, Any]] = list(_SEED_LOGS)

_LANG_NAMES: dict[str, str] = {
    "auto": "Detect Language",
    "en": "English",
    "zh": "Chinese (Simplified)",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "de": "German",
    "ko": "Korean",
    "ru": "Russian",
    "it": "Italian",
}


def _api_key() -> str | None:
    return read_first_secret("GLM_API_KEY", "ZHIPU_API_KEY")


def _api_base() -> str:
    return (os.environ.get("GLM_API_BASE") or DEFAULT_GLM_BASE).rstrip("/")


def _model_name() -> str:
    return (os.environ.get("GLM_MODEL") or DEFAULT_GLM_MODEL).strip() or DEFAULT_GLM_MODEL


def get_current_time_details() -> dict[str, str]:
    d = time.localtime()
    hours = d.tm_hour
    minutes = d.tm_min
    ampm = "PM" if hours >= 12 else "AM"
    hours = hours % 12 or 12
    min_str = f"{minutes:02d}"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return {"time": f"{hours}:{min_str} {ampm}", "date": f"{months[d.tm_mon - 1]} {d.tm_mday}"}


async def glm_completion(system: str, user: str, *, temperature: float = 0.2) -> str:
    """单次 GLM 对话补全（非流式）。"""
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("GLM_API_KEY 或 ZHIPU_API_KEY 未配置")

    url = f"{_api_base()}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": _model_name(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        r = await client.post(url, headers=headers, json=body)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            err_body = r.text[:800]
            raise RuntimeError(f"GLM HTTP {r.status_code}: {err_body}") from None

        obj = r.json()
        err = obj.get("error")
        if isinstance(err, dict) and err.get("message"):
            raise RuntimeError(str(err.get("message")))

        choices = obj.get("choices") or []
        if not choices:
            raise RuntimeError("GLM 返回空 choices")
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise RuntimeError("GLM 返回内容为空")
        return content


def lang_display(code: str) -> str:
    return _LANG_NAMES.get(code, code)


async def translate_text(text: str, source_lang: str, target_lang: str, tone: str = "Professional") -> tuple[str, str]:
    source_text = lang_display(source_lang) if source_lang != "auto" else "Detect automatically"
    target_text = lang_display(target_lang)

    system_prompt = f"""You are a professional linguistic translation engine.
Translate the user input text from '{source_text}' to '{target_text}'.
The tone of translation must be '{tone}'.
Strict rules:
1. Translate only. Do not add any conversational context, meta text, or chat responses.
2. Maintain technical terms, punctuation, layout, and line breaks where appropriate.
3. If the input is in the target language already, optimize it slightly or return it as-is."""

    start = time.time()
    result = await glm_completion(system_prompt, text, temperature=0.2)
    duration = f"{(time.time() - start):.1f}s"
    return result, duration


async def summarize_text(
    text: str,
    key_points_count: int = 5,
    word_limit: int = 250,
    tone: str = "Professional",
) -> tuple[dict[str, Any], str]:
    system_prompt = f"""You are a high-level technical analyst and document compression system.
Summarize the provided content into a cohesive overview and an ordered list of precisely key insights.
Respond strictly in JSON format with keys "overview" (string) and "keyPoints" (array of strings).
Use a '{tone}' style when summarizing. Output must match the text's dominant language.
The overview must be at most {word_limit} words.
Provide exactly {key_points_count} key points in keyPoints."""

    user_prompt = f"""Perform summarization under these parameters:
- Key points count: exactly {key_points_count} bullet points.
- Word limit for overview: maximum {word_limit} words.
- Tone style: {tone}

Here is the text to summarize:
{text}

Respond with valid JSON only: {{"overview": "...", "keyPoints": ["...", ...]}}"""

    start = time.time()
    raw = await glm_completion(system_prompt, user_prompt, temperature=0.3)
    duration = f"{(time.time() - start):.1f}s"

    try:
        # 去掉可能的 markdown 代码块包裹
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        summary = json.loads(cleaned)
    except json.JSONDecodeError:
        summary = {"overview": raw, "keyPoints": ["Summary generation compiled successfully."]}

    if "overview" not in summary:
        summary["overview"] = raw
    if "keyPoints" not in summary or not isinstance(summary["keyPoints"], list):
        summary["keyPoints"] = []

    return summary, duration


def list_logs() -> list[dict[str, Any]]:
    return logs_db


def add_log(payload: dict[str, Any]) -> dict[str, Any]:
    times = get_current_time_details()
    new_log = {
        "id": f"log-{int(time.time() * 1000)}",
        "timestamp": times["time"],
        "date": times["date"],
        **payload,
    }
    logs_db.insert(0, new_log)
    return new_log


def update_log(log_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    for i, log in enumerate(logs_db):
        if log["id"] == log_id:
            merged = {**log, **updates}
            logs_db[i] = merged
            return merged
    return None
