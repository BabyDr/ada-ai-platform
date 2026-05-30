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

  async function fetchHealth(): Promise<void> {
    try {
      const health = await api.fetchHealth();
      apiConnected.value = !!health.keyLoaded;
    } catch (err) {
      console.warn("Sidecar health check loading...", err);
    }
  }

  async function fetchLogs(): Promise<void> {
    try {
      logs.value = (await api.fetchLogs()) as LogEntry[];
    } catch (err) {
      console.warn("Could not load initial logs", err);
    }
  }

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

  async function updateLog(id: string, updates: Partial<LogEntry>): Promise<void> {
    logs.value = logs.value.map((log) => (log.id === id ? { ...log, ...updates } : log));
    try {
      await api.updateLogStatus(id, updates as Record<string, unknown>);
    } catch (err) {
      console.warn("Server status sync failed, using client fallback", err);
    }
  }

  function clearHistory(): void {
    logs.value = [];
  }

  function setQuickText(text: string): void {
    quickText.value = text;
  }

  function consumeQuickText(): string {
    const text = quickText.value;
    quickText.value = "";
    return text;
  }

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
    consumeQuickText,
    toggleTheme,
  };
});
