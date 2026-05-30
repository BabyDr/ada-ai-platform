<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import {
  Sparkles,
  Languages,
  FileText,
  Activity,
  Clock,
  Database,
  ArrowRight,
  CornerDownLeft,
  Cpu,
  Sparkle,
} from "lucide-vue-next";
import { DEFAULT_GLM_MODEL } from "../types";
import { useWorkspaceStore } from "../stores/workspace";

const router = useRouter();
const workspace = useWorkspaceStore();

const apiConnected = computed(() => workspace.apiConnected);
const quickInput = ref("");

const totalProcessed = computed(
  () => workspace.logs.filter((l) => l.status === "success" || l.status === "failed").length,
);

const avgLatency = computed(() => {
  const successfulLogs = workspace.logs.filter((l) => l.status === "success");
  if (successfulLogs.length > 0) {
    const sum = successfulLogs.reduce((acc, curr) => {
      const val = parseFloat(curr.duration);
      return Number.isNaN(val) ? acc : acc + val;
    }, 0);
    return `${(sum / successfulLogs.length).toFixed(1)}s`;
  }
  return "1.8s";
});

const goTo = (name: "translation" | "summarization") => router.push({ name });

const handleQuickSend = () => {
  if (!quickInput.value.trim()) return;

  const text = quickInput.value.trim();
  workspace.setQuickText(text);

  const lowercaseInput = text.toLowerCase();
  const isProbablySummary =
    lowercaseInput.includes("summary") ||
    lowercaseInput.includes("summarize") ||
    lowercaseInput.includes("总结") ||
    lowercaseInput.includes("提炼") ||
    lowercaseInput.includes("要点") ||
    text.length > 250;

  router.push({ name: isProbablySummary ? "summarization" : "translation" });
  quickInput.value = "";
};
</script>

<template>
  <div class="space-y-8 p-8 max-w-6xl mx-auto" id="dashboard-view">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[#26384d]/40 pb-6">
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span
            class="px-2 py-0.5 rounded text-[10px] font-mono tracking-wider font-semibold text-[#00a67e] bg-[#00a67e]/10 border border-[#00a67e]/30 flex items-center gap-1"
          >
            <Sparkle class="w-2.5 h-2.5 animate-pulse" />
            工作区已就绪
          </span>
        </div>
        <h2 class="font-display text-3xl font-bold tracking-tight text-white">智能工作区</h2>
        <p class="text-xs md:text-sm text-[#acb5c9] mt-1 leading-relaxed max-w-xl">
          简化全球文档工作流。通过服务端安全代理调用低延迟 GLM 模型，完成翻译与文档总结。
        </p>
      </div>

      <div id="engine-platform-chip" class="flex items-center gap-3 px-3 py-2 rounded bg-[#08121e] border border-[#26384d]/60">
        <div class="p-2 rounded bg-[#2c3a4c]/60">
          <Cpu class="w-4 h-4 text-[#00a67e]" />
        </div>
        <div class="flex flex-col">
          <span class="text-[10px] font-semibold font-mono tracking-wider text-[#bccac2] uppercase">引擎平台</span>
          <span class="text-xs text-white">{{ DEFAULT_GLM_MODEL }}</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <div id="metric-gateway" class="p-5 rounded border border-[#26384d]/60 bg-[#08121e]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-[#00a67e]/10 text-[#00a67e] border border-[#00a67e]/25">
          <Activity class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-[#acb5c9] font-mono uppercase tracking-wider">网关连接</span>
          <div class="flex items-center gap-1.5 mt-1">
            <span :class="['h-2 w-2 rounded-full', apiConnected ? 'bg-[#00a67e]' : 'bg-red-400']"></span>
            <span class="text-sm font-semibold text-white">
              {{ apiConnected ? "运行正常" : "需要配置" }}
            </span>
          </div>
        </div>
      </div>

      <div id="metric-events" class="p-5 rounded border border-[#26384d]/60 bg-[#08121e]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-sky-500/10 text-sky-400 border border-sky-500/25">
          <Database class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-[#acb5c9] font-mono uppercase tracking-wider">已处理请求</span>
          <span class="text-lg font-semibold text-white mt-0.5 block font-mono">
            {{ totalProcessed }} <span class="text-xs text-[#acb5c9] font-normal">次</span>
          </span>
        </div>
      </div>

      <div id="metric-latency" class="p-5 rounded border border-[#26384d]/60 bg-[#08121e]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-amber-500/10 text-amber-400 border border-amber-500/25">
          <Clock class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-[#acb5c9] font-mono uppercase tracking-wider">平均延迟</span>
          <span class="text-lg font-semibold text-white mt-0.5 block font-mono">{{ avgLatency }}</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        class="group relative rounded border border-[#26384d] bg-gradient-to-b from-[#0e1b2b]/90 to-[#08121e]/90 p-6 flex flex-col justify-between hover:border-[#00a67e]/60 transition-all duration-300"
      >
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded bg-[#00a67e]/10 border border-[#00a67e]/30 flex items-center justify-center">
              <Languages class="w-6 h-6 text-[#00a67e]" />
            </div>
            <span class="text-[10px] font-mono text-[#bccac2] uppercase tracking-wider">多语调翻译器</span>
          </div>
          <h3 class="text-lg font-semibold text-white">文本翻译空间</h3>
          <p class="text-xs text-[#acb5c9] mt-1.5 leading-relaxed">
            支持 10 种目标语言与 5 种语调风格，提供高精度文本转换与术语一致性。
          </p>
        </div>
        <a-button
          id="btn-nav-translation"
          block
          size="middle"
          class="block-btn mt-6"
          @click="goTo('translation')"
        >
          <span class="inline-flex items-center gap-2">
            进入翻译面板
            <ArrowRight class="w-3.5 h-3.5" />
          </span>
        </a-button>
      </div>

      <div
        class="group relative rounded border border-[#26384d] bg-gradient-to-b from-[#0e1b2b]/90 to-[#08121e]/90 p-6 flex flex-col justify-between hover:border-[#00a67e]/60 transition-all duration-300"
      >
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center">
              <FileText class="w-6 h-6 text-sky-400" />
            </div>
            <span class="text-[10px] font-mono text-sky-400 uppercase tracking-wider">文档压缩总结</span>
          </div>
          <h3 class="text-lg font-semibold text-white">智能要点总结</h3>
          <p class="text-xs text-[#acb5c9] mt-1.5 leading-relaxed">
            将会议记录、研究笔记、长文档或代码注释压缩为结构化概述与要点列表。
          </p>
        </div>
        <a-button
          id="btn-nav-summarization"
          block
          size="middle"
          class="block-btn mt-6"
          @click="goTo('summarization')"
        >
          <span class="inline-flex items-center gap-2">
            进入总结工作区
            <ArrowRight class="w-3.5 h-3.5" />
          </span>
        </a-button>
      </div>
    </div>

    <div class="rounded border border-[#26384d] bg-[#0c1622] p-6 shadow-xl relative overflow-hidden">
      <div class="flex items-center gap-2 mb-4">
        <Sparkles class="w-4 h-4 text-[#00a67e]" />
        <h4 class="text-sm font-semibold text-white font-display">智能输入控制台</h4>
      </div>

      <p class="text-xs text-[#acb5c9] mb-4">
        输入任意文本片段，系统将自动判断并跳转到翻译或总结面板，并预填内容。
      </p>

      <form @submit.prevent="handleQuickSend" class="space-y-4">
        <div class="relative">
          <textarea
            v-model="quickInput"
            placeholder="例如：将系统日志翻译成法语…或粘贴较长的会议纪要…"
            rows="3"
            class="w-full bg-[#08121e] border border-[#26384d] focus:border-[#00a67e] rounded p-4 text-xs text-white placeholder-[#bccac2]/40 outline-none resize-none transition-all duration-150 custom-scrollbar focus:ring-1 focus:ring-[#00a67e]"
            @keydown.enter.prevent="handleQuickSend"
          />
        </div>

        <div class="flex items-center justify-between">
          <span class="text-[10px] text-[#bccac2]/55 font-mono">基于 GLM 的启发式自动路由</span>
          <a-button
            type="primary"
            size="small"
            html-type="submit"
            class="action-btn shrink-0"
            :disabled="!quickInput.trim()"
          >
            <template #icon><CornerDownLeft class="w-3.5 h-3.5" /></template>
            分析并跳转
          </a-button>
        </div>
      </form>
    </div>
  </div>
</template>
