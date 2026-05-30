"""任务契约的 Pydantic 请求/响应模型（参数校验，加分项 F15）。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """POST /api/task 请求体。"""

    type: Literal["translate", "summarize"] = Field(..., description="功能类型")
    params: dict[str, Any] = Field(default_factory=dict, description="功能参数，见 functions 描述")


class FunctionItem(BaseModel):
    """单个可用功能的描述（供 CLI / Agent 发现）。"""

    id: str
    name: str
    description: str
    params: dict[str, Any] | None = None


class FunctionsResponse(BaseModel):
    functions: list[FunctionItem]


class CancelResponse(BaseModel):
    message: str
    taskId: str
