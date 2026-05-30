<script setup lang="ts">
import { computed, ref, watch } from "vue";
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
import { SUPPORTED_LANGUAGES, TONE_STYLES, type LogEntry } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import { useTask } from "../composables/useTask";

const workspace = useWorkspaceStore();
const apiConnected = computed(() => workspace.apiConnected);

// 流式输出：result 即逐 token 追加的译文（打字机效果）。
const { result, isStreaming, error, submitTask, cancelCurrentTask } = useTask();

const inputText = ref("");
const sourceLang = ref("auto");
const targetLang = ref("zh");
const selectedTone = ref<"Professional" | "Conversational" | "Technical" | "Academic" | "Creative">("Professional");

const copied = ref(false);
const elapsedTime = ref("--");

// 工作台快捷输入 → 预填（消费一次）。
watch(
  () => workspace.quickText,
  (newVal) => {
    if (newVal) {
      inputText.value = newVal;
      workspace.setQuickText("");
    }
  },
  { immediate: true },
);

const handleCopy = async () => {
  if (!result.value) return;
  try {
    await navigator.clipboard.writeText(result.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch (err) {
    console.error("Failed to copy text", err);
  }
};

const handleDownload = () => {
  if (!result.value) return;
  const element = document.createElement("a");
  const file = new Blob([result.value], { type: "text/plain;charset=utf-8" });
  element.href = URL.createObjectURL(file);
  element.download = `linguist-translation-${targetLang.value}.txt`;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
};

const handleClear = () => {
  inputText.value = "";
  result.value = "";
  error.value = "";
  elapsedTime.value = "--";
};

const handleSwapLanguages = () => {
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
};

const handleStop = () => cancelCurrentTask();

const handleTranslate = async () => {
  if (!inputText.value.trim()) return;
  elapsedTime.value = "--";

  let activeLog: LogEntry | null = null;
  try {
    activeLog = await workspace.addLog({
      type: "translation",
      input: inputText.value.substring(0, 500),
      output: "...",
      duration: "--",
      status: "processing",
      details: {
        sourceLang: SUPPORTED_LANGUAGES.find((l) => l.code === sourceLang.value)?.name || sourceLang.value,
        targetLang: SUPPORTED_LANGUAGES.find((l) => l.code === targetLang.value)?.name || targetLang.value,
        tone: selectedTone.value,
      },
    });
  } catch (e) {
    console.warn("Log creation failed: ", e);
  }

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
        if (!activeLog) return;
        if (payload.status === "cancelled") {
          workspace.updateLog(activeLog.id, {
            status: "failed",
            output: result.value || "已取消",
            duration: elapsedTime.value,
            error: "用户已停止生成",
          });
          return;
        }
        const out = (payload.result as { text?: string } | undefined)?.text ?? result.value;
        workspace.updateLog(activeLog.id, { status: "success", output: out, duration: elapsedTime.value });
      },
      onError: (message) => {
        if (activeLog) {
          workspace.updateLog(activeLog.id, {
            status: "failed",
            output: message,
            duration: "0s",
            error: message,
          });
        }
      },
    },
  );
};
</script>

<template>
  <div class="space-y-6 p-8 max-w-6xl mx-auto" id="translation-view">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#26384d]/40 pb-5">
      <div>
        <h2 class="font-display text-2xl font-bold text-white flex items-center gap-2">
          <Languages class="w-6 h-6 text-[#00a67e]" />
          文本翻译器 · 双栏对照
        </h2>
        <p class="text-xs text-[#acb5c9] mt-1">
          覆盖 10 种全球语言，针对技术词汇与上下文一致性进行标准化翻译。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="isStreaming"
          class="px-2.5 py-1 text-[10px] font-mono font-semibold bg-[#00a67e]/10 text-[#00a67e] border border-[#00a67e]/35 rounded-full flex items-center gap-1.5"
        >
          <span class="animate-spin rounded-full h-2 w-2 border-2 border-t-transparent border-[#00a67e]"></span>
          流式翻译中...
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
          模型服务当前离线。请在 backend/.env 中配置 GLM_API_KEY 或 ZHIPU_API_KEY 后重启 Sidecar。
        </span>
      </div>
    </div>

    <div class="p-4 rounded-xl bg-[#08121e]/40 border border-[#26384d]/60">
      <label class="block text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider mb-2.5">
        选择译文语调
      </label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="t in TONE_STYLES"
          :key="t.value"
          type="button"
          @click="selectedTone = t.value as typeof selectedTone"
          :class="[
            'px-4 py-2 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer',
            selectedTone === t.value
              ? 'bg-gradient-to-r from-[#00a67e] to-[#008f6c] text-white border-b-2 border-white/20'
              : 'bg-[#122131]/60 text-[#acb5c9] border border-[#26384d] hover:bg-[#26384d]',
          ]"
        >
          <div class="flex items-center gap-1.5">
            <Sparkle v-if="selectedTone === t.value" class="w-3 h-3 text-white fill-current animate-pulse" />
            <span>{{ t.label }}</span>
          </div>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="rounded-2xl border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden">
        <div class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold text-[#acb5c9]">源语言</span>
            <select
              v-model="sourceLang"
              class="bg-[#122131] border border-[#26384d]/60 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-[#00a67e]"
            >
              <option v-for="l in SUPPORTED_LANGUAGES" :key="l.code" :value="l.code">{{ l.name }}</option>
            </select>
          </div>
          <button
            v-if="inputText"
            type="button"
            @click="handleClear"
            class="p-1.5 rounded bg-[#122131] hover:bg-red-500/10 border border-[#26384d]/60 text-red-400 text-xs transition-colors flex items-center gap-1 cursor-pointer"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
        </div>

        <div class="p-5 flex-1 min-h-[300px] flex flex-col">
          <textarea
            v-model="inputText"
            placeholder="在此输入待翻译文本或原始文档…"
            maxlength="10000"
            class="resize-none w-full flex-1 bg-transparent text-white text-sm focus:outline-none placeholder-[#bccac2]/35 leading-relaxed custom-scrollbar outline-none focus:ring-0"
          />
        </div>

        <div class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between text-xs text-[#acb5c9] font-mono">
          <span>{{ inputText.length }} / 10,000 字符</span>
          <div class="flex items-center gap-2">
            <button
              v-if="isStreaming"
              type="button"
              @click="handleStop"
              class="flex items-center gap-2 px-5 py-2 rounded-xl bg-red-500/90 hover:bg-red-500 text-white font-semibold text-xs transition-all cursor-pointer"
            >
              <Square class="w-3.5 h-3.5 fill-current" />
              停止生成
            </button>
            <button
              v-else
              type="button"
              @click="handleTranslate"
              :disabled="!inputText.trim()"
              class="flex items-center gap-2 px-5 py-2 rounded-xl bg-[#00a67e] hover:bg-[#008f6c] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-xs transition-all cursor-pointer"
            >
              <Sparkles class="w-3.5 h-3.5" />
              开始翻译
            </button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-[#26384d] bg-[#0c1622] flex flex-col justify-between overflow-hidden relative">
        <div class="absolute top-1/2 left-0 transform -translate-y-1/2 -translate-x-[18px] z-10 hidden lg:block">
          <button
            type="button"
            @click="handleSwapLanguages"
            class="w-8 h-8 rounded-full border border-[#26384d] bg-[#122131] text-white hover:text-[#00a67e] hover:border-[#00a67e]/60 flex items-center justify-center shadow-lg transition-colors cursor-pointer"
          >
            <ArrowRightLeft class="w-3.5 h-3.5" />
          </button>
        </div>

        <div class="px-5 py-3 border-b border-[#26384d] bg-[#08121e] flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xs font-semibold text-[#acb5c9]">目标语言</span>
            <select
              v-model="targetLang"
              class="bg-[#122131] border border-[#26384d]/60 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-[#00a67e]"
            >
              <option v-for="l in SUPPORTED_LANGUAGES.filter((la) => la.code !== 'auto')" :key="l.code" :value="l.code">
                {{ l.name }}
              </option>
            </select>
          </div>
          <div v-if="result" class="flex items-center gap-1.5">
            <button
              type="button"
              @click="handleCopy"
              class="p-1.5 rounded bg-[#122131] hover:bg-[#26384d] text-white border border-[#26384d]/60 text-xs flex items-center gap-1 cursor-pointer transition-colors"
            >
              <Check v-if="copied" class="w-3.5 h-3.5 text-[#00a67e]" />
              <Copy v-else class="w-3.5 h-3.5" />
              <span>{{ copied ? "已复制" : "复制" }}</span>
            </button>
            <button
              type="button"
              @click="handleDownload"
              class="p-1.5 rounded bg-[#122131] hover:bg-[#26384d] text-white border border-[#26384d]/60 text-xs flex items-center gap-1 cursor-pointer transition-colors"
            >
              <Download class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div class="p-5 flex-1 min-h-[300px] flex flex-col bg-[#020c15]/40">
          <div
            v-if="error"
            class="p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-xs leading-relaxed flex items-start gap-2.5"
          >
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span class="font-semibold text-white block">执行失败</span>
              <span>{{ error }}</span>
            </div>
          </div>

          <div
            v-else-if="result"
            class="text-white text-sm leading-relaxed whitespace-pre-wrap flex-1 select-text selection:bg-[#00a67e]/40 custom-scrollbar overflow-y-auto"
          >
            {{ result }}<span v-if="isStreaming" class="inline-block w-1.5 h-4 ml-0.5 align-middle bg-[#00a67e] animate-pulse"></span>
          </div>

          <div v-else-if="isStreaming" class="flex-1 flex flex-col justify-center items-center gap-3">
            <div class="relative flex h-10 w-10">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00a67e] opacity-40"></span>
              <div class="relative rounded-full h-10 w-10 bg-[#00a67e]/20 border border-[#00a67e]/40 flex items-center justify-center">
                <Sparkles class="w-5 h-5 text-[#00a67e] animate-pulse" />
              </div>
            </div>
            <div class="text-center">
              <span class="text-xs font-medium text-white block">正在思考并翻译…</span>
              <span class="text-[10px] text-[#bccac2]/70">流式连接已建立，等待首个 token</span>
            </div>
          </div>

          <div v-else class="flex-1 flex flex-col justify-center items-center text-center text-[#bccac2]/35">
            <Languages class="w-10 h-10 mb-2 stroke-[1.2]" />
            <span class="text-xs">翻译结果将显示在右侧。</span>
          </div>
        </div>

        <div class="px-5 py-3 border-t border-[#26384d] bg-[#08121e] flex items-center justify-between text-[10px] text-[#acb5c9] font-mono">
          <div class="flex items-center gap-1">
            <Clock class="w-3 h-3 text-[#00a67e]" />
            <span>耗时：{{ elapsedTime }}</span>
          </div>
          <span>语调：{{ TONE_STYLES.find((t) => t.value === selectedTone)?.label ?? selectedTone }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
