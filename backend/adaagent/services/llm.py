"""
统一 LLM 流式调用层。

对外暴露 `LLMService.stream(system, user, *, task_type)`，返回 `AsyncIterator[str]`：
- mock 模式：本地预设逐字流，前端 / CLI 联调不依赖任何外部网络与密钥。
- real 模式：复用现有 GLM（OpenAI 兼容 /chat/completions, stream=true）SSE 解析。

模式判定（与决策 A 一致）：
- `settings.llm_mode == "real"` 且检测到 GLM 密钥 → real（GLM 流式）。
- 否则一律 mock，保证零配置可演示。
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncIterator

import httpx

from adaagent.config import settings
from adaagent.env_secrets import read_first_secret
from adaagent.glm_agent import DEFAULT_GLM_BASE, DEFAULT_GLM_MODEL

_MOCK_TRANSLATE = "This is a mock streaming translation generated locally without any API key. 这是本地模拟的逐字翻译流，用于零配置演示。"
_MOCK_SUMMARIZE = json.dumps(
    {
        "overview": "This is a mock summary produced locally for demonstration without an API key.",
        "keyPoints": [
            "Mock mode streams tokens char by char to mimic real SSE.",
            "No external network or API key is required.",
            "Set LLM_MODE=real with a GLM key to call the real model.",
        ],
    },
    ensure_ascii=False,
)


def _glm_key() -> str | None:
    return read_first_secret("GLM_API_KEY", "ZHIPU_API_KEY")


def _glm_base() -> str:
    return (os.environ.get("GLM_API_BASE") or DEFAULT_GLM_BASE).rstrip("/")


def _glm_model() -> str:
    return (os.environ.get("GLM_MODEL") or DEFAULT_GLM_MODEL).strip() or DEFAULT_GLM_MODEL


def effective_mode() -> str:
    """实际生效模式：real 需同时满足 LLM_MODE=real 且有 GLM 密钥。"""
    if settings.llm_mode == "real" and _glm_key():
        return "real"
    return "mock"


class LLMService:
    """翻译 / 总结统一流式入口。"""

    async def stream(self, system: str, user: str, *, task_type: str = "translate") -> AsyncIterator[str]:
        if effective_mode() == "mock":
            async for token in self._mock_stream(task_type):
                yield token
        else:
            async for token in self._real_stream(system, user):
                yield token

    async def _mock_stream(self, task_type: str) -> AsyncIterator[str]:
        """逐字返回预设文本，模拟真实 SSE 节奏。"""
        text = _MOCK_SUMMARIZE if task_type == "summarize" else _MOCK_TRANSLATE
        for char in text:
            yield char
            await asyncio.sleep(0.02)

    async def _real_stream(self, system: str, user: str) -> AsyncIterator[str]:
        """复用 GLM OpenAI 兼容流式接口，逐段 yield delta.content。"""
        api_key = _glm_key()
        if not api_key:
            raise RuntimeError("GLM_API_KEY 或 ZHIPU_API_KEY 未配置")

        url = f"{_glm_base()}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": _glm_model(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream("POST", url, headers=headers, json=body) as r:
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError:
                    err_body = (await r.aread()).decode(errors="replace")[:800]
                    raise RuntimeError(f"GLM HTTP {r.status_code}: {err_body}") from None

                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        payload = line[6:].strip()
                    elif line.startswith("data:"):
                        payload = line[5:].strip()
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
                        piece = (ch.get("delta") or {}).get("content") or ""
                        if piece:
                            yield piece


llm_service = LLMService()
