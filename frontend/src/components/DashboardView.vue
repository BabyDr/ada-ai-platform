<script setup lang="ts">
/**
 * Dashboard 工作台：指标概览、功能入口、智能快捷输入路由。
 * 统计与路由逻辑见 composables/useDashboardMetrics、useQuickRoute。
 */
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
import { useDashboardMetrics } from "../composables/useDashboardMetrics";
import { useQuickRoute } from "../composables/useQuickRoute";

const { apiConnected, llmMode, totalProcessed, avgLatency } = useDashboardMetrics();
const { quickInput, goTo, handleQuickSend } = useQuickRoute();
</script>

<template>
  <div class="space-y-8 p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full min-w-0 overflow-x-hidden" id="dashboard-view">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[var(--color-outline-variant)]/40 pb-6">
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span
            class="px-2 py-0.5 rounded text-[10px] font-mono tracking-wider font-semibold text-[#00a67e] bg-[#00a67e]/10 border border-[#00a67e]/30 flex items-center gap-1"
          >
            <Sparkle class="w-2.5 h-2.5 animate-pulse" />
            工作区已就绪
          </span>
          <span
            v-if="llmMode === 'mock'"
            class="px-2 py-0.5 rounded text-[10px] font-mono tracking-wider font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30"
            title="当前为 Mock 模式，未调用真实大模型"
          >
            Mock 模式
          </span>
        </div>
        <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight text-ui">智能工作区</h2>
        <p class="text-xs md:text-sm text-ui-muted mt-1 leading-relaxed max-w-xl">
          简化全球文档工作流。通过服务端安全代理调用低延迟 GLM 模型，完成翻译与文档总结。
        </p>
      </div>

      <div id="engine-platform-chip" class="flex items-center gap-3 px-3 py-2 rounded bg-[var(--color-surface-header)] border border-[var(--color-outline-variant)]/60">
        <div class="p-2 rounded bg-[var(--color-badge-bg)]">
          <Cpu class="w-4 h-4 text-[#00a67e]" />
        </div>
        <div class="flex flex-col">
          <span class="text-[10px] font-semibold font-mono tracking-wider text-[var(--color-mono-text)] uppercase">引擎平台</span>
          <span class="text-xs text-ui">{{ DEFAULT_GLM_MODEL }}</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <div id="metric-gateway" class="p-5 rounded border border-[var(--color-outline-variant)]/60 bg-[var(--color-surface-header)]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-[#00a67e]/10 text-[#00a67e] border border-[#00a67e]/25">
          <Activity class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-ui-muted font-mono uppercase tracking-wider">网关连接</span>
          <div class="flex items-center gap-1.5 mt-1">
            <span :class="['h-2 w-2 rounded-full', apiConnected ? 'bg-[#00a67e]' : 'bg-red-400']"></span>
            <span class="text-sm font-semibold text-ui">
              {{ apiConnected ? "运行正常" : "需要配置" }}
            </span>
          </div>
        </div>
      </div>

      <div id="metric-events" class="p-5 rounded border border-[var(--color-outline-variant)]/60 bg-[var(--color-surface-header)]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-sky-500/10 text-sky-400 border border-sky-500/25">
          <Database class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-ui-muted font-mono uppercase tracking-wider">已处理请求</span>
          <span class="text-lg font-semibold text-ui mt-0.5 block font-mono">
            {{ totalProcessed }} <span class="text-xs text-ui-muted font-normal">次</span>
          </span>
        </div>
      </div>

      <div id="metric-latency" class="p-5 rounded border border-[var(--color-outline-variant)]/60 bg-[var(--color-surface-header)]/40 flex items-center gap-4">
        <div class="p-3 rounded bg-amber-500/10 text-amber-400 border border-amber-500/25">
          <Clock class="w-5 h-5" />
        </div>
        <div>
          <span class="block text-[10px] text-ui-muted font-mono uppercase tracking-wider">平均延迟</span>
          <span class="text-lg font-semibold text-ui mt-0.5 block font-mono">{{ avgLatency }}</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        id="btn-nav-translation"
        class="group relative rounded border border-[var(--color-outline-variant)] bg-gradient-to-b from-[var(--color-card-from)] to-[var(--color-card-to)] p-6 flex flex-col justify-between hover:border-[#00a67e]/60 transition-all duration-300"
      >
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded bg-[#00a67e]/10 border border-[#00a67e]/30 flex items-center justify-center">
              <Languages class="w-6 h-6 text-[#00a67e]" />
            </div>
            <span class="text-[10px] font-mono text-[var(--color-mono-text)] uppercase tracking-wider">多语调翻译器</span>
          </div>
          <h3 class="text-lg font-semibold text-ui">文本翻译空间</h3>
          <p class="text-xs text-ui-muted mt-1.5 leading-relaxed">
            支持 10 种目标语言与 5 种语调风格，提供高精度文本转换与术语一致性。
          </p>
        </div>
        <a-button block size="middle" class="block-btn action-btn mt-6" @click="goTo('translation')">
          <span>
            进入翻译面板
            <ArrowRight class="w-3.5 h-3.5 shrink-0" />
          </span>
        </a-button>
      </div>

      <div
        id="btn-nav-summarization"
        class="group relative rounded border border-[var(--color-outline-variant)] bg-gradient-to-b from-[var(--color-card-from)] to-[var(--color-card-to)] p-6 flex flex-col justify-between hover:border-[#00a67e]/60 transition-all duration-300"
      >
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center">
              <FileText class="w-6 h-6 text-sky-400" />
            </div>
            <span class="text-[10px] font-mono text-sky-400 uppercase tracking-wider">文档压缩总结</span>
          </div>
          <h3 class="text-lg font-semibold text-ui">智能要点总结</h3>
          <p class="text-xs text-ui-muted mt-1.5 leading-relaxed">
            将会议记录、研究笔记、长文档或代码注释压缩为结构化概述与要点列表。
          </p>
        </div>
        <a-button block size="middle" class="block-btn action-btn mt-6" @click="goTo('summarization')">
          <span>
            进入总结工作区
            <ArrowRight class="w-3.5 h-3.5 shrink-0" />
          </span>
        </a-button>
      </div>
    </div>

    <div class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] p-6 shadow-xl relative overflow-hidden">
      <div class="flex items-center gap-2 mb-4">
        <Sparkles class="w-4 h-4 text-[#00a67e]" />
        <h4 class="text-sm font-semibold text-ui font-display">智能输入控制台</h4>
      </div>

      <p class="text-xs text-ui-muted mb-4">
        输入文本后自动路由：含「总结 / 提炼 / 要点」或超过 250 字 → 总结页；否则 → 翻译页。跳转后会预填内容并清空上次结果。
      </p>

      <form @submit.prevent="handleQuickSend" class="space-y-4">
        <div class="relative">
          <textarea
            v-model="quickInput"
            placeholder="例如：将系统日志翻译成法语…或粘贴较长的会议纪要…"
            rows="3"
            class="w-full bg-[var(--color-surface-header)] border border-[var(--color-outline-variant)] focus:border-[#00a67e] rounded p-4 text-xs text-ui placeholder-[var(--color-placeholder)] outline-none resize-none transition-all duration-150 custom-scrollbar focus:ring-1 focus:ring-[#00a67e]"
            @keydown.enter.prevent="handleQuickSend"
          />
        </div>

        <div class="flex items-center justify-between">
          <span class="text-[10px] text-[var(--color-mono-text)]/55 font-mono">基于 GLM 的启发式自动路由</span>
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
