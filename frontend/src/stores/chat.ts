/**
 * 对话领域 Pinia Store：会话列表、当前会话消息、模型 id、流式拼接状态。
 *
 * 数据流（建议对照 README 阅读）：
 * 1. 用户点击发送 → `sendUserMessage` POST /api/chat → 本地先插入 user 气泡；
 * 2. Sidecar 后台模型通过 WS 推送 `agent:delta` → `applyAgentEvent` 拼到同一条 assistant；
 * 3. `agent:final` → `loadMessages` 用服务端权威数据覆盖列表（含数据库里的 message id）。
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import type { ChatMessage, MessageRole, ServerMessage, Session } from "@/types/chat";
import { createSession, getSessionMessages, getSessions, postChat } from "@/services/api";

/** 将服务端消息转为前端列表项 */
function fromServer(m: ServerMessage): ChatMessage {
  const meta = m.metadata;
  let metadata: ChatMessage["metadata"];
  if (meta && typeof meta === "object") {
    const tool = typeof meta.tool === "string" ? meta.tool : undefined;
    const params = meta.params && typeof meta.params === "object" ? (meta.params as Record<string, unknown>) : undefined;
    if (tool !== undefined || params !== undefined) {
      metadata = { tool, params };
    }
  }
  return {
    id: m.id,
    role: m.role as MessageRole,
    content: m.content,
    metadata,
  };
}

/** 对话域状态：会话、消息、当前模型（仅通过 services 访问网络） */
export const useChatStore = defineStore("chat", () => {
  const sessions = ref<Session[]>([]);
  const messages = ref<ChatMessage[]>([]);
  const activeSessionId = ref<string | null>(null);
  const currentModelId = ref("glm-4-flash");
  const loading = ref(false);
  /** 当前流式 assistant 气泡 id；与 agent:delta / agent:final 配对 */
  const streamingAssistantId = ref<string | null>(null);

  /** 拉取会话列表 */
  async function loadSessions() {
    loading.value = true;
    try {
      sessions.value = await getSessions();
    } finally {
      loading.value = false;
    }
  }

  /** 拉取当前会话消息并覆盖本地列表 */
  async function loadMessages(sessionId: string) {
    streamingAssistantId.value = null;
    const rows = await getSessionMessages(sessionId);
    messages.value = rows.map(fromServer);
  }

  /** 创建新会话并设为当前 */
  async function addSession(title?: string) {
    const s = await createSession(title);
    sessions.value = [s, ...sessions.value.filter((x) => x.id !== s.id)];
    activeSessionId.value = s.id;
    streamingAssistantId.value = null;
    messages.value = [];
  }

  /** 切换当前会话并加载历史 */
  async function selectSession(sessionId: string) {
    activeSessionId.value = sessionId;
    await loadMessages(sessionId);
  }

  /** 发送用户消息（HTTP）；ReAct 步骤由 WebSocket 写入 */
  async function sendUserMessage(text: string) {
    if (!activeSessionId.value) return;
    streamingAssistantId.value = null;
    const sid = activeSessionId.value;
    const ack = await postChat({
      session_id: sid,
      message: text,
      model_id: currentModelId.value,
    });
    messages.value.push({
      id: ack.message_id,
      role: "user",
      content: text,
    });
  }

  /**
   * 处理 Sidecar 下行事件（spec §5.2）。
   * - `agent:delta`：流式正文片段；
   * - `agent:final`：本轮结束，清空 streamingAssistantId 并拉全量消息；
   * - `agent:error`：展示错误文案。
   */
  function applyAgentEvent(type: string, payload: Record<string, unknown>) {
    const genId = () => crypto.randomUUID();

    if (type === "agent:think") {
      messages.value.push({
        id: genId(),
        role: "think",
        content: String(payload.content ?? ""),
      });
      return;
    }
    if (type === "agent:act") {
      const tool = String(payload.tool ?? "");
      const params = (payload.params as Record<string, unknown>) ?? {};
      messages.value.push({
        id: genId(),
        role: "act",
        content: `调用工具 ${tool}`,
        metadata: { tool, params },
      });
      return;
    }
    if (type === "agent:observe") {
      messages.value.push({
        id: genId(),
        role: "observe",
        content: String(payload.result ?? ""),
      });
      return;
    }
    if (type === "agent:delta") {
      const piece = String(payload.content ?? "");
      if (!piece) return;
      const streamId = streamingAssistantId.value;
      if (!streamId) {
        const nid = genId();
        streamingAssistantId.value = nid;
        messages.value.push({ id: nid, role: "assistant", content: piece });
        return;
      }
      const row = messages.value.find((m) => m.id === streamId);
      if (row) {
        row.content += piece;
      } else {
        const nid = genId();
        streamingAssistantId.value = nid;
        messages.value.push({ id: nid, role: "assistant", content: piece });
      }
      return;
    }
    if (type === "agent:final") {
      streamingAssistantId.value = null;
      const sid = activeSessionId.value;
      if (sid) {
        void loadMessages(sid);
      }
      return;
    }
    if (type === "agent:error") {
      streamingAssistantId.value = null;
      messages.value.push({
        id: genId(),
        role: "assistant",
        content: `错误：${String(payload.message ?? "unknown")}`,
      });
    }
  }

  return {
    sessions,
    messages,
    activeSessionId,
    currentModelId,
    loading,
    loadSessions,
    loadMessages,
    addSession,
    selectSession,
    sendUserMessage,
    applyAgentEvent,
  };
});
