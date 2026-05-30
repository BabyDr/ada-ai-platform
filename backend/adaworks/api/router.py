"""聚合 functions + task 子路由；由 main.create_app 以 prefix=/api 挂载。"""

from __future__ import annotations

from fastapi import APIRouter

from adaworks.api.functions import router as functions_router
from adaworks.api.task import router as task_router

api_router = APIRouter()
api_router.include_router(functions_router)
api_router.include_router(task_router)
