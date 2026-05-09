<script setup lang="ts">
/** 用户提问：靠左展示；助手正文由 FinalResult 等组件渲染。 */
defineProps<{ role: "user" | "assistant"; content: string }>();
</script>

<template>
  <div class="flex w-full justify-start text-left">
    <div
      class="max-w-[min(92%,40rem)] rounded-xl border border-arch-border bg-[#eef2f0] px-4 py-3 text-[15px] leading-relaxed text-arch-ink shadow-arch"
    >
      <span class="whitespace-pre-wrap break-words">{{ content }}</span>
    </div>
  </div>
</template>
