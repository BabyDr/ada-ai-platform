/**
 * Vue Router 导航守卫：Linguist 流式生成中离开页面前确认并终止任务（#35 / #30）。
 */
import type { Router } from "vue-router";
import { cancelTaskKeepalive } from "../services/linguistApi";
import { useWorkspaceStore } from "../stores/workspace";

const LINGUIST_ROUTE_NAMES = new Set(["translation", "summarization"]);

export function setupStreamingGuard(router: Router): void {
  /**
   * 全局 beforeEach 守卫：
   * 1. 仅拦截从翻译/总结页离开的导航；
   * 2. 若 Linguist 任务正在流式执行，弹出确认对话框；
   * 3. 用户确认后调用 cancelLinguistTask 终止任务并放行；取消则阻止导航。
   */
  router.beforeEach(async (_to, from, next) => {
    const fromName = from.name;
    if (typeof fromName !== "string" || !LINGUIST_ROUTE_NAMES.has(fromName)) {
      next();
      return;
    }

    const workspace = useWorkspaceStore();
    if (!workspace.linguistStreaming) {
      next();
      return;
    }

    const leave = window.confirm("任务仍在执行，是否离开？离开将终止任务。");
    if (!leave) {
      next(false);
      return;
    }

    await workspace.cancelLinguistTask();
    next();
  });
}

/** 浏览器关闭/刷新：提示 + keepalive 取消任务（#30） */
export function setupBeforeUnloadGuard(): void {
  window.addEventListener("beforeunload", (e) => {
    const workspace = useWorkspaceStore();
    if (!workspace.linguistStreaming) return;

    if (workspace.activeTaskId) {
      cancelTaskKeepalive(workspace.activeTaskId);
    }
    e.preventDefault();
    e.returnValue = "";
  });
}
