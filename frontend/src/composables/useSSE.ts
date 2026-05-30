/**
 * SSE 流式解析 composable（fetch + ReadableStream，不引入 eventsource 库）。
 */
import { ref } from "vue";
import { createTaskSSE } from "../services/linguistApi";
import { createStreamBuffer } from "./useStreamBuffer";

export interface SSEHandlers {
  onStart?: (taskId: string) => void;
  onToken?: (content: string) => void;
  onDone?: (payload: { taskId: string; status: string; duration?: string; result?: unknown }) => void;
  onError?: (message: string) => void;
}

const DISCONNECT_MSG = "连接已断开，请重新提交";
const MAX_BUFFER_SIZE = 10 * 1024 * 1024; // 10MB 安全上限

export function useSSE() {
  const result = ref("");
  const isStreaming = ref(false);
  const error = ref("");
  const currentTaskId = ref("");
  let abortController: AbortController | null = null;
  let settled = false;
  let userAborted = false;
  let tokenBuffer: ReturnType<typeof createStreamBuffer> | null = null;
  let lastSeq = 0;
  const seenSeqs = new Set<number>();

  /** 重置 token 序号去重状态（每次 startSSE 时调用）。 */
  function resetSeqState() {
    lastSeq = 0;
    seenSeqs.clear();
  }

  /**
   * 判定 token 序号是否可接受（单调递增 + 去重）。
   * 后端可能因重试导致重复 token，通过 seq 过滤避免前端重复展示。
   * seq 非 number 类型时（旧版后端兼容）直接放行。
   */
  function acceptTokenSeq(seq: unknown): boolean {
    if (typeof seq !== "number") return true;
    if (seq <= lastSeq || seenSeqs.has(seq)) return false;
    seenSeqs.add(seq);
    lastSeq = seq;
    return true;
  }

  /**
   * SSE 事件分发：将解析后的 event + data 分发到对应 handler。
   * 事件类型：task_start（任务开始）→ token（流式片段）→ task_done / task_error（终态）。
   * JSON 解析失败时触发 onError，忽略已 settled（终态）后的错误。
   */
  function dispatch(event: string, dataStr: string, handlers: SSEHandlers) {
    let data: Record<string, unknown> = {};
    try {
      data = dataStr ? JSON.parse(dataStr) : {};
    } catch {
      if (!settled) {
        const msg = "流式数据解析失败";
        error.value = msg;
        handlers.onError?.(msg);
      }
      return;
    }
    switch (event) {
      case "task_start":
        currentTaskId.value = String(data.taskId ?? "");
        handlers.onStart?.(currentTaskId.value);
        break;
      case "token":
        if (typeof data.content === "string" && acceptTokenSeq(data.seq)) {
          tokenBuffer?.push(data.content);
          handlers.onToken?.(data.content);
        }
        break;
      case "task_done":
        settled = true;
        tokenBuffer?.stop();
        tokenBuffer = null;
        handlers.onDone?.(data as { taskId: string; status: string; duration?: string; result?: unknown });
        break;
      case "task_error":
        settled = true;
        tokenBuffer?.stop();
        tokenBuffer = null;
        error.value = String(data.message ?? "任务执行失败");
        handlers.onError?.(error.value);
        break;
    }
  }

  /**
   * 发起 SSE 流式请求并实时解析事件。
   *
   * 流程：
   * 1. 通过 createTaskSSE 发起 fetch 请求，传入 AbortController 信号支持取消；
   * 2. 使用 ReadableStream 逐块读取，手动解析 SSE 协议（event:/data: 前缀 + \n 分隔）；
   * 3. 每解析出一行 data 调用 dispatch 分发到 handlers；
   * 4. 流结束但未收到 task_done/task_error 时触发断线错误；
   * 5. finally 中清理 buffer、中止 AbortController、重置状态。
   */
  async function startSSE(body: { type: string; params: Record<string, unknown> }, handlers: SSEHandlers = {}) {
    if (isStreaming.value) return;

    result.value = "";
    error.value = "";
    currentTaskId.value = "";
    settled = false;
    userAborted = false;
    resetSeqState();
    isStreaming.value = true;
    abortController = new AbortController();
    tokenBuffer = createStreamBuffer((chunk) => {
      result.value += chunk;
    });

    try {
      const response = await createTaskSSE(body, abortController.signal);
      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const j = await response.json();
          detail = (j.detail as string) || (j.message as string) || detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No readable stream");
      const decoder = new TextDecoder();

      let buffer = "";
      let eventName = "message";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        if (buffer.length > MAX_BUFFER_SIZE) {
          throw new Error("SSE response exceeds maximum buffer size");
        }

        let idx: number;
        while ((idx = buffer.indexOf("\n")) >= 0) {
          try {
            const line = buffer.slice(0, idx).replace(/\r$/, "");
            buffer = buffer.slice(idx + 1);
            if (line === "") {
              eventName = "message";
              continue;
            }
            if (line.startsWith("event:")) {
              eventName = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              dispatch(eventName, line.slice(5).trim(), handlers);
            }
          } catch (err) {
            console.warn("[useSSE] failed to parse SSE line:", err);
            eventName = "message";
          }
        }
      }

      if (!settled && !userAborted) {
        error.value = DISCONNECT_MSG;
        handlers.onError?.(DISCONNECT_MSG);
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") {
        userAborted = true;
      } else if (!settled) {
        error.value = e instanceof Error ? e.message : String(e);
        handlers.onError?.(error.value);
      }
    } finally {
      tokenBuffer?.stop();
      tokenBuffer = null;
      isStreaming.value = false;
      if (abortController) {
        abortController.abort();
        abortController = null;
      }
    }
  }

  /** 用户主动中止：标记 userAborted，中止请求，清理 buffer，重置状态。供「取消」按钮调用。 */
  function stop() {
    userAborted = true;
    abortController?.abort();
    abortController = null;
    tokenBuffer?.stop();
    tokenBuffer = null;
    isStreaming.value = false;
  }

  return { result, isStreaming, error, currentTaskId, startSSE, stop };
}
