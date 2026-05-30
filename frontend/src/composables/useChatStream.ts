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

/** 后端 ws_hub.broadcast 下发的合法事件类型 */
const VALID_AGENT_EVENTS = new Set([
  "agent:think",
  "agent:act",
  "agent:observe",
  "agent:delta",
  "agent:final",
  "agent:error",
]);

export function useChatStream(activeSessionId: Ref<string | null>) {
  const store = useChatStore();
  let ws: WebSocket | null = null;

  /** 关闭当前 WebSocket 连接（会话切换或组件卸载时调用）。 */
  function close() {
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  /**
   * 建立新 WebSocket 连接：先关闭旧连接，再按 sessionId 拼接 WS URL 连接。
   * onmessage 中校验事件类型白名单后分发给 Pinia store。
   */
  function connect(sessionId: string) {
    close();
    const url = getChatWebSocketUrl(sessionId);
    ws = new WebSocket(url);
    ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        const msg = JSON.parse(ev.data) as { type: string; payload: Record<string, unknown> };
        if (typeof msg.type !== "string" || !VALID_AGENT_EVENTS.has(msg.type)) {
          console.warn("[useChatStream] unexpected event type:", msg.type);
          return;
        }
        store.applyAgentEvent(msg.type, msg.payload ?? {});
      } catch (err) {
        console.warn("[useChatStream] failed to parse WS message:", err);
      }
    };
    ws.onerror = () => {
      console.error("[useChatStream] WebSocket error");
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
