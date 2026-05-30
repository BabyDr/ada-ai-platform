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

  function resetSeqState() {
    lastSeq = 0;
    seenSeqs.clear();
  }

  function acceptTokenSeq(seq: unknown): boolean {
    if (typeof seq !== "number") return true;
    if (seq <= lastSeq || seenSeqs.has(seq)) return false;
    seenSeqs.add(seq);
    lastSeq = seq;
    return true;
  }

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

        let idx: number;
        while ((idx = buffer.indexOf("\n")) >= 0) {
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
      abortController = null;
    }
  }

  function stop() {
    userAborted = true;
    abortController?.abort();
    tokenBuffer?.stop();
    tokenBuffer = null;
    isStreaming.value = false;
  }

  return { result, isStreaming, error, currentTaskId, startSSE, stop };
}
