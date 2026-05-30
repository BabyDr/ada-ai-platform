<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { storeToRefs } from "pinia";
import { theme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import Sidebar from "./components/Sidebar.vue";
import { useThemeAttribute } from "./composables/useThemeAttribute";
import { useWorkspaceStore } from "./stores/workspace";

const workspace = useWorkspaceStore();
const { isDark } = storeToRefs(workspace);
const route = useRoute();

useThemeAttribute(isDark);

// 主题：Ant Design algorithm + 浅色语义 token（深色块在 antTheme 中保持原值）。
const antTheme = computed(() => ({
  algorithm: isDark.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
  token: {
    colorPrimary: "#00A67E",
    colorInfo: "#00A67E",
    borderRadius: 4,
    borderRadiusSM: 4,
    borderRadiusLG: 4,
    borderRadiusXS: 4,
    fontFamily:
      '"Inter", system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
    ...(isDark.value
      ? {
          colorBgContainer: "#0c1622",
          colorBgElevated: "#08121e",
          colorBorder: "#26384d",
          colorText: "#d4e4fa",
          colorTextSecondary: "#acb5c9",
        }
      : {
          colorBgContainer: "#ffffff",
          colorBgElevated: "#f0fdf4",
          colorBorder: "#cbd5e1",
          colorText: "#1a1c1e",
          colorTextSecondary: "#64748b",
        }),
  },
}));

const isChat = computed(() => route.name === "chat");

onMounted(() => {
  workspace.fetchHealth();
  workspace.fetchLogs();
});
</script>

<template>
  <a-config-provider :locale="zhCN" :theme="antTheme">
    <div class="flex app-shell-bg min-h-screen h-screen overflow-hidden">
      <Sidebar />

      <main
        :class="[
          'flex-1 min-h-0 h-full',
          isChat
            ? 'overflow-hidden'
            : 'overflow-y-auto app-main-gradient custom-scrollbar',
        ]"
      >
        <router-view v-slot="{ Component }">
          <keep-alive :exclude="['ChatView']">
            <component
              :is="Component"
              :class="isChat ? 'h-full min-h-0' : ''"
            />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </a-config-provider>
</template>
