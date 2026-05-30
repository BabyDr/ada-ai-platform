"""
SQLite 持久化层（aiosqlite 异步驱动）。

知识点：
- `sessions` 存会话元数据；`messages` 存每条消息，`role` 含 user / assistant 及 Mock 的 think/act 等。
- 模型侧拉历史时一般只取 user + assistant 拼多轮对话。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import aiosqlite


def default_db_path() -> Path:
    """默认数据库文件路径；测试可通过环境变量 ADAWORKS_DB_PATH 覆盖。"""
    override = os.environ.get("ADAWORKS_DB_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "db" / "adaworks.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    model_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""


async def connect(db_path: Path | None = None) -> aiosqlite.Connection:
    """建立数据库连接并执行 SCHEMA（幂等：表已存在则跳过）。"""
    path = db_path or default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    await conn.commit()
    return conn


def row_to_session(row: aiosqlite.Row) -> dict[str, Any]:
    """将 sessions 行转为 API Session 对象。"""
    return {
        "id": row["id"],
        "title": row["title"],
        "updated_at": row["updated_at"],
    }


def row_to_message(row: aiosqlite.Row) -> dict[str, Any]:
    """将 messages 行转为 API Message 对象。"""
    meta = row["metadata"]
    metadata: dict[str, Any] | None = None
    if meta:
        try:
            metadata = json.loads(meta)
        except json.JSONDecodeError:
            metadata = None
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "role": row["role"],
        "content": row["content"],
        "metadata": metadata,
        "created_at": row["created_at"],
    }
