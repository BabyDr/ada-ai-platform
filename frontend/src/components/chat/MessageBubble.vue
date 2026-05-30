<script setup lang="ts">
/** 用户消息气泡：纯展示 content prop，右对齐且与回答区共用列宽。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="chat-align-column flex justify-end text-right">
    <div
      class="w-fit max-w-full rounded border border-[var(--color-outline-variant)] bg-[var(--color-chat-bubble)] px-4 py-3 text-[15px] leading-relaxed text-ui"
    >
      <span class="whitespace-pre-wrap break-words">{{ content }}</span>
    </div>
  </div>
</template>
