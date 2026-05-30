"""
内存任务管理器（状态机 + 取消 + 超时支撑）。

设计取舍：
- SSE 生成器运行在请求自身的协程里，跨请求强制 cancel 较复杂；
  这里用「协作式取消」：DELETE 接口标记 `cancelled` 事件，生成器在每个 token 间检查并提前结束。
- 不做过度设计：纯进程内 dict，足够演示 pending→running→done/failed/cancelled。
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    # 协作式取消信号：DELETE 时 set，生成器循环检测。
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskContext] = {}

    def create(self) -> TaskContext:
        task_id = uuid.uuid4().hex[:12]
        ctx = TaskContext(task_id=task_id)
        self._tasks[task_id] = ctx
        return ctx

    def get(self, task_id: str) -> TaskContext | None:
        return self._tasks.get(task_id)

    def set_status(self, task_id: str, status: TaskStatus) -> None:
        ctx = self._tasks.get(task_id)
        if ctx is not None:
            ctx.status = status

    def cancel(self, task_id: str) -> bool:
        """标记取消；运行中的任务返回 True。"""
        ctx = self._tasks.get(task_id)
        if ctx is None:
            return False
        if ctx.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False
        ctx.cancel_event.set()
        ctx.status = TaskStatus.CANCELLED
        return True

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)


task_manager = TaskManager()
