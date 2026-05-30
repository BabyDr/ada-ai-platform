/**
 * WebSocket 与 Sidecar 地址相关的纯函数（无 Vue、无组件）。
 * 实际连接与事件分发在 composables/useChatStream.ts。
 */

/** 拼接 spec §5.2 约定的对话 WebSocket URL */
export function getChatWebSocketUrl(sessionId: string): string {
  const configured = import.meta.env.VITE_WS_BASE?.trim();
  if (configured) {
    return `${configured.replace(/\/$/, "")}/ws/chat/${sessionId}`;
  }
  // 开发默认走当前页面 host，Vite 将 /ws 代理到 Sidecar（支持局域网手机访问）
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/chat/${sessionId}`;
}
