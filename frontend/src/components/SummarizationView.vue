<script setup lang="ts">
import { ref, watch } from "vue";
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
} from "lucide-vue-next";
import { TONE_STYLES, type LogEntry } from "../types";
import * as api from "../services/linguistApi";

interface Props {
  quickText: string;
  apiConnected: boolean;
  onAddLog: (log: Omit<LogEntry, "id" | "timestamp" | "date">) => Promise<LogEntry>;
  onUpdateLog: (id: string, updates: Partial<LogEntry>) => void;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: "update:quickText", text: string): void;
}>();

const inputText = ref("");
const overviewText = ref("");
const keyPoints = ref<string[]>([]);
const keyPointsCount = ref(5);
const wordLimit = ref(250);
const selectedTone = ref<"Professional" | "Conversational" | "Technical" | "Academic" | "Creative">("Professional");

const isProcessing = ref(false);
const copied = ref(false);
const errorText = ref("");
const elapsedTime = ref("--");
const dragActive = ref(false);

const fileInputRef = ref<HTMLInputElement | null>(null);

watch(
  () => props.quickText,
  (newVal) => {
    if (newVal) {
      inputText.value = newVal;
      emit("update:quickText", "");
    }
  },
  { immediate: true },
);

const handleCopy = async () => {
  let textToCopy = "";
  if (overviewText.value) textToCopy += `概述：\n${overviewText.value}\n\n`;
  if (keyPoints.value.length > 0) {
    textToCopy += `核心要点：\n` + keyPoints.value.map((kp, idx) => `${idx + 1}. ${kp}`).join("\n");
  }
  if (!textToCopy) return;
  try {
    await navigator.clipboard.writeText(textToCopy);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch (err) {
    console.error("Failed to copy text", err);
  }
};

const handleDownload = () => {
  let content = "";
  if (overviewText.value) content += `概述：\n${overviewText.value}\n\n`;
  if (keyPoints.value.length > 0) {
    content += `核心要点：\n` + keyPoints.value.map((kp) => `- ${kp}`).join("\n");
  }
  if (!content) return;
  const element = document.createElement("a");
  const file = new Blob([content], { type: "text/plain;charset=utf-8" });
  element.href = URL.createObjectURL(file);
  element.download = "linguist-summary.txt";
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
};

const handleClear = () => {
  inputText.value = "";
  overviewText.value = "";
  keyPoints.value = [];
  errorText.value = "";
  elapsedTime.value = "--";
};

const triggerFileSelect = () => fileInputRef.value?.click();

const handleFileChoose = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files?.[0]) loadFile(target.files[0]);
};

const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  dragActive.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault();
  dragActive.value = false;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  dragActive.value = false;
  if (e.dataTransfer?.files?.[0]) loadFile(e.dataTransfer.files[0]);
};

const loadFile = (file: File) => {
  if (file.type !== "text/plain" && !file.name.endsWith(".md") && !file.name.endsWith(".txt")) {
    alert("不支持的文件类型，仅接受 .txt 与 .md 文档。");
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    if (e.target && typeof e.target.result === "string") inputText.value = e.target.result;
  };
  reader.readAsText(file);
};

const handleSummarize = async () => {
  if (!inputText.value.trim()) return;

  isProcessing.value = true;
  errorText.value = "";
  overviewText.value = "";
  keyPoints.value = [];
  elapsedTime.value = "--";
  const startTime = Date.now();

  let activeLog: LogEntry | null = null;
  try {
    activeLog = await props.onAddLog({
      type: "summarization",
      input: inputText.value.substring(0, 500),
      output: "...",
      duration: "--",
      status: "processing",
      details: {
        keyPointsCount: keyPointsCount.value,
        wordLimit: wordLimit.value,
        tone: selectedTone.value,
      },
    });
  } catch (e) {
    console.warn("Log creation failed: ", e);
  }

  try {
    const data = await api.summarize({
      text: inputText.value,
      keyPointsCount: keyPointsCount.value,
      wordLimit: wordLimit.value,
      tone: selectedTone.value,
    });

    const duration = data.duration || `${((Date.now() - startTime) / 1000).toFixed(1)}s`;
    elapsedTime.value = duration;

    const summaryData = data.result || { overview: "", keyPoints: [] as string[] };
    overviewText.value = summaryData.overview || "";
    keyPoints.value = summaryData.keyPoints || [];

    if (activeLog) {
      props.onUpdateLog(activeLog.id, {
        status: "success",
        output: JSON.stringify(summaryData),
        duration,
      });
    }
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : "总结处理失败。";
    errorText.value = errMessage;
    if (activeLog) {
      props.onUpdateLog(activeLog.id, {
        status: "failed",
        output: errMessage,
        duration: "0s",
        error: errMessage,
      });
    }
  } finally {
    isProcessing.value = false;
  }
};
</script>

<template>
  <div class="space-y-6 p-8 max-w-6xl mx-auto" id="summarization-view">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#26384d]/40 pb-5">
      <div>
        <h2 class="font-display text-2xl font-bold text-white flex items-center gap-2">
          <FileText class="w-6 h-6 text-[#00a67e]" />
          智能要点总结
        </h2>
        <p class="text-xs text-[#acb5c9] mt-1">
          在可配置的篇幅与要点数量下，对会议记录、文档、代码块等进行高压缩总结。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="isProcessing"
          class="px-2.5 py-1 text-[10px] font-mono font-semibold bg-[#00a67e]/10 text-[#00a67e] border border-[#00a67e]/35 rounded-full flex items-center gap-1.5"
        >
          <span class="animate-spin rounded-full h-2 w-2 border-2 border-t-transparent border-[#00a67e]"></span>
          正在生成总结…
        </span>
      </div>
    </div>

    <div
      v-if="!apiConnected"
      class="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3"
    >
      <AlertTriangle class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
      <div>
        <span class="text-xs font-semibold text-white block">未检测到 GLM_API_KEY</span>
        <span class="text-xs text-[#acb5c9] leading-relaxed">
          请在 backend/.env 中配置 GLM_API_KEY 或 ZHIPU_API_KEY 以启用总结功能。
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 p-5 bg-[#08121e]/40 border border-[#26384d]/60 rounded-xl">
      <div id="cfg-word-limit">
        <div class="flex items-center justify-between text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider mb-2">
          <span>概述字数上限</span>
          <span class="text-white bg-[#122131] px-1.5 py-0.5 rounded border border-[#26384d]/60 font-semibold">{{ wordLimit }} 字</span>
        </div>
        <input v-model.number="wordLimit" type="range" min="50" max="800" step="50" class="w-full h-1.5 bg-[#122131] rounded-lg appearance-none cursor-pointer accent-[#00a67e]" />
      </div>

      <div id="cfg-points-count">
        <div class="flex items-center justify-between text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider mb-2">
          <span>要点数量</span>
          <span class="text-white bg-[#122131] px-1.5 py-0.5 rounded border border-[#26384d]/60 font-semibold">{{ keyPointsCount }} 条</span>
        </div>
        <input v-model.number="keyPointsCount" type="range" min="3" max="10" step="1" class="w-full h-1.5 bg-[#122131] rounded-lg appearance-none cursor-pointer accent-[#00a67e]" />
      </div>

      <div id="cfg-tone-style">
        <label class="block text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider mb-2">摘要语气风格</label>
        <select
          v-model="selectedTone"
          class="w-full bg-[#122131] border border-[#26384d]/60 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#00a67e]"
        >
          <option v-for="t in TONE_STYLES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="rounded-2xl border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden">
        <div class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between">
          <span class="text-xs font-semibold text-[#acb5c9] flex items-center gap-1.5">
            <Sliders class="w-3.5 h-3.5" />
            源文档输入
          </span>
          <div class="flex items-center gap-2">
            <input ref="fileInputRef" type="file" class="hidden" accept=".txt,.md" @change="handleFileChoose" />
            <button
              type="button"
              @click="triggerFileSelect"
              class="p-1.5 rounded bg-[#122131] hover:bg-[#26384d] border border-[#26384d]/60 text-white text-xs flex items-center gap-1 transition-colors cursor-pointer"
            >
              <Upload class="w-3.5 h-3.5" />
              <span>导入 TXT/MD</span>
            </button>
            <button
              v-if="inputText"
              type="button"
              @click="handleClear"
              class="p-1.5 rounded bg-[#122131] hover:bg-red-500/10 border border-[#26384d]/60 text-red-400 text-xs transition-colors flex items-center gap-1 cursor-pointer"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          :class="[
            'p-5 flex-1 min-h-[350px] flex flex-col transition-all duration-150 relative',
            dragActive ? 'bg-[#00a67e]/5 border-2 border-dashed border-[#00a67e]/60' : '',
          ]"
        >
          <textarea
            v-model="inputText"
            placeholder="粘贴日志、会议记录、草稿笔记，或拖放 .txt/.md 文件到此处…"
            class="resize-none w-full flex-1 bg-transparent text-white text-sm focus:outline-none placeholder-[#bccac2]/35 leading-relaxed custom-scrollbar outline-none focus:ring-0"
          />
          <div v-if="dragActive" class="absolute inset-0 bg-[#0c1622]/90 flex flex-col items-center justify-center p-6 text-center">
            <Upload class="w-12 h-12 text-[#00a67e] mb-2 animate-bounce" />
            <span class="text-sm font-semibold text-white">松开以导入文档</span>
          </div>
        </div>

        <div class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between text-xs text-[#acb5c9] font-mono">
          <span>已加载 {{ inputText.length.toLocaleString() }} 字符</span>
          <button
            type="button"
            @click="handleSummarize"
            :disabled="isProcessing || !inputText.trim() || !apiConnected"
            class="flex items-center gap-2 px-5 py-2 rounded-xl bg-[#00a67e] hover:bg-[#008f6c] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-xs transition-all cursor-pointer"
          >
            <Sparkles class="w-3.5 h-3.5" />
            生成总结
          </button>
        </div>
      </div>

      <div class="rounded-2xl border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden">
        <div class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between">
          <span class="text-xs font-semibold text-[#acb5c9]">执行摘要与要点</span>
          <div v-if="overviewText || keyPoints.length > 0" class="flex items-center gap-1.5">
            <button type="button" @click="handleCopy" class="p-1.5 rounded bg-[#122131] hover:bg-[#26384d] text-white border border-[#26384d]/60 text-xs flex items-center gap-1 transition-colors cursor-pointer">
              <Check v-if="copied" class="w-3.5 h-3.5 text-[#00a67e]" />
              <Copy v-else class="w-3.5 h-3.5" />
              <span>{{ copied ? "已复制" : "复制" }}</span>
            </button>
            <button type="button" @click="handleDownload" class="p-1.5 rounded bg-[#122131] hover:bg-[#26384d] text-white border border-[#26384d]/60 text-xs flex items-center gap-1 transition-colors cursor-pointer">
              <Download class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div class="p-5 flex-1 min-h-[350px] flex flex-col bg-[#020c15]/40 overflow-y-auto custom-scrollbar">
          <div v-if="isProcessing" class="my-auto flex flex-col justify-center items-center gap-3">
            <div class="relative flex h-10 w-10">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00a67e] opacity-40"></span>
              <div class="relative rounded-full h-10 w-10 bg-[#00a67e]/20 border border-[#00a67e]/40 flex items-center justify-center">
                <Sparkles class="w-5 h-5 text-[#00a67e] animate-pulse" />
              </div>
            </div>
            <div class="text-center">
              <span class="text-xs font-medium text-white block">正在综合提炼要点…</span>
              <span class="text-[10px] text-[#bccac2]/70 font-mono">正在运行 glm-4-flash 约束总结</span>
            </div>
          </div>

          <div
            v-else-if="errorText"
            class="p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-xs leading-relaxed flex items-start gap-2.5"
          >
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span class="font-semibold text-white block">分析失败</span>
              <span>{{ errorText }}</span>
            </div>
          </div>

          <div v-else-if="overviewText || keyPoints.length > 0" class="space-y-6 text-sm">
            <div v-if="overviewText">
              <span class="flex items-center gap-1.5 text-[10px] text-[#00a67e] font-mono tracking-wider uppercase font-semibold mb-2">
                <Sparkle class="w-3 h-3 fill-current" />
                概述摘要
              </span>
              <p class="text-white bg-[#0e1b2b]/40 border border-[#26384d]/30 p-4 rounded-xl leading-relaxed selection:bg-[#00a67e]/40">
                {{ overviewText }}
              </p>
            </div>
            <div v-if="keyPoints.length > 0">
              <span class="flex items-center gap-1.5 text-[10px] text-sky-400 font-mono tracking-wider uppercase font-semibold mb-3">
                <Sparkle class="w-3 h-3 fill-current" />
                核心要点提炼
              </span>
              <ul class="space-y-2.5">
                <li
                  v-for="(point, idx) in keyPoints"
                  :key="idx"
                  class="flex gap-3 text-white leading-relaxed text-xs p-3.5 rounded-xl bg-[#08121e]/50 border border-[#26384d]/40 items-start hover:border-[#00a67e]/30 transition-all"
                >
                  <span class="w-5 h-5 rounded-full bg-[#00a67e]/10 border border-[#00a67e]/20 text-[#00a67e] text-[10px] font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {{ idx + 1 }}
                  </span>
                  <span>{{ point }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div v-else class="my-auto flex flex-col justify-center items-center text-center text-[#bccac2]/35">
            <FileText class="w-10 h-10 mb-2 stroke-[1.2]" />
            <span class="text-xs">概述与要点将显示在此处。</span>
          </div>
        </div>

        <div class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between text-[10px] text-[#acb5c9] font-mono">
          <div class="flex items-center gap-1">
            <Clock class="w-3 h-3 text-[#00a67e]" />
            <span>处理耗时：{{ elapsedTime }}</span>
          </div>
          <span class="uppercase">语气：{{ TONE_STYLES.find((t) => t.value === selectedTone)?.label ?? selectedTone }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
