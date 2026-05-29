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

export interface AppSettings {
  defaultTone: "Professional" | "Conversational" | "Technical" | "Academic" | "Creative";
  preferredModel: string;
}

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

export const TONE_STYLES = [
  { value: "Professional", label: "专业" },
  { value: "Conversational", label: "口语" },
  { value: "Technical", label: "技术" },
  { value: "Academic", label: "学术" },
  { value: "Creative", label: "创意" },
];

export const DEFAULT_GLM_MODEL = "glm-4-flash";

/** Workspace sidebar views (includes legacy agent chat) */
export type WorkspaceViewId =
  | "dashboard"
  | "translation"
  | "summarization"
  | "history"
  | "settings"
  | "chat";
