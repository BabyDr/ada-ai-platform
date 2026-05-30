/**
 * Sidecar HTTP 客户端（Agent Chat 会话与消息）。
 *
 * 与 WebSocket 的分工：发消息用 POST（拿到 message_id），模型生成过程走 WS 事件。
 * 所有请求均含 try/catch 兜底（开发规范 §3.1）。
 */
import type { ChatAck, ChatRequest, ServerMessage, Session } from "@/types/chat";
import { errorMessage } from "@/utils/safeAsync";

/** Sidecar HTTP 根路径（与 spec §8.2、.env.development 一致） */
const BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

/** 包装 fetch：失败时抛出带 HTTP 状态或网络原因的 Error。 */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, init);
    if (!res.ok) {
      throw new Error(`request failed: ${path} HTTP ${res.status}`);
    }
    return (await res.json()) as T;
  } catch (e) {
    throw new Error(errorMessage(e));
  }
}

/** 发送用户消息，触发 Agent（过程由 WebSocket 推送） */
export async function postChat(body: ChatRequest): Promise<ChatAck> {
  return requestJson<ChatAck>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/** 拉取会话列表 */
export async function getSessions(): Promise<Session[]> {
  const data = await requestJson<{ sessions: Session[] }>("/sessions");
  return data.sessions;
}

/** 创建会话 */
export async function createSession(title?: string): Promise<Session> {
  const data = await requestJson<{ session: Session }>("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title ?? undefined }),
  });
  return data.session;
}

/** 拉取会话消息 */
export async function getSessionMessages(sessionId: string): Promise<ServerMessage[]> {
  const data = await requestJson<{ messages: ServerMessage[] }>(`/sessions/${sessionId}/messages`);
  return data.messages;
}
