<script setup lang="ts">
/** 助手最终回答块：流式拼接完成后的 assistant 内容，右缘与用户问题对齐。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="chat-align-column text-left">
    <p class="mb-2 text-[11px] font-bold uppercase tracking-widest text-[#00a67e]">回答</p>
    <div
      class="w-full rounded border border-[var(--color-outline-variant)] bg-[var(--color-chat-bubble)] px-4 py-4 text-[15px] leading-relaxed text-ui"
    >
      <pre class="m-0 whitespace-pre-wrap font-sans">{{ content }}</pre>
    </div>
  </div>
</template>
