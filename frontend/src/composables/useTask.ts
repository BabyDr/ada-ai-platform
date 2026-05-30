/**
 * 任务编排 composable：提交 SSE 任务 + 取消（abort 本地流 + DELETE 后端任务）。
 */
import { useSSE, type SSEHandlers } from "./useSSE";
import { cancelTask, fetchHealth } from "../services/linguistApi";
import { useWorkspaceStore } from "../stores/workspace";
import { errorMessage } from "../utils/safeAsync";
import { clearPersistedTask, persistActiveTask } from "../utils/taskPersistence";

export function useTask() {
  const workspace = useWorkspaceStore();
  const { result, isStreaming, error, currentTaskId, startSSE, stop } = useSSE();

  /** 提交 SSE 任务；异常写入 error ref 并触发 handlers.onError。 */
  async function submitTask(
    type: string,
    params: Record<string, unknown>,
    handlers: SSEHandlers = {},
  ): Promise<void> {
    if (isStreaming.value) return;

    try {
      await fetchHealth();
    } catch {
      const msg = "服务未就绪，请确认 Sidecar 已启动";
      error.value = msg;
      handlers.onError?.(msg);
      return;
    }

    workspace.setLinguistStreaming(true, cancelCurrentTask);

    const wrapped: SSEHandlers = {
      ...handlers,
      onStart: (taskId) => {
        workspace.setActiveTaskId(taskId);
        persistActiveTask(taskId, type);
        handlers.onStart?.(taskId);
      },
      onDone: (payload) => {
        workspace.setLinguistStreaming(false);
        workspace.clearActiveTaskId();
        clearPersistedTask();
        handlers.onDone?.(payload);
      },
      onError: (message) => {
        workspace.setLinguistStreaming(false);
        workspace.clearActiveTaskId();
        clearPersistedTask();
        handlers.onError?.(message);
      },
    };

    try {
      await startSSE({ type, params }, wrapped);
    } catch (e) {
      workspace.setLinguistStreaming(false);
      const msg = errorMessage(e);
      error.value = msg;
      handlers.onError?.(msg);
      console.error("submitTask failed", e);
    } finally {
      workspace.setLinguistStreaming(false);
      workspace.clearActiveTaskId();
      clearPersistedTask();
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
    } finally {
      workspace.setLinguistStreaming(false);
      workspace.clearActiveTaskId();
      clearPersistedTask();
    }
  }

  return { result, isStreaming, error, submitTask, cancelCurrentTask };
}
