"""日志脱敏与分页测试（#7 #32 #34）。"""

from __future__ import annotations

from adaagent.linguist_service import add_log, list_logs, logs_db
from adaagent.services.log_sanitize import redact_secrets


def test_redact_api_key() -> None:
    raw = "failed with sk-abcdefghijklmnopqrstuvwxyz"
    assert "sk-" not in redact_secrets(raw)
    assert "[REDACTED]" in redact_secrets(raw)


def test_list_logs_pagination() -> None:
    before = len(logs_db)
    result = list_logs(page=1, size=2)
    assert result["page"] == 1
    assert result["size"] == 2
    assert len(result["items"]) <= 2
    assert result["total"] >= before


def test_add_log_redacts_secrets() -> None:
    log = add_log({"type": "translation", "input": "key sk-1234567890123456", "output": "ok", "status": "success"})
    assert "sk-" not in log["input"]
    assert "[REDACTED]" in log["input"]
