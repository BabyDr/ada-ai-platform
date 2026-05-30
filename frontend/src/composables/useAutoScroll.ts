/**
 * 自动滚动 composable：监听响应式数据变化后，将容器滚动到底部。
 *
 * 节流策略：
 * - 使用 requestAnimationFrame 对齐屏幕刷新率（~60fps），高频更新只触发一次滚动。
 * - flush: 'post' 确保 DOM 已更新再计算 scrollHeight。
 */
import { watch, type Ref, onScopeDispose } from "vue";

export function useAutoScroll(container: Ref<HTMLElement | null>, trigger: Ref<unknown>) {
  let rafId = 0;

  const stop = watch(
    trigger,
    () => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        // 双 rAF：等 DOM 布局完成后再读 scrollHeight（流式文本追加后高度可能晚一帧更新）
        requestAnimationFrame(() => {
          const el = container.value;
          if (!el) return;
          el.scrollTop = el.scrollHeight;
        });
      });
    },
    { flush: "post" },
  );

  onScopeDispose(() => {
    cancelAnimationFrame(rafId);
    stop();
  });
}
