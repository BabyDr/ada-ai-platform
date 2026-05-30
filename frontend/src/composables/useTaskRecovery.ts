/**
 * #13：页面刷新后检查持久化 taskId，查询后端状态并提示用户。
 */
import { getTaskStatus } from "../services/linguistApi";
import { useWorkspaceStore } from "../stores/workspace";
import { clearPersistedTask, readPersistedTask } from "../utils/taskPersistence";

export async function recoverPersistedTask(expectedType?: string): Promise<string | null> {
  const saved = readPersistedTask();
  if (!saved) return null;
  if (expectedType && saved.type !== expectedType) return null;

  try {
    const { status } = await getTaskStatus(saved.taskId);
    clearPersistedTask();
    await useWorkspaceStore().fetchLogs();

    if (status === "running") {
      return "检测到刷新前仍有任务在执行，流式连接无法恢复，请重新提交。";
    }
    if (status === "done") {
      return "刷新前的任务已完成，请在运行历史中查看结果。";
    }
    if (status === "failed" || status === "cancelled") {
      return "刷新前的任务已结束，请查看运行历史。";
    }
  } catch {
    clearPersistedTask();
  }
  return null;
}
