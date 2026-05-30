<script setup lang="ts">
/** 共享 Leaf：Sidecar 未检测到 GLM 密钥时的琥珀色告警条（Translation / Summarization 共用）。 */
import { AlertTriangle } from "lucide-vue-next";

defineProps<{
  /** 为 false 时展示告警（即 !apiConnected） */
  connected: boolean;
  /** 副标题下的说明文案，各页可定制 */
  description: string;
}>();
</script>

<template>
  <div
    v-if="!connected"
    class="p-4 rounded bg-amber-500/10 border border-amber-500/30 flex items-start gap-3"
  >
    <AlertTriangle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
    <div>
      <span class="text-xs font-semibold text-ui block">未检测到 GLM_API_KEY</span>
      <span class="text-xs text-ui-muted leading-relaxed">{{ description }}</span>
    </div>
  </div>
</template>
