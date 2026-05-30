"""GET /api/functions 返回 translate + summarize 两项。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adaworks.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def test_functions(client: TestClient) -> None:
    r = client.get("/api/functions")
    assert r.status_code == 200
    funcs = r.json()["functions"]
    assert len(funcs) == 2
    ids = {f["id"] for f in funcs}
    assert ids == {"translate", "summarize"}
