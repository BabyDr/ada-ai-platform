<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { theme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import Sidebar from "./components/Sidebar.vue";
import { useWorkspaceStore } from "./stores/workspace";

const workspace = useWorkspaceStore();
const route = useRoute();

// 主题：通过 a-config-provider 的 algorithm 切换明/暗（F19），沿用现有品牌 token。
const antTheme = computed(() => ({
  algorithm: workspace.isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
  token: {
    colorPrimary: "#00A67E",
    colorInfo: "#00A67E",
    borderRadius: 12,
    fontFamily:
      '"Inter", system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
    ...(workspace.isDark
      ? {
          colorBgContainer: "#0c1622",
          colorBgElevated: "#08121e",
          colorBorder: "#26384d",
          colorText: "#d4e4fa",
          colorTextSecondary: "#acb5c9",
        }
      : {}),
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
    <div
      class="flex bg-[#020c15] text-[#d4e4fa] min-h-screen h-screen overflow-hidden"
    >
      <Sidebar />

      <main
        :class="[
          'flex-1 min-h-0 h-full',
          isChat
            ? 'overflow-hidden'
            : 'overflow-y-auto bg-linear-to-tr from-[#020c15] via-[#051424] to-[#010912] custom-scrollbar',
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
