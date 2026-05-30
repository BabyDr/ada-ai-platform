/**
 * SSE 流式解析 composable（fetch + ReadableStream，不引入 eventsource 库）。
 *
 * 解析后端事件：task_start / token / task_done / task_error。
 * - result：逐 token 追加的原始文本（打字机效果数据源）。
 * - currentTaskId：task_start 携带，供取消使用。
 * - 用户主动 abort 不计入 error。
 */
import { ref } from "vue";
import { createTaskSSE } from "../services/linguistApi";

export interface SSEHandlers {
  onStart?: (taskId: string) => void;
  onToken?: (content: string) => void;
  onDone?: (payload: { taskId: string; status: string; duration?: string; result?: unknown }) => void;
  onError?: (message: string) => void;
}

export function useSSE() {
  const result = ref("");
  const isStreaming = ref(false);
  const error = ref("");
  const currentTaskId = ref("");
  let abortController: AbortController | null = null;

  function dispatch(event: string, dataStr: string, handlers: SSEHandlers) {
    let data: Record<string, unknown> = {};
    try {
      data = dataStr ? JSON.parse(dataStr) : {};
    } catch {
      return;
    }
    switch (event) {
      case "task_start":
        currentTaskId.value = String(data.taskId ?? "");
        handlers.onStart?.(currentTaskId.value);
        break;
      case "token":
        if (typeof data.content === "string") {
          result.value += data.content;
          handlers.onToken?.(data.content);
        }
        break;
      case "task_done":
        handlers.onDone?.(data as { taskId: string; status: string; duration?: string; result?: unknown });
        break;
      case "task_error":
        error.value = String(data.message ?? "任务执行失败");
        handlers.onError?.(error.value);
        break;
    }
  }

  async function startSSE(body: { type: string; params: Record<string, unknown> }, handlers: SSEHandlers = {}) {
    result.value = "";
    error.value = "";
    currentTaskId.value = "";
    isStreaming.value = true;
    abortController = new AbortController();

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

        // 按 SSE 规范以空行分隔事件；逐行解析 event:/data:。
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
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // 用户主动取消，不算错误。
      } else {
        error.value = e instanceof Error ? e.message : String(e);
        handlers.onError?.(error.value);
      }
    } finally {
      isStreaming.value = false;
      abortController = null;
    }
  }

  function stop() {
    abortController?.abort();
    isStreaming.value = false;
  }

  return { result, isStreaming, error, currentTaskId, startSSE, stop };
}
