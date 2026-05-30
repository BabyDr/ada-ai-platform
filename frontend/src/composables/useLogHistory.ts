/**
 * HistoryView 列表逻辑：筛选、展开、复制、总结 output 格式化。
 */
import { computed, ref } from "vue";
import type { LogEntry } from "../types";
import { useWorkspaceStore } from "../stores/workspace";
import { formatSummaryForClipboard, parseLogSummaryOutput } from "../utils/linguistFormat";

export type LogFilterType = "all" | "translation" | "summarization";

/** 运行日志页的筛选、展开与复制行为。 */
export function useLogHistory() {
  const workspace = useWorkspaceStore();
  const filterType = ref<LogFilterType>("all");
  const searchQuery = ref("");
  const expandedLogId = ref<string | null>(null);
  /** 最近一次复制成功的日志 id，用于按钮「已复制」反馈。 */
  const copiedLogId = ref<string | null>(null);

  const filterLabels: Record<LogFilterType, string> = {
    all: "全部",
    translation: "翻译",
    summarization: "总结",
  };

  const statusLabels: Record<LogEntry["status"], string> = {
    success: "成功",
    processing: "处理中",
    failed: "失败",
  };

  /** 按类型与关键词过滤日志列表。 */
  const filteredLogs = computed(() =>
    workspace.logs.filter((l) => {
      const matchesType = filterType.value === "all" || l.type === filterType.value;
      const query = searchQuery.value.trim().toLowerCase();
      const matchesSearch = !query
        ? true
        : l.input.toLowerCase().includes(query) ||
          l.output.toLowerCase().includes(query) ||
          (l.error && l.error.toLowerCase().includes(query));
      return matchesType && matchesSearch;
    }),
  );

  /** 切换单条日志的展开/收起状态。 */
  function toggleExpand(id: string): void {
    expandedLogId.value = expandedLogId.value === id ? null : id;
  }

  /** 复制日志 output；总结类 JSON 自动格式化为可读文本。 */
  async function handleCopyOutput(e: Event, id: string, content: string): Promise<void> {
    e.stopPropagation();
    let textToCopy = content;
    const parsed = parseLogSummaryOutput("summarization", content);
    if (parsed) {
      textToCopy = formatSummaryForClipboard(parsed.overview ?? "", parsed.keyPoints ?? []);
    }
    try {
      await navigator.clipboard.writeText(textToCopy);
      copiedLogId.value = id;
      setTimeout(() => {
        copiedLogId.value = null;
      }, 2500);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  }

  /** 将总结类日志 output 解析为结构化对象（模板展示用）。 */
  function formatLogOutput(log: LogEntry) {
    return parseLogSummaryOutput(log.type, log.output);
  }

  const canLoadMore = computed(() => workspace.logs.length < workspace.logsTotal);

  async function loadMoreLogs(): Promise<void> {
    await workspace.loadMoreLogs();
  }

  return {
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
  };
}
