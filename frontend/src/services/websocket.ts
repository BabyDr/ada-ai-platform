/**
 * WebSocket 与 Sidecar 地址相关的纯函数（无 Vue、无组件）。
 * 实际连接与事件分发在 composables/useChatStream.ts。
 */

/** 拼接 spec §5.2 约定的对话 WebSocket URL */
export function getChatWebSocketUrl(sessionId: string): string {
  const base = import.meta.env.VITE_WS_BASE ?? "ws://127.0.0.1:18765";
  return `${base.replace(/\/$/, "")}/ws/chat/${sessionId}`;
}
