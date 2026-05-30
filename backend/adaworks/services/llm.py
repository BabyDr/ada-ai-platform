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
import re
from typing import AsyncIterator

import httpx

from adaworks.config import settings
from adaworks.api.validators import sanitize_upstream_message
from adaworks.env_secrets import read_first_secret
from adaworks.glm_agent import DEFAULT_GLM_BASE, DEFAULT_GLM_MODEL

_MOCK_TRANSLATE_BY_TARGET: dict[str, str] = {
    "Chinese (Simplified)": "这是本地模拟的逐字翻译流，用于零配置演示。",
    "English": "This is a mock streaming translation generated locally without any API key.",
    "Japanese": "これは API キーなしでローカル生成されるモック翻訳ストリームです。",
    "Korean": "API 키 없이 로컬에서 생성되는 모의 번역 스트림입니다.",
    "French": "Traduction simulée localement sans clé API.",
    "Spanish": "Traducción simulada localmente sin clave API.",
    "German": "Lokal simulierte Übersetzung ohne API-Schlüssel.",
    "Russian": "Локальный имитационный перевод без API-ключа.",
    "Italian": "Traduzione simulata localmente senza chiave API.",
}
_MOCK_TRANSLATE_DEFAULT = (
    "This is a mock streaming translation generated locally without any API key. "
    "这是本地模拟的逐字翻译流，用于零配置演示。"
)
_MOCK_SUMMARIZE = json.dumps(
    {
        "overview": "这是本地模拟的概述摘要，用于零配置演示。",
        "keyPoints": [
            "Mock 模式逐字流式输出 token，模拟真实 SSE。",
            "无需外部网络或 API 密钥即可联调。",
            "配置 LLM_MODE=real 与 GLM 密钥后可调用真实模型。",
        ],
    },
    ensure_ascii=False,
)
_MOCK_SUMMARIZE_WORDS = json.dumps(
    {
        "overview": "这是本地模拟的字数概要总结，用于零配置演示，无需 API 密钥。",
        "keyPoints": [],
    },
    ensure_ascii=False,
)


def _glm_key() -> str | None:
    """读取 GLM API 密钥，支持 GLM_API_KEY 和 ZHIPU_API_KEY 两种环境变量名。"""
    return read_first_secret("GLM_API_KEY", "ZHIPU_API_KEY")


def _glm_base() -> str:
    """获取 GLM API 网关地址，可通过 GLM_API_BASE 环境变量覆盖默认值。"""
    return (os.environ.get("GLM_API_BASE") or DEFAULT_GLM_BASE).rstrip("/")


def _glm_model() -> str:
    """获取 GLM 模型名称，可通过 GLM_MODEL 环境变量覆盖默认值。"""
    return (os.environ.get("GLM_MODEL") or DEFAULT_GLM_MODEL).strip() or DEFAULT_GLM_MODEL


def effective_mode() -> str:
    """实际生效模式：real 需同时满足 LLM_MODE=real 且有 GLM 密钥。"""
    if settings.llm_mode == "real" and _glm_key():
        return "real"
    return "mock"


class LLMService:
    """翻译 / 总结统一流式入口。"""

    def __init__(self) -> None:
        self.last_finish_reason: str | None = None

    async def stream(self, system: str, user: str, *, task_type: str = "translate") -> AsyncIterator[str]:
        self.last_finish_reason = None
        if effective_mode() == "mock":
            async for token in self._mock_stream(task_type, system):
                yield token
        else:
            async for token in self._real_stream(system, user):
                yield token

    async def _mock_stream(self, task_type: str, system: str) -> AsyncIterator[str]:
        """逐字返回预设文本，模拟真实 SSE 节奏。"""
        if task_type == "summarize":
            text = _MOCK_SUMMARIZE_WORDS if "no bullet points" in system else _MOCK_SUMMARIZE
        else:
            text = _mock_translate_text(system)
        for char in text:
            yield char
            await asyncio.sleep(0.02)

    async def _real_stream(self, system: str, user: str) -> AsyncIterator[str]:
        """
        调用 GLM OpenAI 兼容接口，逐段 yield delta.content。

        内建一次重试：当模型返回「繁忙」错误时等待 1 秒后重试，其他错误直接抛出。
        """
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
            "max_tokens": 8000,
        }

        # 最多重试 1 次：首次遇到「繁忙」时 sleep 后重跑
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                async for piece in self._read_upstream_stream(url, headers, body):
                    yield piece
                return
            except RuntimeError as e:
                last_error = e
                msg = str(e)
                if attempt == 0 and "繁忙" in msg:
                    # 仅在首次遇到「繁忙」时重试，避免无限循环
                    await asyncio.sleep(1.0)
                    continue
                raise
            except httpx.HTTPError as e:
                raise RuntimeError("模型连接中断，请稍后重试") from e
        if last_error:
            raise last_error

    async def _read_upstream_stream(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, object],
    ) -> AsyncIterator[str]:
        """读取上游 SSE 流，逐行解析 data 字段，yield delta.content 片段。"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream("POST", url, headers=headers, json=body) as r:
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError:
                    # 流式接口在连接建立后仍可返回 4xx，读取 body 便于排错
                    err_body = (await r.aread()).decode(errors="replace")[:800]
                    raise RuntimeError(sanitize_upstream_message(r.status_code, err_body)) from None

                # 逐行解析 SSE：data: {...} 或 data:{...}，[DONE] 标记流结束
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
                    # 上游错误：直接抛出，由调用方决定是否重试
                    err = obj.get("error")
                    if isinstance(err, dict) and err.get("message"):
                        raise RuntimeError("模型服务异常，请稍后重试")
                    # 提取 delta.content 并记录 finish_reason（用于截断检测）
                    for ch in obj.get("choices") or []:
                        reason = ch.get("finish_reason")
                        if isinstance(reason, str):
                            self.last_finish_reason = reason
                        piece = (ch.get("delta") or {}).get("content") or ""
                        if piece:
                            yield str(piece)


def _mock_translate_text(system: str) -> str:
    """从翻译 system prompt 提取目标语言，返回对应 mock 译文。"""
    match = re.search(r"to '([^']+)'", system)
    target = match.group(1) if match else ""
    return _MOCK_TRANSLATE_BY_TARGET.get(target, _MOCK_TRANSLATE_DEFAULT)


llm_service = LLMService()
