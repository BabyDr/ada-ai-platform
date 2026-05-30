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

from adaworks.config import settings


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
    """内存任务状态管理器：创建、状态流转、协作式取消、僵尸清理、终态驱逐。"""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskContext] = {}

    def create(self) -> TaskContext:
        """创建新任务上下文（PENDING 状态），超限时先驱逐终态任务。"""
        self._evict_if_needed()
        task_id = uuid.uuid4().hex[:12]
        ctx = TaskContext(task_id=task_id)
        self._tasks[task_id] = ctx
        return ctx

    def get(self, task_id: str) -> TaskContext | None:
        """按 ID 查找任务上下文，不存在则返回 None。"""
        return self._tasks.get(task_id)

    def set_status(self, task_id: str, status: TaskStatus) -> None:
        """更新任务状态并刷新心跳；若进入终态则触发驱逐检查。"""
        ctx = self._tasks.get(task_id)
        if ctx is not None:
            ctx.status = status
            ctx.last_heartbeat = time.time()
        if status in _TERMINAL:
            self._evict_if_needed()

    def touch_heartbeat(self, task_id: str) -> None:
        """刷新任务心跳时间戳，供 SSE 生成器在每次 yield token 时调用，防止被 sweeper 误判为僵尸。"""
        ctx = self._tasks.get(task_id)
        if ctx is not None:
            ctx.last_heartbeat = time.time()

    def running_count(self) -> int:
        """当前处于 RUNNING 状态的任务数，用于并发限制判断。"""
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
        """当内存任务数超过 max_task_entries 时，优先驱逐已终态（DONE/FAILED/CANCELLED）的旧任务。"""
        cap = settings.max_task_entries
        if len(self._tasks) <= cap:
            return
        # 收集所有终态任务 ID，按超出配额的数量批量移除
        terminal_ids = [tid for tid, ctx in self._tasks.items() if ctx.status in _TERMINAL]
        for tid in terminal_ids[: len(self._tasks) - cap]:
            self._tasks.pop(tid, None)


task_manager = TaskManager()
