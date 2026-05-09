"""
加载 .env：先仓库根目录，再 backend（后者覆盖同名变量）。

这样团队可以把「个人密钥」放在仓库根 .gitignore 的 .env，
而把不含密钥的默认项放在 backend/.env.example 供复制。
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_app_dotenv() -> None:
    """AdaAgent/.env 与 backend/.env 均会读取，便于把密钥放在仓库根。"""
    backend_dir = Path(__file__).resolve().parent.parent
    repo_root = backend_dir.parent
    load_dotenv(repo_root / ".env")
    load_dotenv(backend_dir / ".env", override=True)
