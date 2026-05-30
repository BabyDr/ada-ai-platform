"""env_secrets：JSON 字符串数组拼接为密钥。"""

from __future__ import annotations

import pytest

from adaworks.env_secrets import coalesce_key_from_env_value, read_first_secret


def test_coalesce_plain_string() -> None:
    assert coalesce_key_from_env_value("  sk-abc  ") == "sk-abc"


def test_coalesce_json_string_array() -> None:
    assert coalesce_key_from_env_value('["hel","lo"]') == "hello"


def test_coalesce_empty_and_none() -> None:
    assert coalesce_key_from_env_value(None) is None
    assert coalesce_key_from_env_value("") is None
    assert coalesce_key_from_env_value("   ") is None


def test_read_first_secret_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("A", '["x","y"]')
    monkeypatch.setenv("B", "only-b")
    assert read_first_secret("A", "B") == "xy"
    monkeypatch.delenv("A", raising=False)
    assert read_first_secret("A", "B") == "only-b"
