/**
 * 将 Pinia 明暗状态同步到 document.documentElement[data-theme]，
 * 供 theme.css 语义变量切换；深色 token 仅在 dark 块内定义，不受影响。
 */
import { watch } from "vue";
import type { Ref } from "vue";

export function useThemeAttribute(isDark: Ref<boolean>): void {
  const apply = (dark: boolean) => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  };

  apply(isDark.value);
  watch(isDark, apply);
}
