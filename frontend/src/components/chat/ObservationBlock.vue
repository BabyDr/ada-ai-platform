<script setup lang="ts">
/** ReAct Observe 步骤块：展示工具执行结果。 */
defineProps<{ content: string }>();
</script>

<template>
  <div class="chat-align-column relative overflow-hidden rounded border border-(--color-outline-variant) bg-(--color-surface)">
    <div class="flex items-center gap-2 border-b border-(--color-outline-variant)/70 bg-(--color-surface-header) px-4 py-2.5">
      <span class="flex h-7 w-7 items-center justify-center rounded bg-[#00a67e]/10 text-[#00a67e]">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </span>
      <span class="text-[11px] font-bold uppercase tracking-widest text-[#00a67e]">Observe</span>
      <span
        class="ml-auto rounded bg-[#00a67e]/10 border border-[#00a67e]/25 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#00a67e]"
      >
        Success
      </span>
    </div>
    <pre class="m-0 max-h-48 overflow-auto whitespace-pre-wrap p-4 font-mono leading-relaxed text-(--color-mono-text)">{{ content }}</pre>
  </div>
</template>
