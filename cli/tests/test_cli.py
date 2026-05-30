"""CLI 单元测试（mock httpx，不依赖外部 Sidecar）。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from ai_app import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_list_includes_translate(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "functions": [
            {"id": "translate", "name": "翻译", "description": "多语言翻译"},
            {"id": "summarize", "name": "总结", "description": "要点总结"},
        ],
    }
    mock_resp.raise_for_status = MagicMock()
    monkeypatch.setattr("ai_app.httpx.get", lambda url, **kw: mock_resp)

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "translate" in result.output
    assert "summarize" in result.output


def test_translate_exit_code_zero(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        def iter_lines(self):
            yield 'data: {"content": "你好"}'
            yield 'data: {"taskId": "abc", "status": "done"}'

    class MockStreamCtx:
        def __enter__(self):
            return MockStreamResponse()

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr("ai_app.httpx.stream", lambda *a, **kw: MockStreamCtx())

    result = runner.invoke(
        cli,
        ["translate", "--text", "Hello", "--from", "en", "--to", "zh"],
    )
    assert result.exit_code == 0
    assert "你好" in result.output
