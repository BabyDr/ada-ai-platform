/** #13：刷新后 taskId 持久化（sessionStorage，配额 fallback）。 */
const STORAGE_KEY = "adaagent-active-task";

export interface PersistedTask {
  taskId: string;
  type: string;
  savedAt: number;
}

export function persistActiveTask(taskId: string, type: string): void {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ taskId, type, savedAt: Date.now() } satisfies PersistedTask),
    );
  } catch {
    /* #57 存储配额满时跳过 */
  }
}

export function readPersistedTask(): PersistedTask | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedTask;
    if (!parsed.taskId || !parsed.type) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function clearPersistedTask(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
