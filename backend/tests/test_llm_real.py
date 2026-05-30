"""real 流式：MockTransport 单测 + 有密钥时可选真连集成测试。"""

from __future__ import annotations

import asyncio
import os

import httpx
import pytest

from adaworks.services import llm as llm_mod

_HAS_GLM_KEY = bool(os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPU_API_KEY"))


def _fake_sse_body() -> bytes:
    chunks = [
        b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":" world"}}], "finish_reason":"stop"}\n\n',
        b"data: [DONE]\n\n",
    ]
    return b"".join(chunks)


def test_real_stream_parses_mock_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """MockTransport 伪造 OpenAI 兼容 SSE，断言 token 拼接正确。"""
    monkeypatch.setenv("GLM_API_KEY", "sk-test")
    monkeypatch.setattr(llm_mod.settings, "llm_mode", "real")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/chat/completions")
        assert request.headers.get("Authorization") == "Bearer sk-test"
        return httpx.Response(200, content=_fake_sse_body())

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    async def run() -> list[str]:
        svc = llm_mod.LLMService()
        return [t async for t in svc.stream("sys", "user", task_type="translate")]

    tokens = asyncio.run(run())
    assert "".join(tokens) == "Hello world"
    assert llm_mod.effective_mode() == "real"


def test_real_stream_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)

    async def run() -> None:
        svc = llm_mod.LLMService()
        async for _ in svc._real_stream("sys", "user"):
            pass

    with pytest.raises(RuntimeError, match="未配置"):
        asyncio.run(run())


@pytest.mark.skipif(not _HAS_GLM_KEY, reason="GLM_API_KEY / ZHIPU_API_KEY not set")
def test_real_glm_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    """有密钥时真连一次 GLM 流式接口（CI 无密钥自动跳过）。"""
    monkeypatch.setattr(llm_mod.settings, "llm_mode", "real")

    async def run() -> str:
        svc = llm_mod.LLMService()
        parts: list[str] = []
        async for token in svc.stream(
            "You are a concise assistant.",
            "Reply with exactly one word: OK",
            task_type="translate",
        ):
            parts.append(token)
            if len("".join(parts)) >= 2:
                break
        return "".join(parts)

    try:
        text = asyncio.run(run())
    except RuntimeError as exc:
        pytest.skip(f"GLM API unreachable: {exc}")
    assert text.strip()
