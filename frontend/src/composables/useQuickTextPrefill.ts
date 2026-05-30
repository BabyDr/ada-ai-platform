/**
 * 工作台快捷输入预填：Dashboard 写入 quickText 后，目标页消费一次并清空。
 */
import { watch, type Ref } from "vue";
import { useWorkspaceStore } from "../stores/workspace";

/** 监听 workspace.quickText，有值时写入 target 并立即清空 store。 */
export function useQuickTextPrefill(target: Ref<string>): void {
  const workspace = useWorkspaceStore();

  watch(
    () => workspace.quickText,
    (newVal) => {
      if (newVal) {
        target.value = newVal;
        workspace.setQuickText("");
      }
    },
    { immediate: true },
  );
}
