/** 与会话列表 API 对齐 */
export interface Session {
  id: string;
  title: string;
  updated_at: string;
}

/** 消息角色：用户/助手 + ReAct 步骤（与 spec §6.2 一致） */
export type MessageRole = "user" | "assistant" | "think" | "act" | "observe";

/** 单条消息（含可选元数据，如 act 的工具参数） */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  metadata?: {
    tool?: string;
    params?: Record<string, unknown>;
  };
}

/** POST /api/chat 请求体 */
export interface ChatRequest {
  session_id: string;
  message: string;
  model_id: string;
}

/** POST /api/chat 响应 */
export interface ChatAck {
  session_id: string;
  message_id: string;
}

/** GET /api/sessions/:id/messages 中单条（服务端 metadata 可能为 null） */
export interface ServerMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}
