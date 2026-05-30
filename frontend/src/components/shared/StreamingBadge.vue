<script setup lang="ts">
/** 共享 Leaf：SSE 流式生成中的页头状态 badge（Translation / Summarization 共用）。 */
defineProps<{
  /** 为 true 时展示旋转指示与文案 */
  active: boolean;
  /** 流式状态文案，如「流式翻译中…」 */
  label: string;
}>();
</script>

<template>
  <span
    v-if="active"
    class="px-2.5 py-1 text-[10px] font-mono font-semibold bg-[#00a67e]/10 text-[#00a67e] border border-[#00a67e]/35 rounded flex items-center gap-1.5"
  >
    <span class="animate-spin rounded-full h-2 w-2 border-2 border-t-transparent border-[#00a67e]"></span>
    {{ label }}
  </span>
</template>
