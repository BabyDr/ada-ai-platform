# AdaAgent · Linguist AI / AI TextFlow

面向 [AI Native 开发工程师笔试](docs/ai-navitve/ai-requirement.md) 的 AI 文本处理应用：在现有 **Linguist AI** 工作区上增量演进，提供多语言翻译、智能要点总结、SSE 流式输出与任务取消，并附带 Agent 对话、调用记录与 CLI/Agent 工具链。

> 详细方案见 [`docs/ai-navitve/plan.md`](docs/ai-navitve/plan.md) · 规范见 [`spec/`](spec/) · Agent 协作见 [`agent.md`](agent.md)

---

## 项目介绍

**AdaAgent** 是一个全栈 AI 文本处理平台，包含两条能力线：

| 模块 | 说明 |
|------|------|
| **文本处理主线** | 工作台 → 翻译 / 总结 → 流式结果 → 停止生成 → 历史记录 |
| **Agent Chat（加分）** | WebSocket 多轮对话，ReAct 步骤展示，与会话持久化 |

### 功能一览

- **工作台**：双卡片入口（文本翻译、智能要点总结）+ 快捷输入智能跳转
- **文本翻译**：10 种源/目标语言、5 种语调、双栏对照、SSE 打字机 + 停止生成
- **智能要点总结**：要点数 / 字数上限 / 语调、文件导入、概述 + 要点结构化展示
- **运行日志**：记录每次调用的输入、输出、耗时与状态
- **智能体对话**：GLM/Gemini/Mock Agent，WebSocket 流式回复
- **CLI + skill.md**：`ai-app translate` / `summarize` / `list`，供 Claude Code 等 Agent 调用

### CLI 演示

```bash
$ ai-app list
  translate            文本翻译 - 多语言翻译，支持源/目标语言与语调
  summarize            智能要点总结 - 长文本总结，支持要点数/字数上限/语调

$ ai-app translate --text "Hello world" --from en --to zh
# mock 模式下本地流式输出译文

$ ai-app summarize --text "长文本..." --max-points 3
# 流式输出 JSON 总结
```

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite | Composition API、useSSE / useTask |
| UI | Ant Design Vue + Tailwind CSS v4 | ConfigProvider 明暗主题 |
| 状态 | Pinia | `workspace`（跨页）+ `chat`（Agent） |
| 导航 | Vue Router 4 | `/dashboard` `/translation` `/summarization` 等 |
| 后端 | Python FastAPI + Uvicorn | Sidecar 端口 **18765** |
| LLM | 智谱 GLM / Gemini / Mock | `LLM_MODE=mock\|real`；密钥 `GLM_*` |
| 持久化 | SQLite + 内存日志 | Agent 会话 SQLite；翻译/总结日志内存 |
| CLI | Python Click + httpx | `cli/ai_app.py` |
| 测试 | pytest + vitest | `make test` 一键运行 |

### 仓库结构

```
AdaAgent/
├── frontend/src/
│   ├── components/          # DashboardView, TranslationView, SummarizationView, ...
│   ├── composables/         # useSSE.ts, useTask.ts, useChatStream.ts
│   ├── services/            # linguistApi.ts（SSE task）, api.ts（Chat REST）
│   ├── stores/              # workspace.ts, chat.ts
│   └── router/
├── backend/adaagent/
│   ├── main.py              # FastAPI 入口
│   ├── api/                 # functions, task, schemas
│   └── services/            # llm, prompt, task_manager
├── cli/                     # ai-app CLI
├── .claude/skills/skill.md  # Agent 技能描述
├── spec/                    # 需求、API、页面、任务拆分
├── agent.md                 # AI Agent 协作记录
└── scripts/sidecar.mjs
```

---

## 本地运行指南

### 环境要求

- **Node.js** ≥ 18
- **Python** ≥ 3.10

### 1. 安装

```bash
git clone <your-repo-url> AdaAgent
cd AdaAgent

npm install --registry https://registry.npmjs.org/
npm run sidecar:setup
```

### 2. 环境变量

```bash
cp backend/.env.example backend/.env
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MODE` | `mock` 本地流 / `real` 真实 GLM | `mock` |
| `GLM_API_KEY` | 智谱 API Key（与 Agent Chat 共用） | 空 |
| `GLM_MODEL` | GLM 模型 ID | `glm-4-flash` |
| `GLM_API_BASE` | OpenAI 兼容网关 | 智谱默认 |
| `GEMINI_API_KEY` | Gemini（GLM 未配置时 Chat 使用） | 空 |
| `TASK_TIMEOUT_SECONDS` | 单任务超时 | `60` |

### 3. 一键启动

```bash
npm run dev:all
```

| 服务 | 地址 |
|------|------|
| 前端 Web UI | http://localhost:1420 |
| 后端 Sidecar | http://127.0.0.1:18765 |
| 健康检查 | http://127.0.0.1:18765/api/health |

### 4. CLI

```bash
cd cli && pip install -e .
ai-app --help
ai-app translate --text "你好" --from zh --to en
```

### 5. 测试与构建

```bash
make test                    # 后端 pytest + CLI + 前端 vitest
npm run build --prefix frontend
cd backend && .venv/bin/pytest
npm run test --prefix frontend
```

---

## API 接口文档

完整规范见 [`spec/api-design.md`](spec/api-design.md)。

Base URL：`http://127.0.0.1:18765`

### GET /api/functions

```bash
curl http://127.0.0.1:18765/api/functions
```

### POST /api/task（SSE）

```bash
curl -N -X POST http://127.0.0.1:18765/api/task \
  -H "Content-Type: application/json" \
  -d '{"type":"translate","params":{"text":"你好","sourceLang":"zh","targetLang":"en","tone":"Professional"}}'
```

SSE 事件：`task_start` → `token`（多次）→ `task_done` / `task_error`

### DELETE /api/task/{taskId}

```bash
curl -X DELETE http://127.0.0.1:18765/api/task/{taskId}
```

### 辅助接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/logs` | 翻译/总结内存日志 |

### Agent Chat

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/sessions` | 会话 CRUD |
| POST | `/api/chat` | 发送消息 |
| WebSocket | `/ws/chat/{session_id}` | 流式 Agent 事件 |

> 旧的 `POST /api/translate`、`POST /api/summarize` 已移除，统一使用 SSE task 契约。

---

## Mock / Real 模式

```bash
# backend/.env
LLM_MODE=mock    # 零配置演示，本地预设逐字流
LLM_MODE=real    # 需 GLM_API_KEY
```

| 模式 | 需要 Key | 适用场景 |
|------|----------|----------|
| `mock` | 否 | 联调、CI、笔试演示 |
| `real` | 是 | 真实模型输出 |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [agent.md](agent.md) | AI Agent 角色与协作决策 |
| [spec/](spec/) | 需求、API、页面原型、任务拆分 |
| [.claude/skills/skill.md](.claude/skills/skill.md) | CLI Agent 技能 |
| [docs/ai-navitve/](docs/ai-navitve/) | 笔试需求与实现方案 |

---

## License

Private / 笔试作品 — 提交后可按题目要求删除仓库。
