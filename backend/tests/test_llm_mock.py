"""mock 流式：逐字 token，拼接非空，且不依赖外部网络/密钥。"""

from __future__ import annotations

import asyncio

from adaagent.services.llm import LLMService, effective_mode


def test_mock_mode_default() -> None:
    # 默认 LLM_MODE=mock，effective_mode 恒为 mock（与是否有 GLM 密钥无关）。
    assert effective_mode() == "mock"


def test_mock_stream_yields_tokens() -> None:
    async def run() -> list[str]:
        svc = LLMService()
        return [t async for t in svc.stream("sys", "user", task_type="translate")]

    tokens = asyncio.run(run())
    assert len(tokens) > 1
    assert "".join(tokens).strip()


def test_mock_summarize_is_json() -> None:
    import json

    async def run() -> str:
        svc = LLMService()
        return "".join([t async for t in svc.stream("sys", "user", task_type="summarize")])

    raw = asyncio.run(run())
    data = json.loads(raw)
    assert "overview" in data
    assert isinstance(data["keyPoints"], list)
