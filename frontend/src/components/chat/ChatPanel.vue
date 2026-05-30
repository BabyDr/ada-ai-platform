<script setup lang="ts">
/**
 * 对话面板编排层：消息列表 + InputBar，绑定 chat store 与 WS 流。
 */
import { message } from "ant-design-vue";
import { storeToRefs } from "pinia";
import { computed, ref } from "vue";
import { useChatStore } from "@/stores/chat";
import { useChatStream } from "@/composables/useChatStream";
import { useAutoScroll } from "@/composables/useAutoScroll";
import MessageBubble from "./MessageBubble.vue";
import InputBar from "./InputBar.vue";
import ThinkBlock from "./ThinkBlock.vue";
import ActionBlock from "./ActionBlock.vue";
import ObservationBlock from "./ObservationBlock.vue";
import FinalResult from "./FinalResult.vue";

const chat = useChatStore();
const { messages, activeSessionId } = storeToRefs(chat);

useChatStream(activeSessionId);

/** 消息列表容器，用于自动滚动到底部。 */
const chatListRef = ref<HTMLElement | null>(null);
/** O(1) 滚动触发器：捕获新消息和流式内容追加。 */
const scrollTick = computed(() => {
  const len = messages.value.length;
  if (len === 0) return 0;
  const last = messages.value[len - 1];
  return `${len}:${last.content.length}`;
});
useAutoScroll(chatListRef, scrollTick);

/** 提交用户消息到 chat store（HTTP）；ReAct 步骤由 WS 推送。 */
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
  <div class="flex min-h-0 flex-1 flex-col bg-(--color-background)/40">
    <div ref="chatListRef" class="custom-scrollbar min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-6 sm:px-10">
      <div class="mx-auto max-w-3xl">
        <div
          v-if="!messages.length"
          class="flex flex-col items-center justify-center rounded border border-dashed border-(--color-outline-variant) bg-(--color-surface)/80 px-8 py-16 text-center"
        >
          <div
            class="mb-4 flex h-14 w-14 items-center justify-center rounded bg-[#00a67e]/10 border border-[#00a67e]/30 text-[#00a67e]"
            aria-hidden="true"
          >
            <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3v1m0 16v1M5.6 5.6l.7.7m11.4 11.4l.7.7M3 12h1m16 0h1M5.6 18.4l.7-.7M18.3 5.7l.7-.7" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </div>
          <p class="text-base font-semibold text-ui">开始对话</p>
          <p class="mt-1 max-w-sm text-sm text-ui-muted">输入问题后发送；可观察 Think / Act / Observe 与流式回答。</p>
        </div>
        <div v-else class="flex flex-col gap-4 pb-6">
          <template v-for="m in messages" :key="m.id">
            <MessageBubble v-if="m.role === 'user'" :content="m.content" />
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

    <div class="shrink-0 border-t border-(--color-outline-variant) bg-(--color-surface-header)/90 px-4 py-4 sm:px-10">
      <div class="mx-auto max-w-3xl">
        <InputBar @submit="onSubmitMessage" />
      </div>
    </div>
  </div>
</template>
