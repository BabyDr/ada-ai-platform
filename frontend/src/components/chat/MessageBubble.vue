<script setup lang="ts">
/** 用户消息气泡：纯展示 content prop。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="flex w-full justify-start text-left">
    <div
      class="max-w-[min(92%,40rem)] rounded border border-[#26384d] bg-[#0e1b2b] px-4 py-3 text-[15px] leading-relaxed text-[#d4e4fa]"
    >
      <span class="whitespace-pre-wrap break-words">{{ content }}</span>
    </div>
  </div>
</template>
