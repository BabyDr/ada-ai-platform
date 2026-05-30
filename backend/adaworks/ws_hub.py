"""
按会话分组的 WebSocket 广播（不含业务解析）。

设计意图：业务代码只关心「给某个 session_id 发事件」，不关心底层有多少个连接；
同一浏览器多标签会对应多条连接，broadcast 会全部送达。
"""

from __future__ import annotations

import json
from typing import Any

from starlette.websockets import WebSocket


class ChatHub:
    """管理 ws://.../ws/chat/{session_id} 的连接与下行事件。"""

    def __init__(self) -> None:
        # session_id -> 该会话下所有已 accept 的 WebSocket（可能多个标签页）。
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """接受 WebSocket 握手并将连接加入对应会话房间（支持同一浏览器多标签页）。"""
        await websocket.accept()
        self._rooms.setdefault(session_id, []).append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """从房间移除指定连接；房间为空时清理整个条目。"""
        room = self._rooms.get(session_id)
        if not room:
            return
        if websocket in room:
            room.remove(websocket)
        if not room:
            self._rooms.pop(session_id, None)

    async def broadcast(self, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """
        向该会话所有连接发送一条 JSON 文本帧。
        形状与前端约定一致：{ "type": "agent:delta", "payload": { ... } }。
        """
        body = json.dumps({"type": event_type, "payload": payload}, ensure_ascii=False)
        # 复制房间列表，避免迭代中修改原列表
        room = list(self._rooms.get(session_id, []))
        failed: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_text(body)
            except Exception:
                # 发送失败（客户端已断开）先收集，循环结束后批量移除
                failed.append(ws)
        for ws in failed:
            self.disconnect(session_id, ws)
