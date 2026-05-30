/**
 * 工作台快捷输入预填：Dashboard 写入 quickText 后，目标页消费一次并清空。
 */
import { watch, type Ref } from "vue";
import { useWorkspaceStore } from "../stores/workspace";

/** 监听 workspace.quickText，有值时先重置输出、再写入 target 并清空 store。 */
export function useQuickTextPrefill(target: Ref<string>, onPrefill?: () => void): void {
  const workspace = useWorkspaceStore();

  watch(
    () => workspace.quickText,
    (newVal) => {
      if (!newVal) return;
      onPrefill?.();
      target.value = newVal;
      workspace.setQuickText("");
    },
    { immediate: true },
  );
}
