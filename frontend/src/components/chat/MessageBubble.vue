<script setup lang="ts">
/** 用户消息气泡：纯展示 content prop，右对齐且与回答区共用列宽。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="chat-align-column flex justify-end text-right">
    <div
      class="w-fit max-w-full rounded border border-(--color-outline-variant) bg-(--color-chat-bubble) px-4 py-3 text-[15px] leading-relaxed text-ui"
    >
      <span class="whitespace-pre-wrap wrap-break-word">{{ content }}</span>
    </div>
  </div>
</template>
