const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

export async function fetchHealth(): Promise<{ status: string; keyLoaded?: boolean; llm?: string }> {
  const res = await fetch(apiUrl("/health"));
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchLogs(): Promise<unknown[]> {
  const res = await fetch(apiUrl("/logs"));
  if (!res.ok) throw new Error("Failed to load logs");
  return res.json();
}

export async function addLog(payload: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(apiUrl("/logs/add"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to add log");
  return res.json();
}

export async function updateLogStatus(id: string, updates: Record<string, unknown>): Promise<void> {
  await fetch(apiUrl("/logs/update-status"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, ...updates }),
  });
}

// ---- SSE task 契约（取代旧的非流式 /translate、/summarize）----

export interface FunctionItem {
  id: string;
  name: string;
  description: string;
  params?: Record<string, unknown> | null;
}

/** GET /api/functions —— 供 CLI / Agent 发现能力（前端工作台不依赖）。 */
export async function getFunctions(): Promise<{ functions: FunctionItem[] }> {
  const res = await fetch(apiUrl("/functions"));
  if (!res.ok) throw new Error("Failed to load functions");
  return res.json();
}

/** POST /api/task —— 提交任务，返回原始流式 Response（由 useSSE 解析）。 */
export function createTaskSSE(
  body: { type: string; params: Record<string, unknown> },
  signal?: AbortSignal,
): Promise<Response> {
  return fetch(apiUrl("/task"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

/** DELETE /api/task/{taskId} —— 取消正在执行的任务。 */
export async function cancelTask(taskId: string): Promise<void> {
  await fetch(apiUrl(`/task/${taskId}`), { method: "DELETE" });
}
