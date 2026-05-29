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

export async function translate(payload: {
  text: string;
  sourceLang: string;
  targetLang: string;
  tone: string;
}): Promise<{ text: string; duration: string }> {
  const res = await fetch(apiUrl("/translate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || "Translation failed");
  return data;
}

export async function summarize(payload: {
  text: string;
  keyPointsCount: number;
  wordLimit: number;
  tone: string;
}): Promise<{ result: { overview: string; keyPoints: string[] }; duration: string }> {
  const res = await fetch(apiUrl("/summarize"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || "Summarization failed");
  return data;
}
