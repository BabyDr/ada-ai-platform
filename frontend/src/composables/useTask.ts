/**
 * 任务编排 composable：提交 SSE 任务 + 取消（abort 本地流 + DELETE 后端任务）。
 */
import { useSSE, type SSEHandlers } from "./useSSE";
import { cancelTask } from "../services/linguistApi";
import { errorMessage } from "../utils/safeAsync";

export function useTask() {
  const { result, isStreaming, error, currentTaskId, startSSE, stop } = useSSE();

  /** 提交 SSE 任务；异常写入 error ref 并触发 handlers.onError。 */
  async function submitTask(
    type: string,
    params: Record<string, unknown>,
    handlers: SSEHandlers = {},
  ): Promise<void> {
    try {
      await startSSE({ type, params }, handlers);
    } catch (e) {
      const msg = errorMessage(e);
      error.value = msg;
      handlers.onError?.(msg);
      console.error("submitTask failed", e);
    }
  }

  /** 先中断本地流，再通知后端终止任务（取消闭环）。 */
  async function cancelCurrentTask(): Promise<void> {
    try {
      stop();
      if (currentTaskId.value) {
        await cancelTask(currentTaskId.value);
      }
    } catch (err) {
      console.warn("cancel task failed", err);
    }
  }

  return { result, isStreaming, error, submitTask, cancelCurrentTask };
}
