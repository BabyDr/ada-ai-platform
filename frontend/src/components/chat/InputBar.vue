<script setup lang="ts">
import { ref } from "vue";

const text = ref("");
const emit = defineEmits<{ submit: [value: string] }>();

const modeWeb = ref(false);
const modeLocal = ref(true);
const modeCode = ref(false);

function onSubmit() {
  const v = text.value.trim();
  if (!v) return;
  emit("submit", v);
  text.value = "";
}

const modeActive = "bg-[#00a67e]/10 text-[#00a67e] ring-1 ring-[#00a67e]/30";
const modeIdle = "text-[#acb5c9] hover:bg-[#162537]/50 hover:text-white";
</script>

<template>
  <div>
    <div
      class="flex items-end gap-2 rounded-2xl border border-[#26384d] bg-[#0c1622] p-2 sm:gap-3"
    >
      <button
        type="button"
        class="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-[#acb5c9] transition hover:bg-[#162537]/50 hover:text-[#00a67e]"
        title="附件（占位）"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path
            d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19A4 4 0 1 1 21 12.31l-9.18 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"
          />
        </svg>
      </button>
      <a-textarea
        v-model:value="text"
        :auto-size="{ minRows: 1, maxRows: 6 }"
        placeholder="输入消息… Enter 发送，Shift+Enter 换行"
        class="chat-input !min-h-[44px] flex-1 !resize-none !border-0 !bg-transparent !px-2 !py-2 !text-[#d4e4fa] !shadow-none focus:!ring-0"
        @keydown.enter.exact.prevent="onSubmit"
      />
      <button
        type="button"
        class="mb-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#00a67e] text-white transition hover:bg-[#008f6c]"
        title="发送"
        @click="onSubmit"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path d="M12 19V5M5 12l7-7 7 7" />
        </svg>
      </button>
    </div>
    <div class="mt-3 flex flex-wrap items-center gap-2 sm:gap-4">
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium transition sm:text-sm"
        :class="modeWeb ? modeActive : modeIdle"
        @click="modeWeb = !modeWeb"
      >
        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
        </svg>
        联网搜索
      </button>
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium transition sm:text-sm"
        :class="modeLocal ? modeActive : modeIdle"
        @click="modeLocal = !modeLocal"
      >
        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 21V9" />
        </svg>
        本地上下文
      </button>
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium transition sm:text-sm"
        :class="modeCode ? modeActive : modeIdle"
        @click="modeCode = !modeCode"
      >
        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />
        </svg>
        代码模式
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input::placeholder {
  color: rgba(188, 202, 194, 0.45);
}
</style>
