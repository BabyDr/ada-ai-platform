"""
POST /api/task (SSE) + DELETE /api/task/{taskId} + GET /api/task/{taskId}。

SSE 事件：
  event: task_start  data: {"taskId": "..."}
  event: token       data: {"content": "..."}
  event: task_done   data: {"taskId","status","duration","result"}
  event: task_error  data: {"taskId","message"}

取消：DELETE 标记 cancel_event，生成器在 token 间检测后提前结束并发送 task_done(status=cancelled)。
超时：单个 token 等待超过剩余预算则按 failed 结束（F18）。
任务结束写入 History（复用 linguist_service 内存日志）。
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from adaagent.api.schemas import CancelResponse, TaskCreateRequest
from adaagent.config import settings
from adaagent.linguist_service import add_log, update_log
from adaagent.services.llm import llm_service
from adaagent.services.prompt import build_summarize_messages, build_translate_messages
from adaagent.services.task_manager import TaskStatus, task_manager

router = APIRouter()


def _sse(event: str, data: dict[str, Any]) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def _parse_summary(raw: str) -> dict[str, Any]:
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


def _build_messages(task_type: str, params: dict[str, Any]) -> tuple[str, str]:
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
        int(params.get("keyPointsCount", 5)),
        int(params.get("wordLimit", 250)),
        str(params.get("tone", "Professional")),
    )


def _log_details(task_type: str, params: dict[str, Any]) -> dict[str, Any]:
    if task_type == "translate":
        return {
            "sourceLang": params.get("sourceLang", "auto"),
            "targetLang": params.get("targetLang", "zh"),
            "tone": params.get("tone", "Professional"),
        }
    return {
        "keyPointsCount": params.get("keyPointsCount", 5),
        "wordLimit": params.get("wordLimit", 250),
        "tone": params.get("tone", "Professional"),
    }


async def _task_generator(task_type: str, params: dict[str, Any]) -> AsyncIterator[dict[str, str]]:
    ctx = task_manager.create()
    log_type = "translation" if task_type == "translate" else "summarization"
    raw_input = str(params.get("text", ""))

    log = add_log(
        {
            "type": log_type,
            "input": raw_input[:500],
            "output": "...",
            "duration": "--",
            "status": "processing",
            "details": _log_details(task_type, params),
        }
    )
    log_id = log["id"]

    yield _sse("task_start", {"taskId": ctx.task_id})
    task_manager.set_status(ctx.task_id, TaskStatus.RUNNING)

    system, user = _build_messages(task_type, params)
    collected: list[str] = []
    start = time.time()
    deadline = start + settings.task_timeout_seconds

    try:
        stream = llm_service.stream(system, user, task_type=task_type)
        while True:
            if ctx.cancelled:
                duration = f"{time.time() - start:.1f}s"
                update_log(log_id, {"status": "failed", "output": "Task cancelled", "duration": duration, "error": "Task cancelled by user"})
                yield _sse("task_done", {"taskId": ctx.task_id, "status": "cancelled", "duration": duration, "result": None})
                return

            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(f"任务超过 {settings.task_timeout_seconds}s 超时")

            try:
                piece = await asyncio.wait_for(stream.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break

            collected.append(piece)
            yield _sse("token", {"content": piece})

    except (TimeoutError, asyncio.TimeoutError):
        duration = f"{time.time() - start:.1f}s"
        task_manager.set_status(ctx.task_id, TaskStatus.FAILED)
        update_log(log_id, {"status": "failed", "output": "Timeout", "duration": duration, "error": "任务超时"})
        yield _sse("task_error", {"taskId": ctx.task_id, "message": "任务超时"})
        return
    except Exception as e:  # noqa: BLE001
        duration = f"{time.time() - start:.1f}s"
        task_manager.set_status(ctx.task_id, TaskStatus.FAILED)
        msg = str(e)[:800]
        update_log(log_id, {"status": "failed", "output": msg, "duration": duration, "error": msg})
        yield _sse("task_error", {"taskId": ctx.task_id, "message": msg})
        return

    duration = f"{time.time() - start:.1f}s"
    raw = "".join(collected)
    task_manager.set_status(ctx.task_id, TaskStatus.DONE)

    if task_type == "translate":
        result: dict[str, Any] = {"text": raw}
        update_log(log_id, {"status": "success", "output": raw, "duration": duration})
    else:
        result = _parse_summary(raw)
        update_log(log_id, {"status": "success", "output": json.dumps(result, ensure_ascii=False), "duration": duration})

    yield _sse("task_done", {"taskId": ctx.task_id, "status": "done", "duration": duration, "result": result})


@router.post("/task")
async def create_task(req: TaskCreateRequest) -> EventSourceResponse:
    if not str(req.params.get("text", "")).strip():
        raise HTTPException(status_code=400, detail="params.text is required")
    return EventSourceResponse(_task_generator(req.type, req.params))


@router.delete("/task/{task_id}", response_model=CancelResponse)
async def cancel_task(task_id: str) -> CancelResponse:
    ok = task_manager.cancel(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found or already finished")
    return CancelResponse(message="task cancelled", taskId=task_id)


@router.get("/task/{task_id}")
async def get_task(task_id: str) -> dict[str, str]:
    ctx = task_manager.get(task_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"taskId": ctx.task_id, "status": ctx.status.value}
