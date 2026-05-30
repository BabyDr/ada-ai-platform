/**
 * 导出类 UI 动作：剪贴板复制反馈、文本下载。
 * TranslationView / SummarizationView / HistoryView 共用，避免各文件重复实现。
 */
import { ref } from "vue";

/** 复制文本到剪贴板，并维护「已复制」反馈状态。 */
export function useCopyFeedback(resetMs = 2000) {
  const copied = ref(false);

  /** 写入剪贴板；空内容或失败时返回 false。 */
  async function copyText(text: string): Promise<boolean> {
    if (!text.trim()) return false;
    try {
      await navigator.clipboard.writeText(text);
      copied.value = true;
      setTimeout(() => {
        copied.value = false;
      }, resetMs);
      return true;
    } catch (err) {
      console.error("Failed to copy text", err);
      return false;
    }
  }

  return { copied, copyText };
}

/** 触发浏览器下载纯文本 Blob（调用后自动清理 DOM 节点）。 */
export function downloadTextFile(content: string, filename: string): void {
  if (!content.trim()) return;
  const element = document.createElement("a");
  const file = new Blob([content], { type: "text/plain;charset=utf-8" });
  element.href = URL.createObjectURL(file);
  element.download = filename;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}
