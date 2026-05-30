"""取消闭环：task_start 后标记取消，流提前结束并发送 task_done(status=cancelled)。"""

from __future__ import annotations

import asyncio
import json

from adaagent.api.task import _task_generator
from adaagent.services.task_manager import task_manager


def test_cancel_midstream() -> None:
    async def run() -> list[dict]:
        gen = _task_generator("translate", {"text": "hello world"})
        first = await gen.__anext__()
        task_id = json.loads(first["data"])["taskId"]
        # 模拟 DELETE /api/task/{id}
        assert task_manager.cancel(task_id) is True
        events = [first]
        async for ev in gen:
            events.append(ev)
        return events

    events = asyncio.run(run())
    assert events[0]["event"] == "task_start"
    last = events[-1]
    assert last["event"] == "task_done"
    assert json.loads(last["data"])["status"] == "cancelled"
