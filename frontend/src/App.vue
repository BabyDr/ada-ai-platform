<script setup lang="ts">
import { ref, onMounted } from "vue";
import { theme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import Sidebar from "./components/Sidebar.vue";
import DashboardView from "./components/DashboardView.vue";
import TranslationView from "./components/TranslationView.vue";
import SummarizationView from "./components/SummarizationView.vue";
import HistoryView from "./components/HistoryView.vue";
import SettingsView from "./components/SettingsView.vue";
import ChatView from "./views/ChatView.vue";
import type { LogEntry, WorkspaceViewId } from "./types";
import * as api from "./services/linguistApi";

const activeView = ref<WorkspaceViewId>("dashboard");
const logs = ref<LogEntry[]>([]);
const apiConnected = ref(false);
const quickText = ref("");

const antTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#00A67E",
    colorInfo: "#00A67E",
    colorBgContainer: "#0c1622",
    colorBgElevated: "#08121e",
    colorBorder: "#26384d",
    colorText: "#d4e4fa",
    colorTextSecondary: "#acb5c9",
    borderRadius: 12,
    fontFamily: '"Inter", system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
  },
};

onMounted(async () => {
  try {
    const healthData = await api.fetchHealth();
    apiConnected.value = !!healthData.keyLoaded;
  } catch (err) {
    console.warn("Sidecar health check loading...", err);
  }

  try {
    const logsData = (await api.fetchLogs()) as LogEntry[];
    logs.value = logsData;
  } catch (err) {
    console.warn("Could not load initial logs", err);
  }
});

const handleAddLog = async (newLogData: Omit<LogEntry, "id" | "timestamp" | "date">): Promise<LogEntry> => {
  try {
    const addedLog = (await api.addLog(newLogData)) as LogEntry;
    logs.value = [addedLog, ...logs.value];
    return addedLog;
  } catch (err) {
    console.error("Server logging failed, using safe memory fallback:", err);
  }

  const d = new Date();
  const mockMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  let hr = d.getHours();
  const ampm = hr >= 12 ? "PM" : "AM";
  hr = hr % 12 || 12;
  const min = d.getMinutes() < 10 ? `0${d.getMinutes()}` : String(d.getMinutes());

  const fallbackLog: LogEntry = {
    id: `log-${Date.now()}`,
    timestamp: `${hr}:${min} ${ampm}`,
    date: `${mockMonths[d.getMonth()]} ${d.getDate()}`,
    ...newLogData,
  };

  logs.value = [fallbackLog, ...logs.value];
  return fallbackLog;
};

const handleUpdateLog = async (id: string, updates: Partial<LogEntry>) => {
  logs.value = logs.value.map((log) => (log.id === id ? { ...log, ...updates } : log));
  try {
    await api.updateLogStatus(id, updates);
  } catch (err) {
    console.warn("Server status sync failed, using client fallback", err);
  }
};

const handleClearHistory = () => {
  logs.value = [];
};
</script>

<template>
  <a-config-provider :locale="zhCN" :theme="antTheme">
    <div class="flex bg-[#020c15] text-[#d4e4fa] min-h-screen h-screen overflow-hidden">
      <Sidebar v-model:active-view="activeView" :api-connected="apiConnected" />

      <main
        :class="[
          'flex-1 min-h-0 h-full',
          activeView === 'chat'
            ? 'overflow-hidden'
            : 'overflow-y-auto bg-gradient-to-tr from-[#020c15] via-[#051424] to-[#010912] custom-scrollbar',
        ]"
      >
        <ChatView v-if="activeView === 'chat'" class="h-full min-h-0" />

        <KeepAlive v-else>
          <component
            :is="
              activeView === 'dashboard'
                ? DashboardView
                : activeView === 'translation'
                  ? TranslationView
                  : activeView === 'summarization'
                    ? SummarizationView
                    : activeView === 'history'
                      ? HistoryView
                      : SettingsView
            "
            :logs="logs"
            :api-connected="apiConnected"
            v-model:quick-text="quickText"
            v-model:active-view="activeView"
            :on-add-log="handleAddLog"
            :on-update-log="handleUpdateLog"
            :on-clear-history="handleClearHistory"
          />
        </KeepAlive>
      </main>
    </div>
  </a-config-provider>
</template>
