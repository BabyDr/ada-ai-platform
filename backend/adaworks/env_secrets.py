"""
环境变量中的密钥：支持 JSON 字符串数组，使用时拼接为单个字符串。

示例：GLM_API_KEY='["sk-头","尾"]' → 实际请求使用 sk-头尾。
用于在不改代码的前提下拆分存储（注意：不是加密，只是分段）。
"""

from __future__ import annotations

import json
import os


def coalesce_key_from_env_value(raw: str | None) -> str | None:
    """
    将 env 中的值解析为密钥字符串。

    - 若为 JSON 数组且元素均为字符串，则按顺序拼接（无分隔符）。
    - 否则视为整条密钥（兼容旧写法）。
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed: object = json.loads(s)
        except json.JSONDecodeError:
            return s
        if isinstance(parsed, list) and parsed and all(isinstance(x, str) for x in parsed):
            return "".join(parsed)
        return None
    return s


def read_first_secret(*env_names: str) -> str | None:
    """按顺序读取若干环境变量名，返回第一个解析出非空密钥的结果。"""
    for name in env_names:
        v = coalesce_key_from_env_value(os.environ.get(name))
        if v:
            return v
    return None
