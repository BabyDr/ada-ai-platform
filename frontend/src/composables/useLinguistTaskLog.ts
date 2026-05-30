/**
 * Linguist SSE 任务与运行日志联动：创建 processing 日志 + 完成/取消/失败回调。
 * TranslationView / SummarizationView 共用，避免重复的 addLog/updateLog 模板代码。
 */
import type { LogEntry } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import type { SSEHandlers } from "./useSSE";

export type LinguistLogType = "translation" | "summarization";

export interface LinguistLogCallbacksOptions {
  /** 取消时写入日志的 output 文案（默认取流式 result 或「已取消」） */
  getCancelledOutput?: () => string;
  /** 成功时从 task_done payload 提取最终 output 字符串 */
  buildSuccessOutput: (payload: { result?: unknown }) => string;
}

/** 创建 processing 状态日志；服务端失败时静默降级为 null，不阻断主任务。 */
export async function createProcessingLog(
  type: LinguistLogType,
  inputPreview: string,
  details: LogEntry["details"],
): Promise<LogEntry | null> {
  const workspace = useWorkspaceStore();
  try {
    return await workspace.addLog({
      type,
      input: inputPreview,
      output: "...",
      duration: "--",
      status: "processing",
      details,
    });
  } catch (e) {
    console.warn("Log creation failed: ", e);
    return null;
  }
}

/** 根据 activeLog 生成 SSE onDone/onError 回调，供 submitTask 第三个参数使用。 */
export function buildLinguistLogCallbacks(
  activeLog: LogEntry | null,
  options: LinguistLogCallbacksOptions,
): Pick<SSEHandlers, "onDone" | "onError"> {
  const workspace = useWorkspaceStore();

  return {
    onDone: (payload) => {
      if (!activeLog) return;

      const duration = payload.duration || "--";

      if (payload.status === "cancelled") {
        workspace.updateLog(activeLog.id, {
          status: "failed",
          output: options.getCancelledOutput?.() ?? "已取消",
          duration,
          error: "用户已停止生成",
        });
        return;
      }

      workspace.updateLog(activeLog.id, {
        status: "success",
        output: options.buildSuccessOutput(payload),
        duration,
      });
    },
    onError: (message) => {
      if (!activeLog) return;
      workspace.updateLog(activeLog.id, {
        status: "failed",
        output: message,
        duration: "0s",
        error: message,
      });
    },
  };
}
