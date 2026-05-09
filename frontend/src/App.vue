<script setup lang="ts">
import { theme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";

/** Ant Design 全局主题：与 AI Architect 稿主色 #00A67E 对齐 */
const algorithm = theme.defaultAlgorithm;
const themeToken = {
  colorPrimary: "#00A67E",
  colorInfo: "#00A67E",
  borderRadius: 12,
  fontFamily: '"Inter", system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
};
</script>

<template>
  <a-config-provider :locale="zhCN" :theme="{ algorithm, token: themeToken }">
    <!-- 占满 #app，便于子页面用 h-full / min-h-0 做内部滚动 -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <router-view />
    </div>
  </a-config-provider>
</template>
