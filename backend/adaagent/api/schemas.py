"""任务契约的 Pydantic 请求/响应模型（参数校验，加分项 F15）。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from adaagent.api.validators import validate_text
from adaagent.linguist_service import _LANG_NAMES

ToneLiteral = Literal["Professional", "Conversational", "Technical", "Academic", "Creative"]
SummaryModeLiteral = Literal["points", "words"]

SOURCE_LANGS = frozenset(_LANG_NAMES.keys())
TARGET_LANGS = frozenset(k for k in _LANG_NAMES if k != "auto")


class TranslateParams(BaseModel):
    """翻译任务 params。"""

    text: str
    sourceLang: str = "auto"
    targetLang: str = "zh"
    tone: ToneLiteral = "Professional"

    @field_validator("text")
    @classmethod
    def check_text(cls, v: str) -> str:
        return validate_text(v)

    @model_validator(mode="after")
    def check_langs(self) -> TranslateParams:
        if self.sourceLang not in SOURCE_LANGS:
            raise ValueError(f"invalid sourceLang: {self.sourceLang}")
        if self.targetLang not in TARGET_LANGS:
            raise ValueError(f"invalid targetLang: {self.targetLang}")
        return self


class SummarizeParams(BaseModel):
    """总结任务 params。"""

    text: str
    summaryMode: SummaryModeLiteral = "points"
    keyPointsCount: int = Field(3, ge=3, le=10)
    wordLimit: int = Field(250, ge=50, le=2000)
    tone: ToneLiteral = "Professional"

    @field_validator("text")
    @classmethod
    def check_text(cls, v: str) -> str:
        return validate_text(v)


class TaskCreateRequest(BaseModel):
    """POST /api/task 请求体。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["translate", "summarize"] = Field(..., description="功能类型")
    params: dict[str, Any] = Field(default_factory=dict, description="功能参数，见 functions 描述")

    @model_validator(mode="after")
    def validate_params(self) -> TaskCreateRequest:
        if self.type == "translate":
            validated = TranslateParams.model_validate(self.params)
        else:
            validated = SummarizeParams.model_validate(self.params)
        self.params = validated.model_dump()
        return self


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
