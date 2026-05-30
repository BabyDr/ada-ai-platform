"""
Linguist AI 运行日志（进程内内存）。

翻译 / 总结任务经 SSE（api/task.py）执行；本模块仅负责日志 CRUD 与语言展示名。
"""

from __future__ import annotations

import json
import time
from typing import Any

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


def get_current_time_details() -> dict[str, str]:
    """生成日志条目的 timestamp 与 date 字段（12 小时制）。"""
    d = time.localtime()
    hours = d.tm_hour
    minutes = d.tm_min
    ampm = "PM" if hours >= 12 else "AM"
    hours = hours % 12 or 12
    min_str = f"{minutes:02d}"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return {"time": f"{hours}:{min_str} {ampm}", "date": f"{months[d.tm_mon - 1]} {d.tm_mday}"}


def lang_display(code: str) -> str:
    """语言 code → 展示名（未知 code 原样返回）。"""
    return _LANG_NAMES.get(code, code)


def list_logs() -> list[dict[str, Any]]:
    """返回全部运行日志（内存列表，最新在前）。"""
    return logs_db


def add_log(payload: dict[str, Any]) -> dict[str, Any]:
    """新增一条日志并插入列表头部，自动补全 id/timestamp/date。"""
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
    """按 id 合并更新日志字段；未找到返回 None。"""
    for i, log in enumerate(logs_db):
        if log["id"] == log_id:
            merged = {**log, **updates}
            logs_db[i] = merged
            return merged
    return None
