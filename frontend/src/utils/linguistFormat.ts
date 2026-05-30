/**
 * Linguist 工作台文本格式化工具（翻译/总结/历史日志共用）。
 */

export interface ParsedSummary {
  overview?: string;
  keyPoints?: string[];
}

/** 尝试将总结类 output（JSON 字符串）解析为结构化对象；失败返回 null。 */
export function parseSummaryOutput(output: string): ParsedSummary | null {
  try {
    const parsed = JSON.parse(output) as ParsedSummary;
    if (parsed.overview || (parsed.keyPoints && parsed.keyPoints.length > 0)) {
      return parsed;
    }
  } catch {
    /* 非 JSON，按纯文本处理 */
  }
  return null;
}

/** 组装总结内容为剪贴板文本（编号要点列表）。 */
export function formatSummaryForClipboard(overview: string, keyPoints: string[]): string {
  let text = "";
  if (overview) text += `概述：\n${overview}\n\n`;
  if (keyPoints.length > 0) {
    text += `核心要点：\n${keyPoints.map((kp, idx) => `${idx + 1}. ${kp}`).join("\n")}`;
  }
  return text;
}

/** 组装总结内容为下载文件文本（Markdown 风格要点）。 */
export function formatSummaryForDownload(overview: string, keyPoints: string[]): string {
  let content = "";
  if (overview) content += `概述：\n${overview}\n\n`;
  if (keyPoints.length > 0) {
    content += `核心要点：\n${keyPoints.map((kp) => `- ${kp}`).join("\n")}`;
  }
  return content;
}

/** 将日志 output 转为可展示的总结结构（HistoryView 专用）。 */
export function parseLogSummaryOutput(logType: string, output: string): ParsedSummary | null {
  if (logType !== "summarization") return null;
  return parseSummaryOutput(output);
}
