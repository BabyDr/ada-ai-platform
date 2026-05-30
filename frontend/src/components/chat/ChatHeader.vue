/**
 * ChatView 顶栏：当前模型、在线状态、快捷操作按钮。
 */
<script setup lang="ts">
import { message } from "ant-design-vue";
import { storeToRefs } from "pinia";
import { PanelLeft } from "lucide-vue-next";
import { useChatStore } from "@/stores/chat";

defineProps<{
  /** 移动端显示会话列表入口。 */
  showSessionMenu?: boolean;
}>();

const emit = defineEmits<{
  openSessions: [];
}>();

const chat = useChatStore();
const { currentModelId } = storeToRefs(chat);

/** 占位：历史记录说明。 */
function onHistoryHint(): void {
  message.info("历史记录：即左侧会话列表", 2);
}

/** 占位：分享功能说明。 */
function onShareHint(): void {
  message.info("分享功能可后续接入", 2);
}
</script>

<template>
  <header
    class="flex shrink-0 items-center justify-between gap-2 border-b border-(--color-outline-variant) bg-(--color-surface-header)/90 px-3 py-3 backdrop-blur-sm sm:gap-4 sm:px-5"
  >
    <div class="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
      <a-button
        v-if="showSessionMenu"
        type="text"
        size="small"
        shape="circle"
        class="icon-only-btn shrink-0 md:hidden"
        title="打开会话列表"
        @click="emit('openSessions')"
      >
        <template #icon><PanelLeft class="h-4 w-4 text-ui" /></template>
      </a-button>
      <div class="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
        <span class="truncate font-mono text-xs font-semibold text-ui sm:text-sm">{{ currentModelId }}</span>
      <span
        class="inline-flex items-center gap-1 rounded bg-[#00a67e]/10 border border-[#00a67e]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#00a67e]"
      >
        <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-[#00a67e]" />
        在线
      </span>
      </div>
    </div>
    <div class="flex shrink-0 items-center gap-1">
      <a-button type="text" size="small" shape="circle" class="icon-only-btn" title="历史" @click="onHistoryHint">
        <template #icon>
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
        </template>
      </a-button>
      <a-button type="text" size="small" shape="circle" class="icon-only-btn" title="分享" @click="onShareHint">
        <template #icon>
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13" />
          </svg>
        </template>
      </a-button>
      <a-button type="text" size="small" shape="circle" class="icon-only-btn" title="更多">
        <template #icon>
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="4" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="12" cy="20" r="1.5" />
          </svg>
        </template>
      </a-button>
      <div
        class="ml-1 flex h-9 w-9 items-center justify-center rounded bg-linear-to-br from-[#00a67e] to-[#008f6c] text-xs font-bold text-white"
        title="本地用户"
      >
        U
      </div>
    </div>
  </header>
</template>
