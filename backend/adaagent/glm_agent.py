"""
智谱 GLM：OpenAI 兼容「流式」对话。

流程简述：
1. 从 SQLite 读出当前会话的 user/assistant 消息，拼成 `messages` 数组。
2. POST `/chat/completions` 且 `stream: true`，按行读取 SSE（`data: {...}`）。
3. 每收到一段 `delta.content`，通过 WebSocket 发 `agent:delta`。
4. 流结束后发 `agent:final`，并把完整回答写入 messages 表。

参考：智谱开放平台文档（chat completions + SSE）。
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

import httpx

from adaagent.env_secrets import read_first_secret
from adaagent.mock_agent import _insert_message

if TYPE_CHECKING:
    import aiosqlite

    from adaagent.ws_hub import ChatHub

# 默认模型与网关：可通过环境变量 GLM_MODEL / GLM_API_BASE 覆盖。
DEFAULT_GLM_MODEL = "glm-4-flash"
DEFAULT_GLM_BASE = "https://open.bigmodel.cn/api/paas/v4"


def glm_api_key_configured() -> bool:
    """是否已配置智谱 API Key（支持 .env 中为 JSON 字符串数组，拼接后使用）。"""
    return bool(read_first_secret("GLM_API_KEY", "ZHIPU_API_KEY"))


def _api_key() -> str | None:
    return read_first_secret("GLM_API_KEY", "ZHIPU_API_KEY")


def _api_base() -> str:
    return (os.environ.get("GLM_API_BASE") or DEFAULT_GLM_BASE).rstrip("/")


def _resolve_model(model_id: str) -> str:
    """前端传的 model_id 若以 glm- 开头则视为完整模型名；否则用 GLM_MODEL 或默认。"""
    mid = model_id.strip()
    if mid.startswith("glm-"):
        return mid
    return (os.environ.get("GLM_MODEL") or DEFAULT_GLM_MODEL).strip() or DEFAULT_GLM_MODEL


async def run_glm_agent(
    session_id: str,
    hub: ChatHub,
    db: aiosqlite.Connection,
    lock: asyncio.Lock,
    model_id: str,
) -> None:
    # lock：与 HTTP 写库共用，插入 assistant 前需与 post_chat 等写操作互斥。
    api_key = _api_key()
    if not api_key:
        await hub.broadcast(session_id, "agent:error", {"message": "未配置 GLM_API_KEY 或 ZHIPU_API_KEY"})
        return

    model_name = _resolve_model(model_id)
    base = _api_base()

    async with db.execute(
        "SELECT role, content FROM messages WHERE session_id = ? "
        "AND role IN ('user', 'assistant') ORDER BY created_at ASC",
        (session_id,),
    ) as cur:
        rows = await cur.fetchall()

    messages: list[dict[str, str]] = []
    for row in rows:
        role, content = row["role"], row["content"]
        if role == "user":
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "assistant", "content": content})

    if not messages:
        await hub.broadcast(session_id, "agent:error", {"message": "无有效对话内容"})
        return

    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"model": model_name, "messages": messages, "stream": True}

    collected: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream("POST", url, headers=headers, json=body) as r:
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError:
                    # 流式接口在打开连接后即可 4xx，此时读 body 便于排错。
                    err_body = (await r.aread()).decode(errors="replace")[:800]
                    raise RuntimeError(f"GLM HTTP {r.status_code}: {err_body}") from None

                # SSE：每行一般以 data: 开头；[DONE] 表示结束。
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                    elif line.startswith("data: "):
                        payload = line[6:].strip()
                    else:
                        continue
                    if payload == "[DONE]":
                        break
                    try:
                        obj = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    err = obj.get("error")
                    if isinstance(err, dict) and err.get("message"):
                        raise RuntimeError(str(err.get("message")))
                    for ch in obj.get("choices") or []:
                        delta = ch.get("delta") or {}
                        piece = delta.get("content") or ""
                        if piece:
                            collected.append(piece)
                            await hub.broadcast(session_id, "agent:delta", {"content": piece})
    except Exception as e:  # noqa: BLE001
        await hub.broadcast(session_id, "agent:error", {"message": str(e)[:800]})
        return

    text = "".join(collected).strip()
    if not text:
        await hub.broadcast(session_id, "agent:error", {"message": "GLM 流式结束但内容为空"})
        return

    await hub.broadcast(session_id, "agent:final", {})
    await _insert_message(db, lock, session_id, "assistant", text)
