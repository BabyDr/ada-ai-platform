<script setup lang="ts">
/**
 * API 运行历史日志页：纯 UI 展示，筛选/复制/格式化逻辑见 useLogHistory。
 */
import {
  Search,
  Trash2,
  ChevronDown,
  ChevronUp,
  Languages,
  FileText,
  Clock,
  AlertTriangle,
  Check,
  Copy,
  Terminal,
  Database,
} from "lucide-vue-next";
import { useLogHistory } from "../composables/useLogHistory";
import TruncatedText from "./shared/TruncatedText.vue";

const {
  workspace,
  filterType,
  filterLabels,
  statusLabels,
  searchQuery,
  expandedLogId,
  copiedLogId,
  filteredLogs,
  toggleExpand,
  handleCopyOutput,
  formatLogOutput,
  canLoadMore,
  loadMoreLogs,
} = useLogHistory();
</script>

<template>
  <div class="space-y-6 p-8 max-w-6xl mx-auto" id="history-logs-view">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#26384d]/40 pb-5">
      <div>
        <h2 class="font-display text-2xl font-bold text-white flex items-center gap-2">
          <Terminal class="w-6 h-6 text-[#00a67e]" />
          API 运行历史日志
        </h2>
        <p class="text-xs text-[#acb5c9] mt-1">查看请求参数、响应延迟与模型输出，数据由服务端记录。</p>
      </div>

      <a-button
        v-if="workspace.logs.length > 0"
        type="primary"
        danger
        size="small"
        class="ml-auto md:ml-0 action-btn shrink-0"
        @click="workspace.clearHistory()"
      >
        <template #icon><Trash2 class="w-3.5 h-3.5" /></template>
        清空日志
      </a-button>
    </div>

    <div class="flex flex-col md:flex-row md:items-center gap-4 bg-[#08121e]/40 border border-[#26384d]/60 rounded p-4">
      <div class="relative flex-1">
        <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none text-[#bccac2]/45">
          <Search class="w-4 h-4" />
        </span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="按关键词筛选输入或响应内容…"
          class="w-full bg-[#122131] border border-[#26384d]/60 focus:border-[#00a67e] rounded pl-9 pr-4 py-2 text-xs text-white placeholder-[#bccac2]/35 outline-none transition-colors"
        />
      </div>

      <a-radio-group v-model:value="filterType" size="small" button-style="solid" class="filter-radio-group shrink-0">
        <a-radio-button v-for="type in (['all', 'translation', 'summarization'] as const)" :key="type" :value="type">
          {{ filterLabels[type] }}
        </a-radio-button>
      </a-radio-group>
    </div>

    <div v-if="filteredLogs.length > 0" class="space-y-3.5">
      <div
        v-for="log in filteredLogs"
        :key="log.id"
        @click="toggleExpand(log.id)"
        class="rounded border border-[#26384d] bg-[#0c1622] hover:border-[#00a67e]/40 transition-all duration-150 cursor-pointer overflow-hidden"
      >
        <div class="p-4 flex items-center justify-between gap-4 select-none">
          <div class="flex items-center gap-3">
            <div
              :class="[
                'p-2.5 rounded shrink-0 border',
                log.type === 'translation'
                  ? 'bg-[#00a67e]/10 text-[#00a67e] border-[#00a67e]/15'
                  : 'bg-sky-500/10 text-sky-400 border-sky-500/15',
              ]"
            >
              <Languages v-if="log.type === 'translation'" class="w-4 h-4" />
              <FileText v-else class="w-4 h-4" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-white">
                  {{ log.type === "translation" ? "文本翻译" : "智能总结" }}
                </span>
                <span class="text-[9px] font-mono bg-[#162537] border border-[#26384d]/60 text-[#bccac2] px-1.5 py-0.5 rounded">
                  {{ log.date }} - {{ log.timestamp }}
                </span>
              </div>
              <p class="text-[11px] text-[#acb5c9] mt-0.5 font-sans leading-tight line-clamp-1 max-w-xl">{{ log.input }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1 font-mono text-[10px] text-[#bccac2] bg-[#162537] border border-[#26384d]/60 px-1.5 py-0.5 rounded">
              <Clock class="w-3 h-3 text-[#00a67e]" />
              <span>{{ log.duration }}</span>
            </div>
            <span
              :class="[
                'px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide border',
                log.status === 'success'
                  ? 'bg-[#00a67e]/10 text-[#00a67e] border-[#00a67e]/20'
                  : log.status === 'processing'
                    ? 'bg-amber-500/10 text-amber-500 border-amber-500/25 animate-pulse'
                    : 'bg-red-500/10 text-red-400 border-red-500/20',
              ]"
            >
              {{ statusLabels[log.status] }}
            </span>
            <component :is="expandedLogId === log.id ? ChevronUp : ChevronDown" class="w-4 h-4 text-[#bccac2] shrink-0" />
          </div>
        </div>

        <div v-if="expandedLogId === log.id" class="px-5 pb-5 pt-2 border-t border-[#26384d]/60 bg-[#08121e]/30 space-y-4">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 py-3 border-b border-[#26384d]/40">
            <div v-if="log.type === 'translation' && log.details?.sourceLang" class="space-y-0.5">
              <span class="block text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider">源语言</span>
              <span class="text-xs font-semibold text-white">{{ log.details.sourceLang }}</span>
            </div>
            <div v-if="log.type === 'translation' && log.details?.targetLang" class="space-y-0.5">
              <span class="block text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider">目标语言</span>
              <span class="text-xs font-semibold text-white">{{ log.details.targetLang }}</span>
            </div>
            <div v-if="log.details?.tone" class="space-y-0.5">
              <span class="block text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider">语调</span>
              <span class="text-xs font-semibold text-white">{{ log.details.tone }}</span>
            </div>
            <div v-if="log.type === 'summarization' && log.details?.keyPointsCount" class="space-y-0.5">
              <span class="block text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider">要点数量</span>
              <span class="text-xs font-semibold text-white font-mono">{{ log.details.keyPointsCount }} 条</span>
            </div>
          </div>

          <div>
            <span class="block text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider mb-1.5">原始输入</span>
            <div class="p-3.5 rounded bg-[#0c1622] border border-[#26384d] text-xs text-white leading-relaxed select-text">
              <TruncatedText :text="log.input" :limit="5000" />
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[9px] font-mono text-[#acb5c9] uppercase tracking-wider">模型响应</span>
              <a-button
                v-if="log.status === 'success'"
                type="default"
                size="small"
                class="action-btn !text-[10px]"
                @click="handleCopyOutput($event, log.id, log.output)"
              >
                <template #icon>
                  <Check v-if="copiedLogId === log.id" class="w-3 h-3 text-[#00a67e]" />
                  <Copy v-else class="w-3 h-3" />
                </template>
                {{ copiedLogId === log.id ? "已复制" : "复制响应" }}
              </a-button>
            </div>

            <div
              v-if="log.status === 'failed'"
              class="p-4 rounded border border-red-500/25 bg-red-500/5 text-red-400 text-xs flex items-start gap-2.5"
            >
              <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
              <span>{{ log.error || "服务端处理出错。" }}</span>
            </div>

            <div
              v-else-if="log.status === 'processing'"
              class="p-4 rounded border border-amber-500/25 bg-amber-500/5 text-amber-500 text-xs flex items-center gap-2"
            >
              <span class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-t-transparent border-amber-500"></span>
              <span>等待服务端响应…</span>
            </div>

            <div v-else>
              <template v-if="log.type === 'summarization' && formatLogOutput(log)">
                <div class="space-y-4 p-4 rounded bg-[#0c1622] border border-[#26384d] select-text">
                  <div v-if="formatLogOutput(log)?.overview">
                    <span class="block text-[8px] font-mono text-[#00a67e] uppercase tracking-widest font-bold mb-1">概述</span>
                    <p class="text-xs text-[#bccac2] leading-relaxed">{{ formatLogOutput(log)?.overview }}</p>
                  </div>
                  <div v-if="formatLogOutput(log)?.keyPoints?.length">
                    <ul class="space-y-1.5 text-xs text-white">
                      <li
                        v-for="(point, idx) in formatLogOutput(log)?.keyPoints"
                        :key="idx"
                        class="flex gap-2.5 items-start bg-[#08121e] border border-[#26384d]/40 rounded p-2.5"
                      >
                        <span class="text-[#00a67e] font-mono font-bold">{{ idx + 1 }}.</span>
                        <span>{{ point }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </template>
              <div v-else class="p-4 rounded bg-[#0c1622] border border-[#26384d] text-xs text-white leading-relaxed select-text">
                <TruncatedText :text="log.output" :limit="8000" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="canLoadMore" class="flex justify-center pt-2">
        <a-button type="default" size="small" class="action-btn" :loading="workspace.logsLoading" @click="loadMoreLogs">
          加载更多
        </a-button>
      </div>
    </div>

    <div v-else class="text-center p-12 rounded border border-dashed border-[#26384d] bg-[#0c1622]/40">
      <Database class="w-12 h-12 text-[#bccac2]/25 mx-auto mb-3" />
      <span class="block text-sm font-semibold text-white">暂无运行日志</span>
      <p class="text-xs text-[#acb5c9] max-w-sm mx-auto mt-1">完成翻译或总结任务后，相关记录将显示在这里。</p>
    </div>
  </div>
</template>
