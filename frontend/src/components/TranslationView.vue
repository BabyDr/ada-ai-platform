<script setup lang="ts">
/**
 * 文本翻译页：双栏输入/输出 UI。
 * 任务流、日志、导出逻辑分别见 useTask / useLinguistTaskLog / useExportActions。
 */
import { computed, onMounted, ref } from "vue";
import {
  Sparkles,
  Copy,
  Check,
  Download,
  Trash2,
  ArrowRightLeft,
  AlertTriangle,
  Languages,
  Clock,
  Sparkle,
  Square,
} from "lucide-vue-next";
import { SUPPORTED_LANGUAGES, TONE_STYLES } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
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

const inputText = ref("");
const sourceLang = ref("auto");
const targetLang = ref("zh");
const selectedTone = ref<
  "Professional" | "Conversational" | "Technical" | "Academic" | "Creative"
>("Professional");
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

useQuickTextPrefill(inputText);

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

/** 清空输入、结果与错误状态。 */
function handleClear(): void {
  inputText.value = "";
  result.value = "";
  error.value = "";
  elapsedTime.value = "--";
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
  <div class="space-y-6 p-8 max-w-6xl mx-auto" id="translation-view">
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#26384d]/40 pb-5"
    >
      <div>
        <h2
          class="font-display text-2xl font-bold text-white flex items-center gap-2"
        >
          <Languages class="w-6 h-6 text-[#00a67e]" />
          文本翻译器 · 双栏对照
        </h2>
        <p class="text-xs text-[#acb5c9] mt-1">
          覆盖 10 种全球语言，针对技术词汇与上下文一致性进行标准化翻译。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <StreamingBadge :active="isStreaming" label="流式翻译中..." />
      </div>
    </div>

    <ApiKeyBanner
      :connected="apiConnected"
      description="模型服务当前离线。请在 backend/.env 中配置 GLM_API_KEY 或 ZHIPU_API_KEY 后重启 Sidecar。"
    />

    <div class="p-4 rounded bg-[#08121e]/40 border border-[#26384d]/60">
      <label
        class="block text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider mb-2.5"
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
        class="rounded border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden"
      >
        <div
          class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between"
        >
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold text-[#acb5c9] shrink-0"
              >源语言</span
            >
            <a-select
              v-model:value="sourceLang"
              size="small"
              :options="sourceLanguageOptions"
              class="lang-select min-w-30"
              popup-class-name="lang-select-dropdown"
              :disabled="isStreaming"
            />
          </div>
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

        <div class="p-5 flex-1 min-h-75 flex flex-col">
          <textarea
            v-model="inputText"
            placeholder="在此输入待翻译文本或原始文档…"
            maxlength="50000"
            :disabled="isStreaming"
            class="resize-none w-full flex-1 bg-transparent text-white text-sm focus:outline-none placeholder-[#bccac2]/35 leading-relaxed custom-scrollbar outline-none focus:ring-0 disabled:opacity-60"
          />
        </div>

        <div
          class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between gap-3 text-xs text-[#acb5c9] font-mono"
        >
          <span class="shrink min-w-0 truncate"
            >{{ inputText.length }} / 50,000 字符</span
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
        class="rounded border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden"
      >
        <div
          class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between"
        >
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold text-[#acb5c9] shrink-0"
              >目标语言</span
            >
            <a-select
              v-model:value="targetLang"
              size="small"
              :options="targetLanguageOptions"
              class="lang-select min-w-30"
              popup-class-name="lang-select-dropdown"
              :disabled="isStreaming"
            />
          </div>
          <div v-if="result" class="flex items-center gap-1">
            <a-button
              type="default"
              size="small"
              class="action-btn !text-xs"
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

        <div class="p-5 flex-1 min-h-75 flex flex-col bg-[#020c15]/40">
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
              <span class="font-semibold text-white block">执行失败</span>
              <span>{{ error }}</span>
            </div>
          </div>

          <div
            v-else-if="result"
            class="text-white text-sm leading-relaxed flex-1 select-text selection:bg-[#00a67e]/40 custom-scrollbar overflow-y-auto"
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
              <span class="text-xs font-medium text-white block"
                >正在思考并翻译…</span
              >
              <span class="text-[10px] text-[#bccac2]/70"
                >流式连接已建立，等待首个 token</span
              >
            </div>
          </div>

          <div
            v-else
            class="flex-1 flex flex-col justify-center items-center text-center text-[#bccac2]/35"
          >
            <Languages class="w-10 h-10 mb-2 stroke-[1.2]" />
            <span class="text-xs">翻译结果将显示在右侧。</span>
          </div>
        </div>

        <div
          class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between text-[10px] text-[#acb5c9] font-mono"
        >
          <div class="flex items-center gap-1">
            <Clock class="w-3 h-3 text-[#00a67e]" />
            <span>耗时：{{ elapsedTime }}</span>
          </div>
          <span>语调：{{ selectedToneLabel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
