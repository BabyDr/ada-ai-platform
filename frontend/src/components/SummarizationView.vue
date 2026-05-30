<script setup lang="ts">
/**
 * 智能总结页：配置参数、源文档输入、结构化结果展示。
 * 任务/日志/导出/文件导入分别见对应 composables。
 */
import { computed, onMounted, ref } from "vue";
import { useAutoScroll } from "../composables/useAutoScroll";
import {
  Sparkles,
  Copy,
  Check,
  Download,
  Trash2,
  AlertTriangle,
  Clock,
  Upload,
  Sparkle,
  Sliders,
  FileText,
  Square,
} from "lucide-vue-next";
import { TONE_STYLES, SUMMARY_MODES, type SummaryMode } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import { useTask } from "../composables/useTask";
import { useQuickTextPrefill } from "../composables/useQuickTextPrefill";
import {
  useCopyFeedback,
  downloadTextFile,
} from "../composables/useExportActions";
import {
  buildLinguistLogCallbacks,
  createProcessingLog,
} from "../composables/useLinguistTaskLog";
import { useFileImport } from "../composables/useFileImport";
import {
  formatSummaryForClipboard,
  formatSummaryForDownload,
} from "../utils/linguistFormat";
import { runSafe } from "../utils/safeAsync";
import { recoverPersistedTask } from "../composables/useTaskRecovery";
import ApiKeyBanner from "./shared/ApiKeyBanner.vue";
import StreamingBadge from "./shared/StreamingBadge.vue";
import TruncatedText from "./shared/TruncatedText.vue";

const workspace = useWorkspaceStore();
const apiConnected = computed(() => workspace.apiConnected);

/** result：总结流式阶段的原始 JSON 文本；task_done 后解析为 overview/keyPoints。 */
const { result, isStreaming, error, submitTask, cancelCurrentTask } = useTask();

const inputText = ref("");
const overviewText = ref("");
const keyPoints = ref<string[]>([]);
const summaryMode = ref<SummaryMode>("points");
const keyPointsCount = ref(3);
const wordLimit = ref(250);
const selectedTone = ref<
  "Professional" | "Conversational" | "Technical" | "Academic" | "Creative"
>("Professional");
const elapsedTime = ref("--");
const recoveryNotice = ref("");

/** 输出区域容器，用于自动滚动到底部。 */
const outputRef = ref<HTMLElement | null>(null);
const scrollTick = computed(() => {
  if (isStreaming.value) return `s:${result.value.length}`;
  return `d:${overviewText.value.length}:${keyPoints.value.join("|").length}`;
});
useAutoScroll(outputRef, scrollTick);

const { copied, copyText } = useCopyFeedback();
const toneOptions = TONE_STYLES.map((t) => ({
  value: t.value,
  label: t.label,
}));

/** 清空输出区（快捷预填时复用，不清输入框）。 */
function resetOutputState(): void {
  if (isStreaming.value) cancelCurrentTask();
  overviewText.value = "";
  keyPoints.value = [];
  result.value = "";
  error.value = "";
  elapsedTime.value = "--";
}

useQuickTextPrefill(inputText, resetOutputState);

onMounted(async () => {
  const msg = await recoverPersistedTask("summarize");
  if (msg) recoveryNotice.value = msg;
});

const {
  dragActive,
  fileInputRef,
  triggerFileSelect,
  handleFileChoose,
  handleDragOver,
  handleDragLeave,
  handleDrop,
} = useFileImport((text) => {
  inputText.value = text;
});

/** 复制概述与要点到剪贴板。 */
async function handleCopy(): Promise<void> {
  const text = formatSummaryForClipboard(overviewText.value, keyPoints.value);
  if (!text) return;
  await copyText(text);
}

/** 下载总结结果为 .txt 文件。 */
function handleDownload(): void {
  const content = formatSummaryForDownload(overviewText.value, keyPoints.value);
  if (!content) return;
  downloadTextFile(content, "linguist-summary.txt");
}

/** 清空输入、结果与流式状态；若正在生成则一并中止。 */
function handleClear(): void {
  resetOutputState();
  inputText.value = "";
}

/** 中止当前 SSE 任务。 */
async function handleStop(): Promise<void> {
  await runSafe(() => cancelCurrentTask());
}

/** 提交总结任务（SSE + 运行日志 + 结构化结果解析）。 */
async function handleSummarize(): Promise<void> {
  if (!inputText.value.trim() || isStreaming.value) return;

  await runSafe(
    async () => {
      overviewText.value = "";
      keyPoints.value = [];
      elapsedTime.value = "--";

      const activeLog = await createProcessingLog(
        "summarization",
        inputText.value.substring(0, 500),
        {
          summaryMode: summaryMode.value,
          keyPointsCount: keyPointsCount.value,
          wordLimit: wordLimit.value,
          tone: selectedTone.value,
        },
      );

      const logCallbacks = buildLinguistLogCallbacks(activeLog, {
        getCancelledOutput: () => result.value || "已取消",
        buildSuccessOutput: () =>
          JSON.stringify({
            overview: overviewText.value,
            keyPoints: keyPoints.value,
          }),
      });

      await submitTask(
        "summarize",
        {
          text: inputText.value,
          summaryMode: summaryMode.value,
          keyPointsCount: keyPointsCount.value,
          wordLimit: wordLimit.value,
          tone: selectedTone.value,
        },
        {
          onDone: (payload) => {
            elapsedTime.value = payload.duration || elapsedTime.value;
            if (payload.status !== "cancelled") {
              const summary =
                (payload.result as
                  | { overview?: string; keyPoints?: string[] }
                  | undefined) ?? {};
              overviewText.value = summary.overview || "";
              keyPoints.value = summary.keyPoints || [];
              result.value = "";
            }
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
  <div
    class="space-y-6 p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full min-w-0 overflow-x-hidden"
    id="summarization-view"
  >
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--color-outline-variant)]/40 pb-5"
    >
      <div>
        <h2
          class="font-display text-xl sm:text-2xl font-bold text-ui flex items-center gap-2"
        >
          <FileText class="w-6 h-6 text-[#00a67e]" />
          智能要点总结
        </h2>
        <p class="text-xs text-ui-muted mt-1">
          在可配置的篇幅与要点数量下，对会议记录、文档、代码块等进行高压缩总结。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <StreamingBadge :active="isStreaming" label="正在生成总结…" />
      </div>
    </div>

    <ApiKeyBanner
      :connected="apiConnected"
      description="模型服务当前离线。请在 backend/.env 中配置 GLM_API_KEY 后重启 Sidecar。"
    />

    <div
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 p-4 sm:p-5 bg-[var(--color-surface-header)]/40 border border-[var(--color-outline-variant)]/60 rounded"
    >
      <div id="cfg-summary-mode" class="md:col-span-2 lg:col-span-1">
        <label
          class="block text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2"
          >总结方式</label
        >
        <a-radio-group
          v-model:value="summaryMode"
          size="small"
          button-style="solid"
          class="tone-radio-group"
          :disabled="isStreaming"
        >
          <a-radio-button
            v-for="mode in SUMMARY_MODES"
            :key="mode.value"
            :value="mode.value"
          >
            {{ mode.label }}
          </a-radio-button>
        </a-radio-group>
        <p
          class="text-[10px] text-[var(--color-mono-text)]/60 mt-2 leading-relaxed"
        >
          {{ SUMMARY_MODES.find((m) => m.value === summaryMode)?.description }}
        </p>
      </div>

      <div v-if="summaryMode === 'words'" id="cfg-word-limit">
        <div
          class="flex items-center justify-between text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2"
        >
          <span>概要字数上限</span>
          <span
            class="text-ui bg-[var(--color-input-bg)] px-1.5 py-0.5 rounded border border-[var(--color-outline-variant)]/60 font-semibold"
            >{{ wordLimit }} 字</span
          >
        </div>
        <input
          v-model.number="wordLimit"
          type="range"
          min="50"
          max="800"
          step="50"
          :disabled="isStreaming"
          class="range-control w-full"
        />
      </div>

      <template v-else>
        <div id="cfg-points-count">
          <div
            class="flex items-center justify-between text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2"
          >
            <span>要点数量</span>
            <span
              class="text-ui bg-[var(--color-input-bg)] px-1.5 py-0.5 rounded border border-[var(--color-outline-variant)]/60 font-semibold"
              >{{ keyPointsCount }} 条</span
            >
          </div>
          <input
            v-model.number="keyPointsCount"
            type="range"
            min="3"
            max="10"
            step="1"
            :disabled="isStreaming"
            class="range-control w-full"
          />
        </div>

        <div id="cfg-point-word-limit">
          <div
            class="flex items-center justify-between text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2"
          >
            <span>每条要点字数</span>
            <span
              class="text-ui bg-[var(--color-input-bg)] px-1.5 py-0.5 rounded border border-[var(--color-outline-variant)]/60 font-semibold"
              >{{ wordLimit }} 字</span
            >
          </div>
          <input
            v-model.number="wordLimit"
            type="range"
            min="50"
            max="800"
            step="50"
            :disabled="isStreaming"
            class="range-control w-full"
          />
        </div>
      </template>

      <div id="cfg-tone-style">
        <label
          class="block text-[10px] font-mono text-ui-muted uppercase tracking-wider mb-2"
          >摘要语气风格</label
        >
        <a-select
          v-model:value="selectedTone"
          size="small"
          :options="toneOptions"
          class="form-select w-full"
          :disabled="isStreaming"
        />
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] flex flex-col justify-between overflow-hidden"
      >
        <div
          class="px-5 py-3 border-b border-[var(--color-outline-variant)] bg-[var(--color-surface-header)] flex items-center justify-between gap-2"
        >
          <span
            class="text-xs font-semibold text-ui-muted flex items-center gap-1.5 shrink min-w-0"
          >
            <Sliders class="w-3.5 h-3.5" />
            源文档输入
          </span>
          <div class="flex shrink-0 items-center gap-1">
            <input
              ref="fileInputRef"
              type="file"
              class="hidden"
              accept=".txt,.md"
              @change="handleFileChoose"
            />
            <a-button
              type="default"
              size="small"
              class="action-btn shrink-0"
              :disabled="isStreaming"
              @click="triggerFileSelect"
            >
              <template #icon><Upload class="w-3.5 h-3.5" /></template>
              导入 TXT/MD
            </a-button>
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
        </div>

        <div
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          :class="[
            'p-4 sm:p-5 h-56 sm:h-[350px] overflow-y-auto custom-scrollbar flex flex-col transition-all duration-150 relative',
            dragActive
              ? 'bg-[#00a67e]/5 border-2 border-dashed border-[#00a67e]/60'
              : '',
          ]"
        >
          <textarea
            v-model="inputText"
            placeholder="粘贴日志、会议记录、草稿笔记，或拖放 .txt/.md 文件到此处…"
            maxlength="50000"
            :disabled="isStreaming"
            class="resize-none w-full flex-1 bg-transparent text-ui text-sm focus:outline-none placeholder-[var(--color-placeholder)] leading-relaxed custom-scrollbar outline-none focus:ring-0 disabled:opacity-60"
          />
          <div
            v-if="dragActive"
            class="absolute inset-0 bg-[var(--color-surface)]/90 flex flex-col items-center justify-center p-6 text-center"
          >
            <Upload class="w-12 h-12 text-[#00a67e] mb-2 animate-bounce" />
            <span class="text-sm font-semibold text-ui">松开以导入文档</span>
          </div>
        </div>

        <div
          class="px-5 py-3 border-t border-[var(--color-outline-variant)] bg-[var(--color-surface-header)] flex items-center justify-between gap-3 text-xs text-ui-muted font-mono"
        >
          <span class="shrink min-w-0 truncate"
            >已加载 {{ inputText.length.toLocaleString() }} 字符</span
          >
          <a-button
            v-if="isStreaming"
            type="primary"
            danger
            size="small"
            class="action-btn shrink-0"
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
            class="action-btn shrink-0"
            :disabled="!inputText.trim()"
            @click="handleSummarize"
          >
            <template #icon><Sparkles class="w-3.5 h-3.5" /></template>
            生成总结
          </a-button>
        </div>
      </div>

      <div
        class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] flex flex-col justify-between overflow-hidden"
      >
        <div
          class="px-5 py-3 border-b border-[var(--color-outline-variant)] bg-[var(--color-surface-header)] flex items-center justify-between"
        >
          <span class="text-xs font-semibold text-ui-muted"
            >执行摘要与要点</span
          >
          <div
            v-if="(overviewText || keyPoints.length > 0) && !isStreaming"
            class="flex items-center gap-1"
          >
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

        <div
          ref="outputRef"
          class="p-4 sm:p-5 h-56 sm:h-[350px] overflow-y-auto custom-scrollbar flex flex-col bg-[var(--color-background)]/40"
        >
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
              <span class="font-semibold text-ui block">分析失败</span>
              <span>{{ error }}</span>
            </div>
          </div>

          <div
            v-else-if="isStreaming && result"
            class="text-xs text-[var(--color-mono-text)] font-mono leading-relaxed whitespace-pre-wrap break-words"
          >
            <span
              class="flex items-center gap-1.5 text-[10px] text-[#00a67e] tracking-wider uppercase font-semibold mb-2"
            >
              <span
                class="animate-spin rounded-full h-2.5 w-2.5 border-2 border-t-transparent border-[#00a67e]"
              ></span>
              流式生成中…
            </span>
            {{ result
            }}<span
              class="inline-block w-1.5 h-3.5 ml-0.5 align-middle bg-[#00a67e] animate-pulse"
            ></span>
          </div>

          <div
            v-else-if="isStreaming"
            class="my-auto flex flex-col justify-center items-center gap-3"
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
                >正在综合提炼要点…</span
              >
              <span class="text-[10px] text-ui-subtle font-mono"
                >流式连接已建立，等待首个 token</span
              >
            </div>
          </div>

          <div
            v-else-if="!isStreaming && (overviewText || keyPoints.length > 0)"
            class="space-y-6 text-sm"
          >
            <div v-if="overviewText">
              <span
                class="flex items-center gap-1.5 text-[10px] text-[#00a67e] font-mono tracking-wider uppercase font-semibold mb-2"
              >
                <Sparkle class="w-3 h-3 fill-current" />
                {{ summaryMode === "words" ? "概要总结" : "概述摘要" }}
              </span>
              <p
                class="text-ui bg-[var(--color-chat-bubble)]/40 border border-[var(--color-outline-variant)]/30 p-4 rounded leading-relaxed selection:bg-[#00a67e]/40"
              >
                <TruncatedText :text="overviewText" />
              </p>
            </div>
            <div v-if="summaryMode === 'points' && keyPoints.length > 0">
              <span
                class="flex items-center gap-1.5 text-[10px] text-sky-400 font-mono tracking-wider uppercase font-semibold mb-3"
              >
                <Sparkle class="w-3 h-3 fill-current" />
                核心要点提炼
              </span>
              <ul class="space-y-2.5">
                <li
                  v-for="(point, idx) in keyPoints"
                  :key="idx"
                  class="flex gap-3 text-ui leading-relaxed text-xs p-3.5 rounded bg-[var(--color-surface-header)]/50 border border-[var(--color-outline-variant)]/40 items-start hover:border-[#00a67e]/30 transition-all"
                >
                  <span
                    class="w-5 h-5 rounded bg-[#00a67e]/10 border border-[#00a67e]/20 text-[#00a67e] text-[10px] font-mono font-bold flex items-center justify-center shrink-0 mt-0.5"
                  >
                    {{ idx + 1 }}
                  </span>
                  <span><TruncatedText :text="point" :limit="2000" /></span>
                </li>
              </ul>
            </div>
          </div>

          <div
            v-else
            class="my-auto flex flex-col justify-center items-center text-center text-[var(--color-placeholder)]"
          >
            <FileText class="w-10 h-10 mb-2 stroke-[1.2]" />
            <span class="text-xs">概述与要点将显示在此处。</span>
          </div>
        </div>

        <div
          class="px-5 py-3 border-t border-[var(--color-outline-variant)] bg-[var(--color-surface-header)] flex items-center justify-between text-[10px] text-ui-muted font-mono"
        >
          <div class="flex items-center gap-1">
            <Clock class="w-3 h-3 text-[#00a67e]" />
            <span>处理耗时：{{ elapsedTime }}</span>
          </div>
          <span class="uppercase"
            >语气：{{
              TONE_STYLES.find((t) => t.value === selectedTone)?.label ??
              selectedTone
            }}</span
          >
        </div>
      </div>
    </div>
  </div>
</template>
