"""
HTTP 路由错误兜底（开发规范 §3.2 / #38 错误分级）。

`register_global_exception_handler(app)`：为 FastAPI 注册未捕获异常 → 500 JSON。
SSE 任务生成器内须单独 try/except（见 api/task.py）。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

_log = logging.getLogger("adaworks")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(
    detail: str,
    *,
    level: str,
    request_id: str | None = None,
    code: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"detail": detail, "level": level}
    if request_id:
        body["requestId"] = request_id
    if code:
        body["code"] = code
    return body


def register_global_exception_handler(app: FastAPI) -> None:
    """注册全局异常 handler：HTTPException 保持原 status，其余返回 500 + detail。"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        rid = _request_id(request)
        status = exc.status_code
        if status in (400, 422):
            level = "L1"
        elif status in (401, 403):
            level = "L4"
        elif status == 429:
            level = "L2"
        else:
            level = "L2" if status < 500 else "L3"
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=status,
            content=_error_body(detail, level=level, request_id=rid),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = _request_id(request)
        _log.exception("Unhandled error on %s [request_id=%s]", request.url.path, rid)
        return JSONResponse(
            status_code=500,
            content=_error_body("系统异常，请稍后重试", level="L3", request_id=rid),
        )
