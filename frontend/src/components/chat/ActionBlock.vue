<script setup lang="ts">
defineProps<{
  tool: string;
  params: Record<string, unknown>;
}>();
</script>

<template>
  <div
    class="overflow-hidden rounded-xl border border-[#26384d] bg-[#0c1622]"
    style="border-left-width: 4px; border-left-color: #00a67e"
  >
    <div class="border-b border-[#26384d]/80 bg-[#08121e] px-4 py-2">
      <span class="font-mono text-xs font-bold uppercase tracking-wide text-[#00a67e]">Act</span>
      <span class="ml-2 font-mono text-xs text-[#d4e4fa]">: {{ tool }}</span>
    </div>
    <pre class="m-0 max-h-52 overflow-auto p-4 font-mono text-[12px] leading-relaxed text-[#bccac2]">{{ JSON.stringify(params, null, 2) }}</pre>
  </div>
</template>
