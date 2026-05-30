---
name: ai-textflow
description: AI text processing — translate between languages and summarize long text via Sidecar SSE API
---

# AI TextFlow CLI

Sidecar 提供的文本翻译与智能总结能力，可通过 `ai-app` 命令行工具调用。

## Prerequisites

- Sidecar 已启动：`npm run sidecar` 或 `npm run dev:all`（默认 `http://127.0.0.1:18765`）
- 可选：`cd cli && pip install -e .` 安装全局 `ai-app` 命令

## Commands

### list

列出可用功能（translate / summarize）。

```bash
ai-app list
```

### translate

多语言文本翻译（SSE 流式输出到终端）。

```bash
ai-app translate --text "你好世界" --from zh --to en
ai-app translate --text "Hello" --from en --to zh --tone Professional
```

参数：

| 选项 | 说明 |
|------|------|
| `--text` | 待翻译文本（必填） |
| `--from` | 源语言代码，如 `zh` / `en` / `ja` |
| `--to` | 目标语言代码 |
| `--tone` | 语调，默认 `Professional` |

### summarize

长文本要点总结（SSE 流式输出 JSON 结构）。

```bash
ai-app summarize --text "长文本内容..." --max-points 5
ai-app summarize --text "..." --max-points 3 --word-limit 200 --tone Technical
```

参数：

| 选项 | 说明 |
|------|------|
| `--text` | 待总结文本（必填） |
| `--max-points` | 要点数量，默认 3 |
| `--word-limit` | 概述字数上限，0 表示不限 |
| `--tone` | 语调，默认 `Professional` |

## API 契约（供 Agent 直接 HTTP 调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/functions` | 功能列表 |
| POST | `/api/task` | 提交任务，SSE 返回 `task_start` / `token` / `task_done` |
| DELETE | `/api/task/{taskId}` | 取消进行中的任务 |

POST body 示例：

```json
{"type": "translate", "params": {"text": "你好", "sourceLang": "zh", "targetLang": "en", "tone": "Professional"}}
```

```json
{"type": "summarize", "params": {"text": "...", "keyPointsCount": 5, "wordLimit": 250, "tone": "Professional"}}
```

## Environment

- `LLM_MODE=mock`（默认）：本地预设流式输出，无需 API Key
- `LLM_MODE=real`：需配置 `GLM_API_KEY` 或 `ZHIPU_API_KEY`
