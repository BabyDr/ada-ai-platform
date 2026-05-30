"""任务管理器：create/get/cancel 基本路径与状态机。"""

from __future__ import annotations

from adaagent.services.task_manager import TaskManager, TaskStatus


def test_create_and_get() -> None:
    tm = TaskManager()
    ctx = tm.create()
    assert tm.get(ctx.task_id) is ctx
    assert ctx.status == TaskStatus.PENDING
    assert not ctx.cancelled


def test_cancel_running() -> None:
    tm = TaskManager()
    ctx = tm.create()
    tm.set_status(ctx.task_id, TaskStatus.RUNNING)
    assert tm.cancel(ctx.task_id) is True
    assert ctx.status == TaskStatus.CANCELLED
    assert ctx.cancelled
    # 已结束的任务不可再次取消
    assert tm.cancel(ctx.task_id) is False


def test_cancel_unknown() -> None:
    tm = TaskManager()
    assert tm.cancel("missing") is False


def test_running_count() -> None:
    tm = TaskManager()
    ctx = tm.create()
    tm.set_status(ctx.task_id, TaskStatus.RUNNING)
    assert tm.running_count() == 1
    tm.set_status(ctx.task_id, TaskStatus.DONE)
    assert tm.running_count() == 0


def test_sweep_zombie_tasks() -> None:
    tm = TaskManager()
    ctx = tm.create()
    tm.set_status(ctx.task_id, TaskStatus.RUNNING)
    ctx.last_heartbeat = 0.0
    assert tm.sweep_zombie_tasks() == 1
    assert ctx.status == TaskStatus.FAILED
