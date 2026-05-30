<script setup lang="ts">
/** ReAct Act 步骤块：展示 tool 名与 params JSON。 */
defineProps<{
  tool: string;
  params: Record<string, unknown>;
}>();
</script>

<template>
  <div
    class="chat-align-column overflow-hidden rounded border border-(--color-outline-variant) bg-(--color-surface)"
    style="border-left-width: 4px; border-left-color: #00a67e"
  >
    <div class="border-b border-(--color-outline-variant)/80 bg-(--color-surface-header) px-4 py-2">
      <span class="font-mono text-xs font-bold uppercase tracking-wide text-[#00a67e]">Act</span>
      <span class="ml-2 font-mono text-xs text-ui">: {{ tool }}</span>
    </div>
    <pre class="m-0 max-h-52 overflow-auto p-4 font-mono leading-relaxed text-(--color-mono-text)">{{ JSON.stringify(params, null, 2) }}</pre>
  </div>
</template>
