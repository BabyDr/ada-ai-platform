<script setup lang="ts">
import { message } from "ant-design-vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "@/stores/chat";
import { useChatStream } from "@/composables/useChatStream";
import MessageBubble from "./MessageBubble.vue";
import InputBar from "./InputBar.vue";
import ThinkBlock from "./ThinkBlock.vue";
import ActionBlock from "./ActionBlock.vue";
import ObservationBlock from "./ObservationBlock.vue";
import FinalResult from "./FinalResult.vue";

const chat = useChatStore();
const { messages, activeSessionId } = storeToRefs(chat);

useChatStream(activeSessionId);

async function onSubmitMessage(text: string) {
  try {
    await chat.sendUserMessage(text);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    message.error(`${msg} — 请确认后端已运行：npm run sidecar（或一键 npm run dev:all）`, 6);
  }
}
</script>

<template>
  <!-- flex-1 + min-h-0：在父级 flex 列中占满剩余高度，仅本区纵向滚动 -->
  <div class="flex min-h-0 flex-1 flex-col bg-arch-canvas">
    <div class="scrollbar-arch min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-6 sm:px-10">
      <div class="mx-auto max-w-3xl">
        <div
          v-if="!messages.length"
          class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-arch-border bg-arch-surface/80 px-8 py-16 text-center shadow-arch"
        >
          <div
            class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-arch-think text-arch-primary"
            aria-hidden="true"
          >
            <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3v1m0 16v1M5.6 5.6l.7.7m11.4 11.4l.7.7M3 12h1m16 0h1M5.6 18.4l.7-.7M18.3 5.7l.7-.7" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </div>
          <p class="text-base font-semibold text-arch-ink">开始对话</p>
          <p class="mt-1 max-w-sm text-sm text-arch-muted">输入问题后发送；可观察 Think / Act / Observe 与流式回答。</p>
        </div>
        <div v-else class="flex flex-col gap-4 pb-6">
          <template v-for="m in messages" :key="m.id">
            <MessageBubble v-if="m.role === 'user'" role="user" :content="m.content" />
            <ThinkBlock v-else-if="m.role === 'think'" :content="m.content" />
            <ActionBlock
              v-else-if="m.role === 'act'"
              :tool="m.metadata?.tool ?? 'unknown'"
              :params="m.metadata?.params ?? {}"
            />
            <ObservationBlock v-else-if="m.role === 'observe'" :content="m.content" />
            <FinalResult v-else-if="m.role === 'assistant'" :content="m.content" />
          </template>
        </div>
      </div>
    </div>

    <div class="shrink-0 border-t border-arch-border bg-arch-surface px-4 py-4 shadow-arch-lg sm:px-10">
      <div class="mx-auto max-w-3xl">
        <InputBar @submit="onSubmitMessage" />
      </div>
    </div>
  </div>
</template>
