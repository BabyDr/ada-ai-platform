/**
 * #13：页面刷新后检查持久化 taskId，查询后端状态并提示用户。
 *
 * 流程：
 * 1. 从 sessionStorage 读取上次持久化的 taskId 和 type；
 * 2. 调用后端 GET /api/task/{id} 查询任务当前状态；
 * 3. 根据状态（running/done/failed/cancelled）返回对应的提示文案；
 * 4. 无论成功与否都清理 sessionStorage 中的持久化记录。
 */
import { getTaskStatus } from "../services/linguistApi";
import { useWorkspaceStore } from "../stores/workspace";
import { clearPersistedTask, readPersistedTask } from "../utils/taskPersistence";

/**
 * 恢复刷新前的任务状态：查询后端任务状态，返回用户提示文案。
 * @param expectedType 期望的任务类型（translate/summarize），不匹配则跳过恢复。
 * @returns 提示文案或 null（无持久化任务时不提示）。
 */
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
