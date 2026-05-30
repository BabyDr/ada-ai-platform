"""
HTTP 路由错误兜底（开发规范 §3.2）。

`register_global_exception_handler(app)`：为 FastAPI 注册未捕获异常 → 500 JSON。
SSE 任务生成器内须单独 try/except（见 api/task.py）。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

_log = logging.getLogger("adaagent")


def register_global_exception_handler(app: FastAPI) -> None:
    """注册全局异常 handler：HTTPException 保持原 status，其余返回 500 + detail。"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        _log.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": str(exc)[:800]})
