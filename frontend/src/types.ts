/**
 * Linguist 工作台共享类型与常量（语言列表、语调、日志结构、默认模型）。
 */

/** 单条 API 运行日志（翻译/总结任务） */
export interface LogEntry {
  id: string;
  timestamp: string;
  date: string;
  type: "translation" | "summarization";
  input: string;
  output: string;
  duration: string;
  status: "success" | "processing" | "failed";
  error?: string;
  details?: {
    sourceLang?: string;
    targetLang?: string;
    keyPointsCount?: number;
    wordLimit?: number;
    tone?: string;
  };
}

/** 翻译源/目标语言选项（code 供 API，name 供 UI） */
export const SUPPORTED_LANGUAGES = [
  { code: "auto", name: "自动检测" },
  { code: "en", name: "英语" },
  { code: "zh", name: "简体中文" },
  { code: "es", name: "西班牙语" },
  { code: "fr", name: "法语" },
  { code: "ja", name: "日语" },
  { code: "de", name: "德语" },
  { code: "ko", name: "韩语" },
  { code: "ru", name: "俄语" },
  { code: "it", name: "意大利语" },
];

/** 译文/摘要语调风格选项 */
export const TONE_STYLES = [
  { value: "Professional", label: "专业" },
  { value: "Conversational", label: "口语" },
  { value: "Technical", label: "技术" },
  { value: "Academic", label: "学术" },
  { value: "Creative", label: "创意" },
];

/** 默认 GLM 模型 id（与 backend DEFAULT_GLM_MODEL 一致） */
export const DEFAULT_GLM_MODEL = "glm-4-flash";
