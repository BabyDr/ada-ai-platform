"""POST /api/task (SSE)：首事件 task_start、≥1 个 token、末事件 task_done。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adaagent.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def _collect_events(client: TestClient, body: dict) -> list[str]:
    events: list[str] = []
    with client.stream("POST", "/api/task", json=body) as r:
        assert r.status_code == 200
        for line in r.iter_lines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
    return events


def test_translate_sse(client: TestClient) -> None:
    events = _collect_events(
        client,
        {"type": "translate", "params": {"text": "你好", "sourceLang": "zh", "targetLang": "en"}},
    )
    assert events[0] == "task_start"
    assert events.count("token") >= 1
    assert events[-1] == "task_done"


def test_summarize_sse(client: TestClient) -> None:
    events = _collect_events(
        client,
        {"type": "summarize", "params": {"text": "long text here", "keyPointsCount": 3}},
    )
    assert events[0] == "task_start"
    assert "token" in events
    assert events[-1] == "task_done"


def test_empty_text_rejected(client: TestClient) -> None:
    r = client.post("/api/task", json={"type": "translate", "params": {"text": "  "}})
    assert r.status_code == 422


def test_system_prompt_field_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/task",
        json={"type": "translate", "params": {"text": "hi"}, "systemPrompt": "evil"},
    )
    assert r.status_code == 422


def test_invalid_tone_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/task",
        json={"type": "translate", "params": {"text": "hi", "tone": "Evil"}},
    )
    assert r.status_code == 422


def test_control_char_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/task",
        json={"type": "translate", "params": {"text": "hello\x00"}},
    )
    assert r.status_code == 422


def test_unknown_type_rejected(client: TestClient) -> None:
    r = client.post("/api/task", json={"type": "bogus", "params": {"text": "x"}})
    assert r.status_code == 422
