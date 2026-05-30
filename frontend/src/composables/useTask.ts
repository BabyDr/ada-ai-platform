/**
 * 任务编排 composable：提交 SSE 任务 + 取消（abort 本地流 + DELETE 后端任务）。
 */
import { useSSE, type SSEHandlers } from "./useSSE";
import { cancelTask } from "../services/linguistApi";

export function useTask() {
  const { result, isStreaming, error, currentTaskId, startSSE, stop } = useSSE();

  async function submitTask(
    type: string,
    params: Record<string, unknown>,
    handlers: SSEHandlers = {},
  ) {
    await startSSE({ type, params }, handlers);
  }

  async function cancelCurrentTask() {
    // 先中断本地流，再通知后端终止任务（取消闭环）。
    stop();
    if (currentTaskId.value) {
      try {
        await cancelTask(currentTaskId.value);
      } catch (err) {
        console.warn("cancel task failed", err);
      }
    }
  }

  return { result, isStreaming, error, currentTaskId, submitTask, cancelCurrentTask };
}
