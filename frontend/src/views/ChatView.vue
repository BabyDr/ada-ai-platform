<script setup lang="ts">
import { message } from "ant-design-vue";
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "@/stores/chat";
import ChatPanel from "@/components/chat/ChatPanel.vue";

const chat = useChatStore();
const { sessions, activeSessionId, loading, currentModelId } = storeToRefs(chat);

const BACKEND_HINT =
  "请先在仓库根目录执行：npm run sidecar:setup，再 npm run dev:all（或另开终端 npm run sidecar）";

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

async function onSelect(id: string) {
  try {
    await chat.selectSession(id);
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    message.error(`${detail}。${BACKEND_HINT}`, 6);
  }
}

async function onNew() {
  try {
    await chat.addSession();
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    message.error(`${detail}。${BACKEND_HINT}`, 6);
  }
}

function onSettings() {
  message.info("设置：后续可接 Tauri / 配置页", 2);
}
function onHelp() {
  message.info("详见仓库 README.md 启动说明", 3);
}
</script>

<template>
  <div
    class="flex h-full min-h-0 w-full min-w-0 flex-1 overflow-hidden bg-gradient-to-tr from-[#020c15] via-[#051424] to-[#010912] font-sans text-[#d4e4fa]"
  >
    <aside
      class="flex h-full min-h-0 w-[260px] shrink-0 flex-col overflow-hidden border-r border-[#26384d] bg-[#020c15]"
    >
      <div class="flex items-start gap-3 px-4 pt-5 pb-4">
        <div
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-[#00a67e]/20 to-[#00a67e]/40 border border-[#00a67e]/40 text-[#00a67e]"
        >
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <div class="min-w-0 pt-0.5">
          <h1 class="text-[15px] font-bold leading-tight tracking-tight text-white">AdaAgent</h1>
          <p class="mt-0.5 text-[10px] font-semibold uppercase tracking-widest text-[#acb5c9]">智能体对话</p>
        </div>
      </div>

      <div class="px-3 pb-2">
        <button
          type="button"
          class="flex w-full items-center justify-center gap-2 rounded-xl bg-[#00a67e] py-3 text-sm font-semibold text-white transition hover:bg-[#008f6c]"
          @click="onNew"
        >
          <span class="text-lg leading-none">+</span>
          新建会话
        </button>
      </div>

      <p class="px-4 pb-2 text-[11px] font-semibold uppercase tracking-wider text-[#acb5c9]">最近</p>

      <a-spin :spinning="loading" class="flex min-h-0 flex-1 flex-col">
        <div class="custom-scrollbar flex-1 overflow-y-auto px-2 pb-4">
          <button
            v-for="s in sessions"
            :key="s.id"
            type="button"
            class="mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition"
            :class="
              activeSessionId === s.id
                ? 'bg-gradient-to-r from-[#2c3a4c] to-[#162537] font-medium text-white border-l-2 border-[#00a67e]'
                : 'text-[#acb5c9] hover:bg-[#162537]/50 hover:text-white'
            "
            @click="onSelect(s.id)"
          >
            <span
              class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#08121e] text-[#00a67e] border border-[#26384d]/60"
              aria-hidden="true"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </span>
            <span class="min-w-0 flex-1 truncate">{{ s.title }}</span>
          </button>
        </div>
      </a-spin>

      <div class="mt-auto border-t border-[#26384d] px-2 py-3">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 mb-1 text-left text-sm text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-white"
          @click="onSettings"
        >
          <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path
              d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            />
          </svg>
          设置
        </button>
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-white"
          @click="onHelp"
        >
          <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" />
          </svg>
          帮助
        </button>
      </div>
    </aside>

    <main class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <header
        class="flex shrink-0 items-center justify-between gap-4 border-b border-[#26384d] bg-[#08121e]/90 px-5 py-3 backdrop-blur-sm"
      >
        <div class="flex min-w-0 flex-wrap items-center gap-3">
          <span class="truncate font-mono text-sm font-semibold text-white">{{ currentModelId }}</span>
          <span
            class="inline-flex items-center gap-1 rounded-md bg-[#00a67e]/10 border border-[#00a67e]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#00a67e]"
          >
            <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-[#00a67e]" />
            在线
          </span>
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <button
            type="button"
            class="rounded-lg p-2 text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-white"
            title="历史"
            @click="message.info('历史记录：即左侧会话列表', 2)"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
          </button>
          <button
            type="button"
            class="rounded-lg p-2 text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-white"
            title="分享"
            @click="message.info('分享功能可后续接入', 2)"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13" />
            </svg>
          </button>
          <button type="button" class="rounded-lg p-2 text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-white" title="更多">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="4" r="1.5" />
              <circle cx="12" cy="12" r="1.5" />
              <circle cx="12" cy="20" r="1.5" />
            </svg>
          </button>
          <div
            class="ml-1 flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#00a67e] to-[#008f6c] text-xs font-bold text-white"
            title="本地用户"
          >
            U
          </div>
        </div>
      </header>

      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <ChatPanel v-if="activeSessionId" class="min-h-0 flex-1" />
        <div
          v-else
          class="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 overflow-hidden p-10 text-center text-[#acb5c9]"
        >
          <p class="text-sm font-medium text-white">请选择或创建会话</p>
          <p class="max-w-xs text-xs">点击侧栏「新建会话」开始。</p>
        </div>
      </div>
    </main>
  </div>
</template>
