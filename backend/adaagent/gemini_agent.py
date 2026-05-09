"""
Google Gemini：使用官方 `google-genai` 异步流式接口。

要点：
- `client.aio.models.generate_content_stream` 返回异步迭代器，每个 chunk 的 `.text`
  一般为**当前片段**文本，依次广播为 `agent:delta`。
- 用完后必须 `await client.aio.aclose()` 释放连接（在 finally 中）。
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from google import genai
from google.genai import errors, types

from adaagent.env_secrets import read_first_secret
from adaagent.mock_agent import _insert_message

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

if TYPE_CHECKING:
    import aiosqlite

    from adaagent.ws_hub import ChatHub


def gemini_api_key_configured() -> bool:
    """是否已配置 Gemini Developer API Key（支持 .env 中为 JSON 字符串数组，拼接后使用）。"""
    return bool(read_first_secret("GEMINI_API_KEY", "GOOGLE_API_KEY"))


def _api_key() -> str | None:
    return read_first_secret("GEMINI_API_KEY", "GOOGLE_API_KEY")


def _resolve_model(model_id: str) -> str:
    """与 GLM 侧类似：gemini- 前缀走前端指定模型，否则用 GEMINI_MODEL 或默认。"""
    if model_id.startswith("gemini-"):
        return model_id
    return (os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


def _format_gemini_error(exc: BaseException) -> str:
    if isinstance(exc, errors.ClientError) and getattr(exc, "code", None) == 429:
        return (
            "Gemini 返回 429（配额或速率限制）。"
            "可在 backend/.env 设置 GEMINI_MODEL=gemini-2.5-flash 或 gemini-2.0-flash-lite 等其它模型；"
            "若 free tier 对该模型 limit 为 0，需在 Google AI Studio / Cloud 检查计费与配额。"
            f" 原始信息（节选）：{str(exc)[:500]}"
        )
    return str(exc)[:800]


async def run_gemini_agent(
    session_id: str,
    hub: ChatHub,
    db: aiosqlite.Connection,
    lock: asyncio.Lock,
    model_id: str,
) -> None:
    api_key = _api_key()
    if not api_key:
        await hub.broadcast(session_id, "agent:error", {"message": "未配置 GEMINI_API_KEY 或 GOOGLE_API_KEY"})
        return

    model_name = _resolve_model(model_id)

    async with db.execute(
        "SELECT role, content FROM messages WHERE session_id = ? "
        "AND role IN ('user', 'assistant') ORDER BY created_at ASC",
        (session_id,),
    ) as cur:
        rows = await cur.fetchall()

    contents: list[types.Content] = []
    for row in rows:
        role, content = row["role"], row["content"]
        if role == "user":
            contents.append(
                types.UserContent(parts=[types.Part.from_text(text=content)]),
            )
        else:
            contents.append(
                types.ModelContent(parts=[types.Part.from_text(text=content)]),
            )

    if not contents:
        await hub.broadcast(session_id, "agent:error", {"message": "无有效对话内容"})
        return

    collected: list[str] = []
    client = genai.Client(api_key=api_key)
    try:
        # 异步流式：避免阻塞事件循环，且便于在 async 函数里直接 await broadcast。
        stream = await client.aio.models.generate_content_stream(
            model=model_name,
            contents=contents,
        )
        async for chunk in stream:
            piece = chunk.text or ""
            if piece:
                collected.append(piece)
                await hub.broadcast(session_id, "agent:delta", {"content": piece})
    except errors.ClientError as e:
        await hub.broadcast(session_id, "agent:error", {"message": _format_gemini_error(e)})
        return
    except Exception as e:  # noqa: BLE001
        await hub.broadcast(session_id, "agent:error", {"message": _format_gemini_error(e)})
        return
    finally:
        await client.aio.aclose()

    full = "".join(collected).strip()
    if not full:
        await hub.broadcast(
            session_id,
            "agent:error",
            {"message": "（模型未返回文本，可能被安全策略拦截。）"},
        )
        return

    await hub.broadcast(session_id, "agent:final", {})
    await _insert_message(db, lock, session_id, "assistant", full)
