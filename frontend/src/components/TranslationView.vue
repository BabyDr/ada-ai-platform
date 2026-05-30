<script setup lang="ts">
/**
 * 文本翻译页：双栏输入/输出 UI。
 * 任务流、日志、导出逻辑分别见 useTask / useLinguistTaskLog / useExportActions。
 */
import { computed, onMounted, ref, watch } from "vue";
import { useAutoScroll } from "../composables/useAutoScroll";
import { useWorkspaceStore } from "../stores/workspace";
import {
  Sparkles,
  Copy,
  Check,
  Download,
  Trash2,
  ArrowRightLeft,
  AlertTriangle,
  Languages,
  Globe,
  Target,
  Clock,
  Sparkle,
  Square,
} from "lucide-vue-next";
import { SUPPORTED_LANGUAGES, TONE_STYLES } from "../types";
import { useTask } from "../composables/useTask";
import { useQuickTextPrefill } from "../composables/useQuickTextPrefill";
import { useCopyFeedback, downloadTextFile } from "../composables/useExportActions";
import { buildLinguistLogCallbacks, createProcessingLog } from "../composables/useLinguistTaskLog";
import { runSafe } from "../utils/safeAsync";
import { recoverPersistedTask } from "../composables/useTaskRecovery";
import ApiKeyBanner from "./shared/ApiKeyBanner.vue";
import StreamingBadge from "./shared/StreamingBadge.vue";
import TruncatedText from "./shared/TruncatedText.vue";

const workspace = useWorkspaceStore();
const apiConnected = computed(() => workspace.apiConnected);

/** 流式输出：result 即逐 token 追加的译文。 */
const { result, isStreaming, error, submitTask, cancelCurrentTask } = useTask();

/** 输出区域容器，用于自动滚动到底部。 */
const outputRef = ref<HTMLElement | null>(null);
const scrollTick = computed(() => result.value);
useAutoScroll(outputRef, scrollTick);

const MAX_INPUT_CHARS = 5000;
const inputText = ref("");
const sourceLang = ref("auto");
const targetLang = ref("zh");
const selectedTone = ref<
  "Professional" | "Conversational" | "Technical" | "Academic" | "Creative"
>(workspace.defaultTone as "Professional" | "Conversational" | "Technical" | "Academic" | "Creative");
watch(() => workspace.defaultTone, (v) => { selectedTone.value = v as typeof selectedTone.value; });
const elapsedTime = ref("--");
const recoveryNotice = ref("");

const { copied, copyText } = useCopyFeedback();

const selectedToneLabel = computed(
  () => TONE_STYLES.find((t) => t.value === selectedTone.value)?.label ?? selectedTone.value,
);

const sourceLanguageOptions = SUPPORTED_LANGUAGES.map((l) => ({ value: l.code, label: l.name }));
const targetLanguageOptions = SUPPORTED_LANGUAGES.filter((l) => l.code !== "auto").map((l) => ({
  value: l.code,
  label: l.name,
}));

/** 清空输出区（快捷预填时复用，不清输入框）。 */
function resetOutputState(): void {
  if (isStreaming.value) cancelCurrentTask();
  result.value = "";
  error.value = "";
  elapsedTime.value = "--";
}

useQuickTextPrefill(inputText, resetOutputState);

onMounted(async () => {
  const msg = await recoverPersistedTask("translate");
  if (msg) recoveryNotice.value = msg;
});

/** 复制译文到剪贴板。 */
async function handleCopy(): Promise<void> {
  if (!result.value) return;
  await copyText(result.value);
}

/** 下载译文为 .txt 文件。 */
function handleDownload(): void {
  if (!result.value) return;
  downloadTextFile(result.value, `linguist-translation-${targetLang.value}.txt`);
}

/** 清空输入、结果与错误状态；若正在生成则一并中止。 */
function handleClear(): void {
  resetOutputState();
  inputText.value = "";
}

/** 交换源/目标语言；若有结果则回填到输入框。 */
function handleSwapLanguages(): void {
  if (sourceLang.value === "auto") {
    sourceLang.value = targetLang.value;
    targetLang.value = "en";
  } else {
    const temp = sourceLang.value;
    sourceLang.value = targetLang.value;
    targetLang.value = temp;
  }
  if (result.value && !isStreaming.value) {
    inputText.value = result.value;
    result.value = "";
  }
}

/** 中止当前 SSE 任务。 */
async function handleStop(): Promise<void> {
  await runSafe(() => cancelCurrentTask());
}

/** 提交翻译任务（SSE + 运行日志）。 */
async function handleTranslate(): Promise<void> {
  if (!inputText.value.trim() || isStreaming.value) return;

  await runSafe(
    async () => {
      elapsedTime.value = "--";

      const activeLog = await createProcessingLog("translation", inputText.value.substring(0, 500), {
        sourceLang: SUPPORTED_LANGUAGES.find((l) => l.code === sourceLang.value)?.name || sourceLang.value,
        targetLang: SUPPORTED_LANGUAGES.find((l) => l.code === targetLang.value)?.name || targetLang.value,
        tone: selectedTone.value,
      });

      const logCallbacks = buildLinguistLogCallbacks(activeLog, {
        getCancelledOutput: () => result.value || "已取消",
        buildSuccessOutput: (payload) =>
          (payload.result as { text?: string } | undefined)?.text ?? result.value,
      });

      await submitTask(
        "translate",
        {
          text: inputText.value,
          sourceLang: sourceLang.value,
          targetLang: targetLang.value,
          tone: selectedTone.value,
        },
        {
          onDone: (payload) => {
            elapsedTime.value = payload.duration || elapsedTime.value;
            logCallbacks.onDone?.(payload);
          },
          onError: (message) => {
            logCallbacks.onError?.(message);
          },
        },
      );
    },
    (msg) => {
      error.value = msg;
    },
  );
}
</script>

<template>
  <div class="space-y-6 p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full min-w-0 overflow-x-hidden" id="translation-view">
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-(--color-outline-variant)/40 pb-5"
    >
      <div>
        <h2
          class="font-display text-xl sm:text-2xl font-bold text-ui flex items-center gap-2"
        >
          <Languages class="w-6 h-6 text-[#00a67e]" />
          文本翻译器 · 双栏对照
        </h2>
        <p class="text-xs text-ui-muted mt-1">
          覆盖 10 种全球语言，针对技术词汇与上下文一致性进行标准化翻译。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <StreamingBadge :active="isStreaming" label="流式翻译中..." />
      </div>
    </div>

    <ApiKeyBanner
      :connected="apiConnected"
      description="模型服务当前离线。请在 backend/.env 中配置 GLM_API_KEY 后重启 Sidecar。"
    />

    <div class="p-4 sm:p-5 rounded bg-(--color-surface-header)/40 border border-(--color-outline-variant)/60">
      <label
        class="block text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2.5"
      >
        选择译文语调
      </label>
      <a-radio-group
        v-model:value="selectedTone"
        size="small"
        button-style="solid"
        class="tone-radio-group"
        :disabled="isStreaming"
      >
        <a-radio-button
          v-for="t in TONE_STYLES"
          :key="t.value"
          :value="t.value"
        >
          <span class="inline-flex items-center gap-1">
            <Sparkle
              v-if="selectedTone === t.value"
              class="w-3 h-3 fill-current"
            />
            {{ t.label }}
          </span>
        </a-radio-button>
      </a-radio-group>
    </div>

    <div
      class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] gap-y-6"
    >
      <div
        class="rounded border border-(--color-outline-variant)/60 bg-(--color-surface-header)/40 flex flex-col justify-between overflow-hidden"
      >
        <div
          class="h-10 px-5 border-b border-(--color-outline-variant) bg-(--color-surface-header) flex items-center justify-between"
        >
          <span class="text-xs font-semibold text-ui-muted shrink-0 flex items-center gap-1.5"
            ><Globe class="w-3.5 h-3.5" />源语言</span
          >
          <a-select
            v-model:value="sourceLang"
            size="small"
            :options="sourceLanguageOptions"
            class="lang-select min-w-30"
            popup-class-name="lang-select-dropdown"
            :disabled="isStreaming"
          />
          <a-button
            v-if="inputText"
            type="text"
            size="small"
            shape="circle"
            danger
            class="icon-only-btn"
            title="清空"
            @click="handleClear"
          >
            <template #icon><Trash2 class="w-3.5 h-3.5" /></template>
          </a-button>
        </div>

        <div class="p-4 sm:p-5 h-64 sm:h-87.5 overflow-y-auto custom-scrollbar flex flex-col">
          <textarea
            v-model="inputText"
            placeholder="在此输入待翻译文本或原始文档…"
            :maxlength="MAX_INPUT_CHARS"
            :disabled="isStreaming"
            class="resize-none w-full flex-1 bg-transparent text-ui text-sm focus:outline-none placeholder-(--color-placeholder) leading-relaxed custom-scrollbar outline-none focus:ring-0 disabled:opacity-60"
          />
        </div>

        <div
          class="h-10 px-5 border-t border-(--color-outline-variant) bg-(--color-surface-header) flex items-center justify-between gap-3 text-[10px] text-ui-muted font-mono"
        >
          <span class="shrink min-w-0 truncate"
            >{{ inputText.length }} / {{ MAX_INPUT_CHARS.toLocaleString() }} 字符</span
          >
          <div class="flex shrink-0 items-center gap-2">
            <a-button
              v-if="isStreaming"
              type="primary"
              danger
              size="small"
              class="action-btn"
              @click="handleStop"
            >
              <template #icon
                ><Square class="w-3.5 h-3.5 fill-current"
              /></template>
              停止生成
            </a-button>
            <a-button
              v-else
              type="primary"
              size="small"
              class="action-btn"
              :disabled="!inputText.trim()"
              @click="handleTranslate"
            >
              <template #icon><Sparkles class="w-3.5 h-3.5" /></template>
              开始翻译
            </a-button>
          </div>
        </div>
      </div>

      <div class="flex lg:hidden items-center justify-center py-1">
        <a-button
          shape="circle"
          size="small"
          class="icon-only-btn shadow-md"
          title="交换语言"
          :disabled="isStreaming"
          @click="handleSwapLanguages"
        >
          <template #icon><ArrowRightLeft class="w-3.5 h-3.5" /></template>
        </a-button>
      </div>

      <div class="hidden lg:flex items-center justify-center self-center px-3">
        <a-button
          shape="circle"
          size="small"
          class="icon-only-btn shadow-md"
          title="交换语言"
          :disabled="isStreaming"
          @click="handleSwapLanguages"
        >
          <template #icon><ArrowRightLeft class="w-3.5 h-3.5" /></template>
        </a-button>
      </div>

      <div
        class="rounded border border-(--color-outline-variant)/60 bg-(--color-surface-header)/40 flex flex-col justify-between overflow-hidden"
      >
        <div
          class="h-10 px-5 border-b border-(--color-outline-variant) bg-(--color-surface-header) flex items-center justify-between"
        >
          <span class="text-xs font-semibold text-ui-muted shrink-0 flex items-center gap-1.5"
            ><Target class="w-3.5 h-3.5" />目标语言</span
          >
          <a-select
            v-model:value="targetLang"
            size="small"
            :options="targetLanguageOptions"
            class="lang-select min-w-30"
            popup-class-name="lang-select-dropdown"
            :disabled="isStreaming"
          />
          <div v-if="result" class="flex items-center gap-1">
            <a-button
              type="default"
              size="small"
              class="action-btn text-xs!"
              @click="handleCopy"
            >
              <template #icon>
                <Check v-if="copied" class="w-3.5 h-3.5 text-[#00a67e]" />
                <Copy v-else class="w-3.5 h-3.5" />
              </template>
              {{ copied ? "已复制" : "复制" }}
            </a-button>
            <a-button
              type="default"
              size="small"
              shape="circle"
              class="icon-only-btn"
              title="下载"
              @click="handleDownload"
            >
              <template #icon><Download class="w-3.5 h-3.5" /></template>
            </a-button>
          </div>
        </div>

        <div ref="outputRef" class="p-4 sm:p-5 h-64 sm:h-87.5 overflow-y-auto custom-scrollbar flex flex-col bg-(--color-background)/40">
          <div
            v-if="recoveryNotice"
            class="p-4 rounded border border-amber-500/20 bg-amber-500/5 text-amber-400 text-xs leading-relaxed flex items-start gap-2.5 mb-3"
          >
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
            <span>{{ recoveryNotice }}</span>
          </div>

          <div
            v-if="error"
            class="p-4 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs leading-relaxed flex items-start gap-2.5"
          >
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span class="font-semibold text-ui block">执行失败</span>
              <span>{{ error }}</span>
            </div>
          </div>

          <div
            v-else-if="result"
            class="text-ui text-sm leading-relaxed select-text selection:bg-[#00a67e]/40 whitespace-pre-wrap wrap-break-word"
          >
            <TruncatedText :text="result" />
            <span
              v-if="isStreaming"
              class="inline-block w-1.5 h-4 ml-0.5 align-middle bg-[#00a67e] animate-pulse"
            ></span>
          </div>

          <div
            v-else-if="isStreaming"
            class="flex-1 flex flex-col justify-center items-center gap-3"
          >
            <div class="relative flex h-10 w-10">
              <span
                class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00a67e] opacity-40"
              ></span>
              <div
                class="relative rounded h-10 w-10 bg-[#00a67e]/20 border border-[#00a67e]/40 flex items-center justify-center"
              >
                <Sparkles class="w-5 h-5 text-[#00a67e] animate-pulse" />
              </div>
            </div>
            <div class="text-center">
              <span class="text-xs font-medium text-ui block"
                >正在思考并翻译…</span
              >
              <span class="text-[10px] text-ui-subtle"
                >流式连接已建立，等待首个 token</span
              >
            </div>
          </div>

          <div
            v-else
            class="flex-1 flex flex-col justify-center items-center text-center text-(--color-placeholder)"
          >
            <Languages class="w-10 h-10 mb-2 stroke-[1.2]" />
            <span class="text-xs">翻译结果将显示在右侧。</span>
          </div>
        </div>

        <div
          class="h-10 px-5 border-t border-(--color-outline-variant) bg-(--color-surface-header) flex items-center justify-between text-[10px] text-ui-muted font-mono"
        >
          <span>语调：{{ selectedToneLabel }}</span>
          <div class="flex items-center gap-1">
            <Clock class="w-3 h-3 text-[#00a67e]" />
            <span>耗时：{{ elapsedTime }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
