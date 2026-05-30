/**
 * 响应式断点：监听 viewport 是否处于移动端宽度（< md / 768px）。
 * 供 App 侧栏抽屉、Chat 会话列表等布局切换使用。
 */
import { onMounted, onUnmounted, ref } from "vue";

const MOBILE_QUERY = "(max-width: 767px)";

/** 返回 isMobile，随窗口 resize 更新。 */
export function useBreakpoint() {
  const isMobile = ref(
    typeof window !== "undefined" && window.matchMedia(MOBILE_QUERY).matches,
  );
  let mql: MediaQueryList | null = null;

  const sync = (): void => {
    isMobile.value = mql?.matches ?? false;
  };

  onMounted(() => {
    mql = window.matchMedia(MOBILE_QUERY);
    sync();
    mql.addEventListener("change", sync);
  });

  onUnmounted(() => {
    mql?.removeEventListener("change", sync);
  });

  return { isMobile };
}
