"""
总结结果 JSON 解析（翻译/总结 SSE 任务与 linguist 日志共用）。

将 LLM 流式输出的原始文本解析为 {overview, keyPoints} 结构，容错 markdown 代码块包裹。
"""

from __future__ import annotations

import json
from typing import Any


def parse_summary_json(raw: str) -> dict[str, Any]:
    """把总结的原始流式文本解析为 {overview, keyPoints}（容错处理 markdown 代码块）。"""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
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
