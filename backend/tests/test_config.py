"""配置默认值与环境变量覆盖。"""

from __future__ import annotations

import pytest


def test_default_mode() -> None:
    from adaagent.config import Settings

    s = Settings(_env_file=None)
    assert s.llm_mode == "mock"
    assert s.task_timeout_seconds == 60
    assert s.sidecar_port == 18765


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from adaagent.config import Settings

    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.setenv("TASK_TIMEOUT_SECONDS", "5")
    s = Settings(_env_file=None)
    assert s.llm_mode == "real"
    assert s.task_timeout_seconds == 5
