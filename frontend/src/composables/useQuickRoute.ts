/**
 * Dashboard 智能输入控制台：启发式判断翻译 vs 总结并路由跳转。
 */
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useWorkspaceStore } from "../stores/workspace";

export type QuickRouteTarget = "translation" | "summarization";

/** 根据关键词与文本长度判断应跳转的功能页。 */
export function detectQuickRouteTarget(text: string): QuickRouteTarget {
  const lowercaseInput = text.toLowerCase();
  const isProbablySummary =
    lowercaseInput.includes("summary") ||
    lowercaseInput.includes("summarize") ||
    lowercaseInput.includes("总结") ||
    lowercaseInput.includes("提炼") ||
    lowercaseInput.includes("要点") ||
    text.length > 250;

  return isProbablySummary ? "summarization" : "translation";
}

/** Dashboard 快捷输入：预填 quickText 并路由到对应功能页。 */
export function useQuickRoute() {
  const router = useRouter();
  const workspace = useWorkspaceStore();
  const quickInput = ref("");

  /** 路由到 translation 或 summarization 页面。 */
  function goTo(name: QuickRouteTarget): void {
    router.push({ name });
  }

  /** 提交快捷输入：写入 store 并跳转。 */
  function handleQuickSend(): void {
    if (!quickInput.value.trim()) return;

    const text = quickInput.value.trim();
    workspace.setQuickText(text);
    router.push({ name: detectQuickRouteTarget(text) });
    quickInput.value = "";
  }

  return { quickInput, goTo, handleQuickSend };
}
