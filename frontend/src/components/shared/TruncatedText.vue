<script setup lang="ts">
/** 长文本截断展示（#36）：默认折叠，可展开全文。 */
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    text: string;
    limit?: number;
  }>(),
  { limit: 10000 },
);

const expanded = ref(false);

const displayText = computed(() => {
  if (expanded.value || props.text.length <= props.limit) return props.text;
  return `${props.text.slice(0, props.limit)}…`;
});

const canExpand = computed(() => props.text.length > props.limit);
</script>

<template>
  <div>
    <span class="whitespace-pre-wrap break-words">{{ displayText }}</span>
    <button
      v-if="canExpand"
      type="button"
      class="ml-2 text-[#00a67e] text-xs hover:underline"
      @click="expanded = !expanded"
    >
      {{ expanded ? "收起" : "展开全文" }}
    </button>
  </div>
</template>
