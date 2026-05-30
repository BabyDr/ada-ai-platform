"""
内存任务管理器（状态机 + 取消 + 超时 + 心跳支撑）。

设计取舍：
- SSE 生成器运行在请求自身的协程里，跨请求强制 cancel 较复杂；
  这里用「协作式取消」：DELETE 接口标记 `cancelled` 事件，生成器在每个 token 间检查并提前结束。
- #44 并发限制、#45 终态 eviction、#31 僵尸任务 sweeper。
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

from adaagent.config import settings


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

_TERMINAL = frozenset({TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED})


@dataclass
class TaskContext:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    last_heartbeat: float = field(default_factory=time.time)
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskContext] = {}

    def create(self) -> TaskContext:
        self._evict_if_needed()
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
            ctx.last_heartbeat = time.time()
        if status in _TERMINAL:
            self._evict_if_needed()

    def touch_heartbeat(self, task_id: str) -> None:
        ctx = self._tasks.get(task_id)
        if ctx is not None:
            ctx.last_heartbeat = time.time()

    def running_count(self) -> int:
        return sum(1 for ctx in self._tasks.values() if ctx.status == TaskStatus.RUNNING)

    def cancel(self, task_id: str) -> bool:
        """标记取消；运行中的任务返回 True。"""
        ctx = self._tasks.get(task_id)
        if ctx is None:
            return False
        if ctx.status in _TERMINAL:
            return False
        ctx.cancel_event.set()
        ctx.status = TaskStatus.CANCELLED
        return True

    def sweep_zombie_tasks(self) -> int:
        """#31：RUNNING 且超过 zombie_task_seconds 无心跳 → FAILED。"""
        now = time.time()
        limit = settings.zombie_task_seconds
        swept = 0
        for ctx in self._tasks.values():
            if ctx.status != TaskStatus.RUNNING:
                continue
            if now - ctx.last_heartbeat > limit:
                ctx.status = TaskStatus.FAILED
                ctx.cancel_event.set()
                swept += 1
        if swept:
            self._evict_if_needed()
        return swept

    def _evict_if_needed(self) -> None:
        cap = settings.max_task_entries
        if len(self._tasks) <= cap:
            return
        terminal_ids = [tid for tid, ctx in self._tasks.items() if ctx.status in _TERMINAL]
        for tid in terminal_ids[: len(self._tasks) - cap]:
            self._tasks.pop(tid, None)


task_manager = TaskManager()
