/**
 * Sidecar HTTP 客户端（浏览器 fetch）。
 *
 * 与 WebSocket 的分工：发消息用 POST（拿到 message_id），模型生成过程走 WS 事件。
 * 根路径来自 Vite 环境变量，开发时见 `frontend/.env.development`。
 */
import type { ChatAck, ChatRequest, ServerMessage, Session } from "@/types/chat";

/** Sidecar HTTP 根路径（与 spec §8.2、.env.development 一致） */
const BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:18765/api";

/** 发送用户消息，触发 Agent（过程由 WebSocket 推送） */
export async function postChat(body: ChatRequest): Promise<ChatAck> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`chat failed: ${res.status}`);
  return res.json() as Promise<ChatAck>;
}

/** 拉取会话列表 */
export async function getSessions(): Promise<Session[]> {
  const res = await fetch(`${BASE}/sessions`);
  if (!res.ok) throw new Error(`sessions failed: ${res.status}`);
  const data = (await res.json()) as { sessions: Session[] };
  return data.sessions;
}

/** 创建会话 */
export async function createSession(title?: string): Promise<Session> {
  const res = await fetch(`${BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title ?? undefined }),
  });
  if (!res.ok) throw new Error(`create session failed: ${res.status}`);
  const data = (await res.json()) as { session: Session };
  return data.session;
}

/** 拉取会话消息 */
export async function getSessionMessages(sessionId: string): Promise<ServerMessage[]> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error(`messages failed: ${res.status}`);
  const data = (await res.json()) as { messages: ServerMessage[] };
  return data.messages;
}
