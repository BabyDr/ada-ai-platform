/**
 * Dashboard 指标：网关状态、已处理请求数、平均延迟。
 * 统计逻辑从 DashboardView 下沉，便于单测与复用。
 */
import { computed } from "vue";
import { useWorkspaceStore } from "../stores/workspace";

/** 从 workspace.logs 派生 Dashboard 顶部三枚指标卡数据。 */
export function useDashboardMetrics() {
  const workspace = useWorkspaceStore();

  const apiConnected = computed(() => workspace.apiConnected);
  const llmMode = computed(() => workspace.llmMode);

  /** 已完成（成功或失败）的请求总数。 */
  const totalProcessed = computed(
    () => workspace.logs.filter((l) => l.status === "success" || l.status === "failed").length,
  );

  /** 成功请求的平均 duration；无数据时返回演示默认值。 */
  const avgLatency = computed(() => {
    const successfulLogs = workspace.logs.filter((l) => l.status === "success");
    if (successfulLogs.length === 0) return "1.8s";

    const sum = successfulLogs.reduce((acc, curr) => {
      const val = parseFloat(curr.duration);
      return Number.isNaN(val) ? acc : acc + val;
    }, 0);
    return `${(sum / successfulLogs.length).toFixed(1)}s`;
  });

  return { apiConnected, llmMode, totalProcessed, avgLatency };
}
