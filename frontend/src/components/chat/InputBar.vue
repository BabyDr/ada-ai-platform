<script setup lang="ts">
/** 对话输入栏：本地文本状态 + 模式开关占位，提交通过 emit 交给 ChatPanel。 */
import { ref } from "vue";

const text = ref("");
const emit = defineEmits<{ submit: [value: string] }>();

const modeWeb = ref(false);
const modeLocal = ref(true);
const modeCode = ref(false);

/** 校验非空后 emit submit 并清空输入框。 */
function onSubmit() {
  const v = text.value.trim();
  if (!v) return;
  emit("submit", v);
  text.value = "";
}
</script>

<template>
  <div>
    <div
      class="chat-input-bar flex items-center gap-2 rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] p-2 sm:gap-3"
    >
      <a-button type="text" shape="circle" size="large" class="icon-only-btn shrink-0" title="附件（占位）">
        <template #icon>
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path
              d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19A4 4 0 1 1 21 12.31l-9.18 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"
            />
          </svg>
        </template>
      </a-button>
      <a-textarea
        v-model:value="text"
        :auto-size="{ minRows: 1, maxRows: 6 }"
        placeholder="输入消息… Enter 发送，Shift+Enter 换行"
        class="chat-input !min-h-10 flex-1 !resize-none !border-0 !bg-transparent !px-2 !py-0 !text-ui !shadow-none focus:!ring-0"
        @keydown.enter.exact.prevent="onSubmit"
      />
      <a-button type="primary" shape="circle" size="large" class="icon-only-btn shrink-0" title="发送" @click="onSubmit">
        <template #icon>
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </template>
      </a-button>
    </div>
    <div class="mt-3 flex flex-wrap items-center gap-2 sm:gap-3">
      <a-button
        size="small"
        class="action-btn chat-mode-btn"
        :type="modeWeb ? 'primary' : 'default'"
        @click="modeWeb = !modeWeb"
      >
        <template #icon>
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
          </svg>
        </template>
        联网搜索
      </a-button>
      <a-button
        size="small"
        class="action-btn chat-mode-btn"
        :type="modeLocal ? 'primary' : 'default'"
        @click="modeLocal = !modeLocal"
      >
        <template #icon>
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18M9 21V9" />
          </svg>
        </template>
        本地上下文
      </a-button>
      <a-button
        size="small"
        class="action-btn chat-mode-btn"
        :type="modeCode ? 'primary' : 'default'"
        @click="modeCode = !modeCode"
      >
        <template #icon>
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />
          </svg>
        </template>
        代码模式
      </a-button>
    </div>
  </div>
</template>

<style scoped>
/** 与 lg 圆形按钮同高，单行时占位与文字垂直居中 */
.chat-input-bar :deep(.chat-input textarea) {
  min-height: 2.5rem !important;
  padding-block: 0.5rem;
  line-height: 1.5rem;
  box-sizing: border-box;
}

/** 多行输入时发送/附件按钮贴底，单行时与输入框同高仍视觉居中 */
.chat-input-bar :deep(.icon-only-btn.ant-btn-lg) {
  align-self: flex-end;
}

.chat-input::placeholder {
  color: var(--color-placeholder);
}
</style>
