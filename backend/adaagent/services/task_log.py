"""
SSE 任务执行期间的 linguist 运行日志辅助。

翻译/总结任务在 task.py 中共用：创建 processing 日志、按终态更新 output。
"""

from __future__ import annotations

import json
from typing import Any

from adaagent.linguist_service import add_log, update_log
from adaagent.services.prompt import build_summarize_messages, build_translate_messages


def log_type_for_task(task_type: str) -> str:
    """SSE task type → linguist 日志 type（translate → translation）。"""
    return "translation" if task_type == "translate" else "summarization"


def build_log_details(task_type: str, params: dict[str, Any]) -> dict[str, Any]:
    """从任务 params 提取写入日志 details 字段的结构。"""
    if task_type == "translate":
        return {
            "sourceLang": params.get("sourceLang", "auto"),
            "targetLang": params.get("targetLang", "zh"),
            "tone": params.get("tone", "Professional"),
        }
    return {
        "keyPointsCount": params.get("keyPointsCount", 3),
        "wordLimit": params.get("wordLimit", 250),
        "tone": params.get("tone", "Professional"),
    }


def build_task_messages(task_type: str, params: dict[str, Any]) -> tuple[str, str]:
    """根据任务类型与 params 构建 (system, user) prompt 二元组。"""
    text = str(params.get("text", ""))
    if task_type == "translate":
        return build_translate_messages(
            text,
            str(params.get("sourceLang", "auto")),
            str(params.get("targetLang", "zh")),
            str(params.get("tone", "Professional")),
        )
    return build_summarize_messages(
        text,
        int(params.get("keyPointsCount", 3)),
        int(params.get("wordLimit", 250)),
        str(params.get("tone", "Professional")),
    )


def create_processing_log(task_type: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    创建 processing 状态日志。

    Returns:
        (log_id, log_dict) 供 task 生成器引用。
    """
    raw_input = str(params.get("text", ""))
    log = add_log(
        {
            "type": log_type_for_task(task_type),
            "input": raw_input[:500],
            "output": "...",
            "duration": "--",
            "status": "processing",
            "details": build_log_details(task_type, params),
        }
    )
    return log["id"], log


def mark_log_cancelled(log_id: str, duration: str) -> None:
    """用户取消任务时更新日志为 failed + 取消说明。"""
    update_log(
        log_id,
        {
            "status": "failed",
            "output": "Task cancelled",
            "duration": duration,
            "error": "Task cancelled by user",
        },
    )


def mark_log_timeout(log_id: str, duration: str) -> None:
    """任务超时时更新日志。"""
    update_log(
        log_id,
        {"status": "failed", "output": "Timeout", "duration": duration, "error": "任务超时"},
    )


def mark_log_failed(log_id: str, duration: str, message: str) -> None:
    """任务异常失败时更新日志。"""
    msg = message[:800]
    update_log(log_id, {"status": "failed", "output": msg, "duration": duration, "error": msg})


def mark_log_success_translate(log_id: str, duration: str, text: str) -> None:
    """翻译成功：output 为纯文本译文。"""
    update_log(log_id, {"status": "success", "output": text, "duration": duration})


def mark_log_success_summarize(log_id: str, duration: str, result: dict[str, Any]) -> None:
    """总结成功：output 为 JSON 字符串。"""
    update_log(
        log_id,
        {"status": "success", "output": json.dumps(result, ensure_ascii=False), "duration": duration},
    )
