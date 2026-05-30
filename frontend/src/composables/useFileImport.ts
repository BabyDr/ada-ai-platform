/**
 * 文本文件导入：点击选择 + 拖拽上传（.txt / .md）。
 * SummarizationView 专用，逻辑与 UI 事件处理集中在此。
 */
import { ref } from "vue";

const ACCEPTED_EXTENSIONS = [".txt", ".md"];

/** 校验是否为可导入的纯文本文件。 */
function isAcceptedTextFile(file: File): boolean {
  return file.type === "text/plain" || ACCEPTED_EXTENSIONS.some((ext) => file.name.endsWith(ext));
}

/** 读取 File 为 UTF-8 字符串并通过回调返回。 */
function readTextFile(file: File, onLoad: (text: string) => void): void {
  const reader = new FileReader();
  reader.onload = (e) => {
    if (e.target && typeof e.target.result === "string") {
      onLoad(e.target.result);
    }
  };
  reader.readAsText(file);
}

/**
 * 文件导入 composable：维护拖拽高亮与 hidden input 引用。
 * @param onTextLoaded 文件读取成功后的回调（通常写入 inputText ref）
 */
export function useFileImport(onTextLoaded: (text: string) => void) {
  const dragActive = ref(false);
  const fileInputRef = ref<HTMLInputElement | null>(null);

  /** 触发隐藏的 file input 点击。 */
  function triggerFileSelect(): void {
    fileInputRef.value?.click();
  }

  /** 处理 `<input type="file">` 的 change 事件。 */
  function handleFileChoose(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (target.files?.[0]) loadFile(target.files[0]);
  }

  /** 拖拽悬停：阻止默认行为并高亮投放区。 */
  function handleDragOver(e: DragEvent): void {
    e.preventDefault();
    dragActive.value = true;
  }

  /** 拖拽离开：取消高亮。 */
  function handleDragLeave(e: DragEvent): void {
    e.preventDefault();
    dragActive.value = false;
  }

  /** 拖放文件：读取第一个合法文件。 */
  function handleDrop(e: DragEvent): void {
    e.preventDefault();
    dragActive.value = false;
    if (e.dataTransfer?.files?.[0]) loadFile(e.dataTransfer.files[0]);
  }

  /** 校验类型并读取文件内容。 */
  function loadFile(file: File): void {
    if (!isAcceptedTextFile(file)) {
      alert("不支持的文件类型，仅接受 .txt 与 .md 文档。");
      return;
    }
    readTextFile(file, onTextLoaded);
  }

  return {
    dragActive,
    fileInputRef,
    triggerFileSelect,
    handleFileChoose,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  };
}
