<script setup lang="ts">
/** ACT：深绿左边线 + 等宽「终端」感（稿中工具调用块） */
defineProps<{
  tool: string;
  params: Record<string, unknown>;
}>();
</script>

<template>
  <div
    class="overflow-hidden rounded-xl border border-arch-border bg-arch-surface shadow-arch"
    style="border-left-width: 4px; border-left-color: #004d3d"
  >
    <div class="border-b border-arch-border/80 bg-arch-canvas/50 px-4 py-2">
      <span class="font-mono text-xs font-bold uppercase tracking-wide text-arch-primary">Act</span>
      <span class="ml-2 font-mono text-xs text-arch-ink">: {{ tool }}</span>
    </div>
    <pre
      class="m-0 max-h-52 overflow-auto p-4 font-mono text-[12px] leading-relaxed text-arch-ink"
    >{{ JSON.stringify(params, null, 2) }}</pre>
  </div>
</template>
