<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { storeToRefs } from "pinia";
import { theme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import { Menu } from "lucide-vue-next";
import Sidebar from "./components/Sidebar.vue";
import { useBreakpoint } from "./composables/useBreakpoint";
import { useThemeAttribute } from "./composables/useThemeAttribute";
import { useWorkspaceStore } from "./stores/workspace";

const workspace = useWorkspaceStore();
const { isDark } = storeToRefs(workspace);
const route = useRoute();
const { isMobile } = useBreakpoint();
const sidebarOpen = ref(false);

/** 路由切换后关闭移动端导航抽屉。 */
watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false;
  },
);

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

const pageTitles: Record<string, string> = {
  dashboard: "工作台",
  translation: "文本翻译",
  summarization: "智能总结",
  chat: "智能体对话",
  history: "运行日志",
  settings: "全局设置",
};

const mobileTitle = computed(
  () => pageTitles[String(route.name ?? "")] ?? "AdaWorks AI",
);

onMounted(() => {
  workspace.fetchHealth();
  workspace.fetchLogs();
});
</script>

<template>
  <a-config-provider :locale="zhCN" :theme="antTheme">
    <div
      class="flex app-shell-bg min-h-screen h-screen w-full max-w-full overflow-hidden overflow-x-hidden"
    >
      <Sidebar v-if="!isMobile" />

      <a-drawer
        v-if="isMobile"
        v-model:open="sidebarOpen"
        placement="left"
        :width="280"
        :closable="true"
        :body-style="{ padding: 0, height: '100%' }"
        class="mobile-nav-drawer"
        title="导航"
      >
        <Sidebar embedded @navigate="sidebarOpen = false" />
      </a-drawer>

      <div
        class="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden max-w-full"
      >
        <header
          v-if="isMobile"
          class="flex shrink-0 items-center gap-3 border-b ui-border bg-[var(--color-background)] px-4 py-3"
        >
          <a-button
            type="text"
            size="small"
            shape="circle"
            class="icon-only-btn shrink-0"
            title="打开导航菜单"
            @click="sidebarOpen = true"
          >
            <template #icon><Menu class="h-5 w-5 text-ui" /></template>
          </a-button>
          <h1 class="min-w-0 flex-1 truncate text-sm font-semibold text-ui">
            {{ mobileTitle }}
          </h1>
        </header>

        <main
          :class="[
            'min-h-0 flex-1 min-w-0 max-w-full overflow-x-hidden',
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
    </div>
  </a-config-provider>
</template>
