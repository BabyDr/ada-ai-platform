<script setup lang="ts">
/** 助手最终回答块：流式拼接完成后的 assistant 内容。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="text-left">
    <p class="mb-2 text-[11px] font-bold uppercase tracking-widest text-[#00a67e]">回答</p>
    <div
      class="max-w-[min(95%,42rem)] rounded border border-[#26384d] bg-[#0e1b2b] px-4 py-4 text-[15px] leading-relaxed text-[#d4e4fa]"
    >
      <pre class="m-0 whitespace-pre-wrap font-sans">{{ content }}</pre>
    </div>
  </div>
</template>
