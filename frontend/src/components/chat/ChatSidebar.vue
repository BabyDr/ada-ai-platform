/** * ChatView 侧栏：会话列表、新建会话、设置/帮助入口。 * 会话 CRUD 通过 chat
store，View 层仅做布局与错误提示。 */
<script setup lang="ts">
import { message } from "ant-design-vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "@/stores/chat";

const emit = defineEmits<{
  settings: [];
  help: [];
}>();

const chat = useChatStore();
const { sessions, activeSessionId, loading } = storeToRefs(chat);

const BACKEND_HINT =
  "请先在仓库根目录执行：npm run sidecar:setup，再 npm run dev:all（或另开终端 npm run sidecar）";

/** 切换当前会话并加载历史消息。 */
async function onSelect(id: string): Promise<void> {
  try {
    await chat.selectSession(id);
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    message.error(`${detail}。${BACKEND_HINT}`, 6);
  }
}

/** 创建新会话并设为当前。 */
async function onNew(): Promise<void> {
  try {
    await chat.addSession();
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    message.error(`${detail}。${BACKEND_HINT}`, 6);
  }
}

defineExpose({ onNew });
</script>

<template>
  <aside
    class="flex h-full min-h-0 w-65 shrink-0 flex-col overflow-hidden border-r border-[var(--color-outline-variant)] bg-[var(--color-background)]"
  >
    <div class="flex items-start gap-3 px-4 pt-5 pb-4">
      <div
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded bg-gradient-to-tr from-[#00a67e]/20 to-[#00a67e]/40 border border-[#00a67e]/40 text-[#00a67e]"
      >
        <svg
          class="h-6 w-6"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      </div>
      <div class="min-w-0 pt-0.5">
        <h1
          class="text-[15px] font-bold leading-tight tracking-tight text-ui"
        >
          AdaAgent
        </h1>
        <p
          class="mt-0.5 text-[10px] font-semibold uppercase tracking-widest text-ui-muted"
        >
          智能体对话
        </p>
      </div>
    </div>

    <div class="px-3 pb-2">
      <a-button
        block
        type="primary"
        size="middle"
        class="block-btn action-btn"
        @click="onNew"
      >
        <template #icon><span class="text-base leading-none">+</span></template>
        新建会话
      </a-button>
    </div>

    <p
      class="px-4 pb-2 text-[11px] font-semibold uppercase tracking-wider text-ui-muted"
    >
      最近
    </p>

    <a-spin :spinning="loading" class="flex min-h-0 flex-1 flex-col">
      <div class="custom-scrollbar flex-1 overflow-y-auto px-2 pb-4">
        <button
          v-for="s in sessions"
          :key="s.id"
          type="button"
          class="mb-1 flex w-full items-center gap-3 rounded px-3 py-2.5 text-left text-sm transition"
          :class="
            activeSessionId === s.id
               ? 'sidebar-nav-active font-medium'
              : 'sidebar-nav-inactive'
          "
          @click="onSelect(s.id)"
        >
          <span
            class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-surface-header)] text-[#00a67e] border border-[var(--color-outline-variant)]/60"
            aria-hidden="true"
          >
            <svg
              class="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
              />
            </svg>
          </span>
          <span class="min-w-0 flex-1 truncate">{{ s.title }}</span>
        </button>
      </div>
    </a-spin>

    <div class="mt-auto border-t border-[var(--color-outline-variant)] px-2 py-3 space-y-1">
      <a-button
        block
        type="text"
        size="small"
        class="chat-sidebar-btn action-btn"
        @click="emit('settings')"
      >
        <template #icon>
          <svg
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="3" />
            <path
              d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            />
          </svg>
        </template>
        设置
      </a-button>
      <a-button
        block
        type="text"
        size="small"
        class="chat-sidebar-btn action-btn"
        @click="emit('help')"
      >
        <template #icon>
          <svg
            class="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" />
          </svg>
        </template>
        帮助
      </a-button>
    </div>
  </aside>
</template>
