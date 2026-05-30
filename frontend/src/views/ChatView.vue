<script setup lang="ts">
/**
 * 智能体对话页壳：挂载侧栏 + 顶栏 + ChatPanel，初始化默认会话。
 */
import { message } from "ant-design-vue";
import { onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "@/stores/chat";
import ChatPanel from "@/components/chat/ChatPanel.vue";
import ChatSidebar from "@/components/chat/ChatSidebar.vue";
import ChatHeader from "@/components/chat/ChatHeader.vue";
import { useBreakpoint } from "@/composables/useBreakpoint";

const chat = useChatStore();
const { sessions, activeSessionId } = storeToRefs(chat);
const { isMobile } = useBreakpoint();
const sessionDrawerOpen = ref(false);

const BACKEND_HINT =
  "请先在仓库根目录执行：npm run sidecar:setup，再 npm run dev:all（或另开终端 npm run sidecar）";

/** 首次进入：拉会话列表，无则自动创建并选中第一条。 */
onMounted(async () => {
  try {
    await chat.loadSessions();
    if (!sessions.value.length) {
      await chat.addSession();
    } else {
      await chat.selectSession(sessions.value[0].id);
    }
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    message.error(`${detail}。${BACKEND_HINT}`, 8);
  }
});

/** 占位：设置入口。 */
function onSettings(): void {
  message.info("设置：后续可接 Tauri / 配置页", 2);
}

/** 占位：帮助入口。 */
function onHelp(): void {
  message.info("详见仓库 README.md 启动说明", 3);
}
</script>

<template>
  <div
    class="flex h-full min-h-0 w-full min-w-0 max-w-full flex-1 overflow-hidden overflow-x-hidden app-main-gradient font-sans text-ui"
  >
    <ChatSidebar
      v-if="!isMobile"
      @settings="onSettings"
      @help="onHelp"
    />

    <a-drawer
      v-if="isMobile"
      v-model:open="sessionDrawerOpen"
      placement="left"
      :width="280"
      :closable="true"
      :body-style="{ padding: 0, height: '100%' }"
      title="会话"
    >
      <ChatSidebar
        embedded
        @settings="onSettings"
        @help="onHelp"
        @navigate="sessionDrawerOpen = false"
      />
    </a-drawer>

    <main class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <ChatHeader
        :show-session-menu="isMobile"
        @open-sessions="sessionDrawerOpen = true"
      />

      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <ChatPanel v-if="activeSessionId" class="min-h-0 flex-1" />
        <div
          v-else
          class="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 overflow-hidden p-10 text-center text-ui-muted"
        >
          <p class="text-sm font-medium text-ui">请选择或创建会话</p>
          <p class="max-w-xs text-xs">点击侧栏「新建会话」开始。</p>
        </div>
      </div>
    </main>
  </div>
</template>
