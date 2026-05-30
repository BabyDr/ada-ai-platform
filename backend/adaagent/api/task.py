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
from adaagent.services.llm import llm_service
from adaagent.services.summary_parser import parse_summary_json
from adaagent.services.task_log import (
    build_task_messages,
    create_processing_log,
    mark_log_cancelled,
    mark_log_failed,
    mark_log_success_summarize,
    mark_log_success_translate,
    mark_log_timeout,
)
from adaagent.services.task_manager import TaskStatus, task_manager

router = APIRouter()


def _sse(event: str, data: dict[str, Any]) -> dict[str, str]:
    """构造 sse-starlette 事件字典。"""
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


async def _task_generator(task_type: str, params: dict[str, Any]) -> AsyncIterator[dict[str, str]]:
    """SSE 任务主循环：流式 LLM + 协作式取消 + 日志终态写入。"""
    ctx = task_manager.create()
    log_id, _log = create_processing_log(task_type, params)

    yield _sse("task_start", {"taskId": ctx.task_id})
    task_manager.set_status(ctx.task_id, TaskStatus.RUNNING)

    system, user = build_task_messages(task_type, params)
    collected: list[str] = []
    start = time.time()
    deadline = start + settings.task_timeout_seconds

    try:
        stream = llm_service.stream(system, user, task_type=task_type)
        while True:
            if ctx.cancelled:
                duration = f"{time.time() - start:.1f}s"
                mark_log_cancelled(log_id, duration)
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
        mark_log_timeout(log_id, duration)
        yield _sse("task_error", {"taskId": ctx.task_id, "message": "任务超时"})
        return
    except Exception as e:  # noqa: BLE001
        duration = f"{time.time() - start:.1f}s"
        task_manager.set_status(ctx.task_id, TaskStatus.FAILED)
        msg = str(e)[:800]
        mark_log_failed(log_id, duration, msg)
        yield _sse("task_error", {"taskId": ctx.task_id, "message": msg})
        return

    duration = f"{time.time() - start:.1f}s"
    raw = "".join(collected)
    task_manager.set_status(ctx.task_id, TaskStatus.DONE)

    if task_type == "translate":
        result: dict[str, Any] = {"text": raw}
        mark_log_success_translate(log_id, duration, raw)
    else:
        result = parse_summary_json(raw)
        mark_log_success_summarize(log_id, duration, result)

    yield _sse("task_done", {"taskId": ctx.task_id, "status": "done", "duration": duration, "result": result})


@router.post("/task")
async def create_task(req: TaskCreateRequest) -> EventSourceResponse:
    """提交 SSE 流式任务（translate / summarize）。"""
    if not str(req.params.get("text", "")).strip():
        raise HTTPException(status_code=400, detail="params.text is required")
    return EventSourceResponse(_task_generator(req.type, req.params))


@router.delete("/task/{task_id}", response_model=CancelResponse)
async def cancel_task(task_id: str) -> CancelResponse:
    """协作式取消正在运行的任务。"""
    ok = task_manager.cancel(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found or already finished")
    return CancelResponse(message="task cancelled", taskId=task_id)


@router.get("/task/{task_id}")
async def get_task(task_id: str) -> dict[str, str]:
    """查询任务状态（pending / running / done / failed / cancelled）。"""
    ctx = task_manager.get(task_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"taskId": ctx.task_id, "status": ctx.status.value}
