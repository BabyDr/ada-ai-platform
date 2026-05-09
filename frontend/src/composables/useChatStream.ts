/**
 * 组合式函数 useChatStream：把「当前会话 ID」与「WebSocket 长连接」绑在一起。
 *
 * - 订阅 spec §5.2 约定的事件，转给 Pinia `applyAgentEvent`；
 * - `watch(..., { immediate: true })`：有 sessionId 时立即 connect；切换会话先 close 再连新 URL；
 * - `onUnmounted` 关闭连接，避免泄漏或组件销毁后仍收消息。
 */
import { onUnmounted, watch, type Ref } from "vue";
import { useChatStore } from "@/stores/chat";
import { getChatWebSocketUrl } from "@/services/websocket";

export function useChatStream(activeSessionId: Ref<string | null>) {
  const store = useChatStore();
  let ws: WebSocket | null = null;

  function close() {
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  function connect(sessionId: string) {
    close();
    const url = getChatWebSocketUrl(sessionId);
    ws = new WebSocket(url);
    ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        // 与后端 ws_hub.broadcast 发出的结构一致：{ type, payload }
        const msg = JSON.parse(ev.data) as { type: string; payload: Record<string, unknown> };
        store.applyAgentEvent(msg.type, msg.payload ?? {});
      } catch {
        /* 忽略非 JSON */
      }
    };
  }

  watch(
    activeSessionId,
    (id) => {
      if (id) {
        connect(id);
      } else {
        close();
      }
    },
    { immediate: true },
  );

  onUnmounted(() => close());
}
