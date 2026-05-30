"""后台僵尸任务 sweeper（#31）。"""

from __future__ import annotations

import asyncio
import logging

from adaagent.services.task_manager import task_manager

_log = logging.getLogger("adaagent")


async def run_task_sweeper(interval_seconds: int = 60) -> None:
    """周期性扫描无心跳 RUNNING 任务并标记 FAILED。"""
    while True:
        await asyncio.sleep(interval_seconds)
        swept = task_manager.sweep_zombie_tasks()
        if swept:
            _log.warning("Swept %s zombie task(s)", swept)
