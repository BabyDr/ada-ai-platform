/**
 * Linguist Sidecar HTTP 客户端（翻译/总结/日志/ SSE 任务）。
 * 根路径来自 Vite 环境变量 VITE_API_BASE，默认 /api。
 * 所有请求均含 try/catch 兜底（开发规范 §3.1）。
 */
const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

/** 拼接 Sidecar API 完整 URL。 */
function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

/** 包装 fetch：网络/解析失败时抛出带上下文的 Error。 */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(apiUrl(path), init);
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const j = (await res.json()) as { detail?: string; message?: string };
        detail = j.detail || j.message || detail;
      } catch {
        /* 非 JSON 错误体 */
      }
      throw new Error(detail);
    }
    return (await res.json()) as T;
  } catch (e) {
    if (e instanceof Error) throw e;
    throw new Error(String(e));
  }
}

/** GET /api/health —— 检查 Sidecar 与 GLM 密钥是否就绪。 */
export async function fetchHealth(): Promise<{ status: string; keyLoaded?: boolean; llm?: string }> {
  return requestJson("/health");
}

/** GET /api/logs —— 拉取运行历史日志列表。 */
export async function fetchLogs(): Promise<unknown[]> {
  return requestJson("/logs");
}

/** POST /api/logs/add —— 创建 processing 状态日志。 */
export async function addLog(payload: Record<string, unknown>): Promise<unknown> {
  return requestJson("/logs/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/** POST /api/logs/update-status —— 更新日志状态与 output。 */
export async function updateLogStatus(id: string, updates: Record<string, unknown>): Promise<void> {
  try {
    await fetch(apiUrl("/logs/update-status"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, ...updates }),
    });
  } catch (e) {
    console.warn("updateLogStatus failed", e);
  }
}

export interface FunctionItem {
  id: string;
  name: string;
  description: string;
  params?: Record<string, unknown> | null;
}

/** GET /api/functions —— 供 CLI / Agent 发现能力（前端工作台不依赖）。 */
export async function getFunctions(): Promise<{ functions: FunctionItem[] }> {
  return requestJson("/functions");
}

/** POST /api/task —— 提交 SSE 任务，返回原始流式 Response（由 useSSE 解析）。 */
export function createTaskSSE(
  body: { type: string; params: Record<string, unknown> },
  signal?: AbortSignal,
): Promise<Response> {
  try {
    return fetch(apiUrl("/task"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    return Promise.reject(e instanceof Error ? e : new Error(String(e)));
  }
}

/** DELETE /api/task/{taskId} —— 取消正在执行的任务。 */
export async function cancelTask(taskId: string): Promise<void> {
  try {
    const res = await fetch(apiUrl(`/task/${taskId}`), { method: "DELETE" });
    if (!res.ok) {
      throw new Error(`cancel failed: HTTP ${res.status}`);
    }
  } catch (e) {
    throw e instanceof Error ? e : new Error(String(e));
  }
}
