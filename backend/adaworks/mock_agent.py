"""
Mock 模型：无 API Key 时的本地演示。

作用：
- 走与真实模型相同的事件通道（think / act / observe / delta / final），便于只学前端或联调。
- 仍写入 SQLite，便于观察「会话与消息」数据流。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite

    from adaworks.ws_hub import ChatHub


async def _insert_message(
    db: aiosqlite.Connection,
    lock: asyncio.Lock,
    session_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> str:
    """在锁内插入一条消息并 commit；返回新消息 id。"""
    mid = uuid.uuid4().hex
    meta_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
    async with lock:
        await db.execute(
            "INSERT INTO messages (id, session_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)",
            (mid, session_id, role, content, meta_json),
        )
        await db.execute(
            "UPDATE sessions SET updated_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        await db.commit()
    return mid


async def run_mock_agent(
    session_id: str,
    hub: ChatHub,
    db: aiosqlite.Connection,
    lock: asyncio.Lock,
) -> None:
    """异步任务：用 sleep 模拟耗时，依次推送事件并写入 SQLite。"""
    await asyncio.sleep(0.55)
    await hub.broadcast(session_id, "agent:think", {"content": "（Mock）分析用户需求，准备调用示例工具。"})
    await _insert_message(db, lock, session_id, "think", "（Mock）分析用户需求，准备调用示例工具。")

    await asyncio.sleep(0.35)
    await hub.broadcast(
        session_id,
        "agent:act",
        {"tool": "file_read", "params": {"path": "./README.md"}},
    )
    await _insert_message(
        db,
        lock,
        session_id,
        "act",
        "调用工具 file_read",
        {"tool": "file_read", "params": {"path": "./README.md"}},
    )

    await asyncio.sleep(0.35)
    observe = '{"preview": "… 文件内容省略 …"}'
    await hub.broadcast(session_id, "agent:observe", {"result": observe})
    await _insert_message(db, lock, session_id, "observe", observe)

    await asyncio.sleep(0.4)
    final_text = "（Mock 最终回答）这是 AdaWorks 开发阶段的示例回复。"
    for i in range(0, len(final_text), 12):
        await hub.broadcast(session_id, "agent:delta", {"content": final_text[i : i + 12]})
        await asyncio.sleep(0.06)
    await hub.broadcast(session_id, "agent:final", {})
    await _insert_message(db, lock, session_id, "assistant", final_text)
