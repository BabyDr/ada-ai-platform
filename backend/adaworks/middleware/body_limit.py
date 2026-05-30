"""请求体大小限制中间件（#47）。"""

from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_BODY_BYTES = 1_048_576  # 1MB


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """请求体大小限制中间件：检查 Content-Length 头，超过 1MB 返回 413。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """对 POST/PUT/PATCH 请求校验 Content-Length；缺失或格式错误时放行（由框架层兜底）。"""
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > MAX_BODY_BYTES:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request body too large", "level": "L1"},
                        )
                except (ValueError, OverflowError):
                    # Content-Length 值非法，返回 400 拒绝请求
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid Content-Length header"},
                    )
        return await call_next(request)
