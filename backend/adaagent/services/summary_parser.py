"""
总结结果 JSON 解析（翻译/总结 SSE 任务与 linguist 日志共用）。

将 LLM 流式输出的原始文本解析为 {overview, keyPoints} 结构，容错 markdown 代码块包裹。
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class SummaryResult(BaseModel):
    """总结结构化输出 Schema（#8 / #24）。"""

    overview: str = Field(min_length=1)
    keyPoints: list[str] = Field(min_length=1)


def _clean_json_raw(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return cleaned.strip()


def parse_summary_json(raw: str) -> dict[str, Any]:
    """把总结的原始流式文本解析为 {overview, keyPoints}（容错处理 markdown 代码块）。"""
    cleaned = _clean_json_raw(raw)
    try:
        summary = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"overview": raw, "keyPoints": []}
    if not isinstance(summary, dict):
        return {"overview": raw, "keyPoints": []}
    summary.setdefault("overview", raw)
    if not isinstance(summary.get("keyPoints"), list):
        summary["keyPoints"] = []
    return summary


def validate_summary(raw: str, key_points_count: int) -> dict[str, Any]:
    """
    严格校验总结 JSON；失败抛 ValueError（供 #25 重试）。

    Raises:
        ValueError: JSON 无效或 Schema 不匹配。
    """
    cleaned = _clean_json_raw(raw)
    if not cleaned:
        raise ValueError("empty summary output")
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError("invalid JSON in summary output") from e
    if not isinstance(data, dict):
        raise ValueError("summary output must be a JSON object")
    try:
        result = SummaryResult.model_validate(data)
    except ValidationError as e:
        raise ValueError("summary schema validation failed") from e
    if len(result.keyPoints) != key_points_count:
        raise ValueError(
            f"expected exactly {key_points_count} keyPoints, got {len(result.keyPoints)}"
        )
    return result.model_dump()
