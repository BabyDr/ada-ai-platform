<script setup lang="ts">
/** 最终回答：白底卡片 + 柔和阴影（稿中主回答区） */
defineProps<{ content: string }>();
</script>

<template>
  <div class="text-left">
    <p class="mb-2 text-[11px] font-bold uppercase tracking-widest text-arch-muted">回答</p>
    <div
      class="max-w-[min(95%,42rem)] rounded-xl border border-arch-border bg-arch-surface px-4 py-4 text-[15px] leading-relaxed text-arch-ink shadow-arch-lg"
    >
      <pre class="m-0 whitespace-pre-wrap font-sans">{{ content }}</pre>
    </div>
  </div>
</template>
