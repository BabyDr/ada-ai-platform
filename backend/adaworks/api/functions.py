"""GET /api/functions —— 返回可用功能列表（供 CLI / skill.md / Agent 发现；前端工作台不依赖）。"""

from __future__ import annotations

from fastapi import APIRouter

from adaworks.api.schemas import FunctionItem, FunctionsResponse

router = APIRouter()

FUNCTIONS: list[FunctionItem] = [
    FunctionItem(
        id="translate",
        name="文本翻译",
        description="多语言翻译，支持源/目标语言与语调（10 种语言 + 5 种语调）。",
        params={
            "text": "string",
            "sourceLang": "string (auto|en|zh|es|fr|ja|de|ko|ru|it)",
            "targetLang": "string",
            "tone": "string (Professional|Conversational|Technical|Academic|Creative)",
        },
    ),
    FunctionItem(
        id="summarize",
        name="智能要点总结",
        description="长文本总结，支持按要点 / 按字数两种模式。",
        params={
            "text": "string",
            "summaryMode": "string (points|words)",
            "keyPointsCount": "number (points 模式)",
            "wordLimit": "number (points=每条要点字数, words=概要字数上限)",
            "tone": "string",
        },
    ),
]


@router.get("/functions", response_model=FunctionsResponse)
async def get_functions() -> FunctionsResponse:
    """返回 translate / summarize 两项能力描述（SSE task type，非独立 REST 路径）。"""
    return FunctionsResponse(functions=FUNCTIONS)
