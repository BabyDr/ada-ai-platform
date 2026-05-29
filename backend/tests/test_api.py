"""Sidecar HTTP 与 WebSocket 行为自测。"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adaagent.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """每个用例独立 SQLite 文件。"""
    db_file = tmp_path / "test.db"
    app = create_app(db_file)
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["llm"] in ("glm", "gemini", "mock")
    assert "keyLoaded" in data
    assert isinstance(data["keyLoaded"], bool)


def test_linguist_logs(client: TestClient) -> None:
    r = client.get("/api/logs")
    assert r.status_code == 200
    logs = r.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1


def test_sessions_crud_and_messages(client: TestClient) -> None:
    r = client.get("/api/sessions")
    assert r.status_code == 200
    assert r.json()["sessions"] == []

    r = client.post("/api/sessions", json={})
    assert r.status_code == 200
    sess = r.json()["session"]
    sid = sess["id"]
    assert sess["title"] == "新会话"
    assert "updated_at" in sess

    r = client.get("/api/sessions")
    assert len(r.json()["sessions"]) == 1

    r = client.get(f"/api/sessions/{sid}/messages")
    assert r.status_code == 200
    assert r.json()["messages"] == []

    r = client.delete(f"/api/sessions/{sid}")
    assert r.json()["success"] is True
    r = client.get("/api/sessions")
    assert r.json()["sessions"] == []


def test_chat_triggers_mock_agent(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Agent 异步落库；不用同步 TestClient 阻塞 WS receive（会与后台 task 争用事件循环）。"""
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    r = client.post("/api/sessions", json={"title": "t1"})
    sid = r.json()["session"]["id"]

    r = client.post(
        "/api/chat",
        json={"session_id": sid, "message": "你好", "model_id": "mock-default"},
    )
    assert r.status_code == 200
    ack = r.json()
    assert ack["session_id"] == sid
    assert "message_id" in ack

    # mock_agent 累计 sleep 约 1.65s+，留足余量
    time.sleep(2.5)

    r = client.get(f"/api/sessions/{sid}/messages")
    roles = [m["role"] for m in r.json()["messages"]]
    assert "user" in roles
    assert "think" in roles
    assert "act" in roles
    assert "observe" in roles
    assert "assistant" in roles


def test_chat_unknown_session(client: TestClient) -> None:
    r = client.post(
        "/api/chat",
        json={"session_id": "nope", "message": "x", "model_id": "mock"},
    )
    assert r.status_code == 404
