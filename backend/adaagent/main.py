"""
AdaAgent Python Sidecar（FastAPI）。

职责概览：
- 提供 REST API：会话 CRUD、发消息、健康检查。
- 提供 WebSocket：按会话推送模型事件（流式 delta、结束、错误等）。
- 在收到用户消息后，通过 asyncio.create_task 后台执行模型逻辑，避免阻塞 HTTP 响应。

详细模块分工见仓库根目录 README.md。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from adaagent.bootstrap_env import load_app_dotenv

load_app_dotenv()

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from adaagent.api.router import api_router
from adaagent.db import connect, row_to_message, row_to_session
from adaagent.gemini_agent import gemini_api_key_configured, run_gemini_agent
from adaagent.glm_agent import DEFAULT_GLM_MODEL, glm_api_key_configured, run_glm_agent
from adaagent.linguist_service import (
    add_log,
    list_logs,
    update_log,
)
from adaagent.mock_agent import run_mock_agent
from adaagent.http_safe import register_global_exception_handler
from adaagent.ws_hub import ChatHub


def _active_llm_mode() -> str:
    """根据环境变量决定实际调用的模型后端（与 post_chat 分支一致）。"""
    # GLM 优先：与业务上「默认用智谱」一致；未配置时再尝试 Gemini。
    if glm_api_key_configured():
        return "glm"
    if gemini_api_key_configured():
        return "gemini"
    return "mock"


class SessionCreate(BaseModel):
    """创建会话请求体。"""

    title: str | None = None


class ChatRequestBody(BaseModel):
    """POST /api/chat 请求体。"""

    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息")
    model_id: str = Field(..., description="当前模型 ID")


class LogAddRequest(BaseModel):
    type: str
    input: str
    output: str = ""
    duration: str = "--"
    status: str = "processing"
    error: str | None = None
    details: dict[str, Any] | None = None


class LogUpdateRequest(BaseModel):
    id: str
    status: str | None = None
    output: str | None = None
    duration: str | None = None
    error: str | None = None


def create_app(db_path: Path | None = None) -> FastAPI:
    """创建 FastAPI 应用；单测可传入独立 db_path 使用内存或临时文件库。"""

    # hub：所有 WS 连接与广播逻辑；db_lock：多协程写入 SQLite 时串行化，避免锁竞争导致损坏。
    hub = ChatHub()
    db_lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = await connect(db_path)
        app.state.db = conn
        app.state.hub = hub
        app.state.db_lock = db_lock
        log = logging.getLogger("adaagent")
        mode = _active_llm_mode()
        if mode == "glm":
            log.warning("LLM 模式: GLM（已检测到 GLM_API_KEY 或 ZHIPU_API_KEY）")
        elif mode == "gemini":
            log.warning("LLM 模式: Gemini（已检测到 GEMINI_API_KEY 或 GOOGLE_API_KEY）")
        else:
            log.warning(
                "LLM 模式: Mock。请在 .env 中设置 GLM_API_KEY（智谱）或 GEMINI_API_KEY 后重启 Sidecar",
            )
        yield
        await conn.close()

    app = FastAPI(title="AdaAgent Sidecar", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_global_exception_handler(app)

    @app.get("/api/sessions")
    async def list_sessions(request: Request) -> dict[str, Any]:
        """获取会话列表。"""
        db = request.app.state.db
        async with db.execute("SELECT * FROM sessions ORDER BY updated_at DESC") as cur:
            rows = await cur.fetchall()
        return {"sessions": [dict(row_to_session(r)) for r in rows]}

    @app.post("/api/sessions")
    async def create_session(request: Request, body: SessionCreate) -> dict[str, Any]:
        """创建新会话。"""
        sid = uuid.uuid4().hex
        title = (body.title or "").strip() or "新会话"
        db = request.app.state.db
        lock: asyncio.Lock = request.app.state.db_lock
        async with lock:
            await db.execute(
                "INSERT INTO sessions (id, title, model_id) VALUES (?, ?, ?)",
                (sid, title, DEFAULT_GLM_MODEL),
            )
            await db.commit()
        async with db.execute("SELECT * FROM sessions WHERE id = ?", (sid,)) as cur:
            row = await cur.fetchone()
        assert row is not None
        return {"session": dict(row_to_session(row))}

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str, request: Request) -> dict[str, bool]:
        """删除会话。"""
        db = request.app.state.db
        lock: asyncio.Lock = request.app.state.db_lock
        async with lock:
            cur = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()
        return {"success": cur.rowcount > 0}

    @app.get("/api/sessions/{session_id}/messages")
    async def list_messages(session_id: str, request: Request) -> dict[str, Any]:
        """获取会话消息历史。"""
        db = request.app.state.db
        async with db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ) as cur:
            rows = await cur.fetchall()
        return {"messages": [dict(row_to_message(r)) for r in rows]}

    @app.post("/api/chat")
    async def post_chat(request: Request, body: ChatRequestBody) -> dict[str, str]:
        """发送消息：落库用户消息并异步触发 GLM / Gemini / Mock。"""
        db = request.app.state.db
        lock: asyncio.Lock = request.app.state.db_lock
        hub: ChatHub = request.app.state.hub

        async with db.execute("SELECT id FROM sessions WHERE id = ?", (body.session_id,)) as cur:
            if await cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="session not found")

        # 用户消息先落库，模型任务稍后读取「user/assistant」历史构建上下文。
        user_mid = uuid.uuid4().hex
        async with lock:
            await db.execute(
                "INSERT INTO messages (id, session_id, role, content, metadata) VALUES (?, ?, ?, ?, NULL)",
                (user_mid, body.session_id, "user", body.message),
            )
            await db.execute(
                "UPDATE sessions SET model_id = ?, updated_at = datetime('now') WHERE id = ?",
                (body.model_id, body.session_id),
            )
            await db.commit()

        # create_task：立即返回 HTTP，模型在后台跑并通过 WebSocket 推送。
        if glm_api_key_configured():
            asyncio.create_task(
                run_glm_agent(body.session_id, hub, db, lock, body.model_id),
            )
        elif gemini_api_key_configured():
            asyncio.create_task(
                run_gemini_agent(body.session_id, hub, db, lock, body.model_id),
            )
        else:
            asyncio.create_task(
                run_mock_agent(body.session_id, hub, db, lock),
            )
        return {"session_id": body.session_id, "message_id": user_mid}

    @app.websocket("/ws/chat/{session_id}")
    async def websocket_chat(websocket: WebSocket, session_id: str) -> None:
        """
        长连接：仅用于服务端下行推送；客户端发来的文本帧可忽略（仅占位保活）。
        业务事件一律由后台模型任务调用 hub.broadcast 下发。
        """
        starlette_app = websocket.scope["app"]
        hub: ChatHub = starlette_app.state.hub
        await hub.connect(session_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(session_id, websocket)

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        """健康检查；`llm` 为 glm / gemini / mock；`keyLoaded` 供 Linguist 前端使用。"""
        key_loaded = glm_api_key_configured() or gemini_api_key_configured()
        return {
            "status": "ok",
            "llm": _active_llm_mode(),
            "keyLoaded": key_loaded,
        }

    @app.get("/api/logs")
    async def get_logs() -> list[dict[str, Any]]:
        """获取翻译/总结操作日志（内存）。"""
        return list_logs()

    @app.post("/api/logs/add")
    async def post_log_add(body: LogAddRequest) -> dict[str, Any]:
        """追加操作日志。"""
        return add_log(body.model_dump(exclude_none=True))

    @app.post("/api/logs/update-status")
    async def post_log_update(body: LogUpdateRequest) -> dict[str, Any]:
        """更新日志状态。"""
        updates = body.model_dump(exclude={"id"}, exclude_none=True)
        updated = update_log(body.id, updates)
        if updated is None:
            raise HTTPException(status_code=404, detail="Log not found")
        return updated

    # SSE 任务契约：GET /api/functions、POST /api/task、DELETE/GET /api/task/{id}
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
