/**
 * 跨页共享状态（从 App.vue props 下沉）。
 *
 * 职责：运行日志、快捷输入文本、API 连接状态、明暗主题。
 * 各 View 直接读写本 store，不再经 App 透传 props。
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import type { LogEntry } from "../types";
import * as api from "../services/linguistApi";

const THEME_KEY = "adaagent-dark";

export const useWorkspaceStore = defineStore("workspace", () => {
  const logs = ref<LogEntry[]>([]);
  const quickText = ref("");
  const apiConnected = ref(false);
  const isDark = ref<boolean>(localStorage.getItem(THEME_KEY) !== "false");

  /** 拉取 Sidecar 健康状态，更新 apiConnected。 */
  async function fetchHealth(): Promise<void> {
    try {
      const health = await api.fetchHealth();
      apiConnected.value = !!health.keyLoaded;
    } catch (err) {
      console.warn("Sidecar health check loading...", err);
    }
  }

  /** 从服务端加载历史运行日志。 */
  async function fetchLogs(): Promise<void> {
    try {
      logs.value = (await api.fetchLogs()) as LogEntry[];
    } catch (err) {
      console.warn("Could not load initial logs", err);
    }
  }

  /** 新增一条日志；服务端失败时降级为本地内存条目。 */
  async function addLog(newLogData: Omit<LogEntry, "id" | "timestamp" | "date">): Promise<LogEntry> {
    try {
      const addedLog = (await api.addLog(newLogData)) as LogEntry;
      logs.value = [addedLog, ...logs.value];
      return addedLog;
    } catch (err) {
      console.error("Server logging failed, using safe memory fallback:", err);
    }

    const d = new Date();
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    let hr = d.getHours();
    const ampm = hr >= 12 ? "PM" : "AM";
    hr = hr % 12 || 12;
    const min = d.getMinutes() < 10 ? `0${d.getMinutes()}` : String(d.getMinutes());
    const fallbackLog: LogEntry = {
      id: `log-${Date.now()}`,
      timestamp: `${hr}:${min} ${ampm}`,
      date: `${months[d.getMonth()]} ${d.getDate()}`,
      ...newLogData,
    };
    logs.value = [fallbackLog, ...logs.value];
    return fallbackLog;
  }

  /** 更新本地日志并尝试同步到服务端。 */
  async function updateLog(id: string, updates: Partial<LogEntry>): Promise<void> {
    logs.value = logs.value.map((log) => (log.id === id ? { ...log, ...updates } : log));
    try {
      await api.updateLogStatus(id, updates as Record<string, unknown>);
    } catch (err) {
      console.warn("Server status sync failed, using client fallback", err);
    }
  }

  /** 清空本地日志列表（不删服务端 seed 数据，仅 UI 侧）。 */
  function clearHistory(): void {
    logs.value = [];
  }

  /** Dashboard 快捷输入写入，目标页消费后应清空。 */
  function setQuickText(text: string): void {
    quickText.value = text;
  }

  /** 切换明暗主题并持久化到 localStorage。 */
  function toggleTheme(): void {
    isDark.value = !isDark.value;
    localStorage.setItem(THEME_KEY, String(isDark.value));
  }

  return {
    logs,
    quickText,
    apiConnected,
    isDark,
    fetchHealth,
    fetchLogs,
    addLog,
    updateLog,
    clearHistory,
    setQuickText,
    toggleTheme,
  };
});
