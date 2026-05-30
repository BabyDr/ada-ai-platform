<script setup lang="ts">
/** ReAct Think 步骤块：可折叠展示推理内容。 */
import { ref } from "vue";

defineProps<{ content: string }>();

const open = ref(true);
</script>

<template>
  <div class="chat-align-column overflow-hidden rounded border border-(--color-outline-variant) bg-(--color-surface-header)/80">
    <button
      type="button"
      class="flex w-full items-center gap-2 px-4 py-3 text-left transition hover:bg-[#162537]/40"
      @click="open = !open"
    >
      <span
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#00a67e]/10 border border-[#00a67e]/25 text-[#00a67e]"
        aria-hidden="true"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path
            d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
          />
        </svg>
      </span>
      <span class="text-[11px] font-bold uppercase tracking-widest text-[#00a67e]">Think</span>
      <span class="ml-auto text-xs text-ui-muted">{{ open ? "收起" : "展开" }}</span>
    </button>
    <div v-show="open" class="border-t border-(--color-outline-variant)/60 px-4 pb-4 pt-1 text-sm leading-relaxed text-ui">
      {{ content }}
    </div>
  </div>
</template>
