# AdaAgent · Linguist AI / AI TextFlow

面向 [AI Native 开发工程师笔试](docs/ai-native/ai-requirement.md) 的 AI 文本处理应用，提供多语言翻译、智能要点总结、SSE 流式输出与任务取消，并附带 Agent 对话、调用记录与 CLI/Agent 工具链。

> 详细方案见 [`docs/ai-native/plan.md`](docs/ai-native/plan.md) · 规范见 [`docs/spec/`](docs/spec/) · 使用手册见 [`docs/manual.md`](docs/manual.md) · Agent 协作见 [`agent.md`](agent.md)

---

## 项目介绍

**AdaAgent** 是一个全栈 AI 文本处理平台，包含两条能力线：

| 模块 | 说明 |
|------|------|
| **文本处理主线** | 工作台 → 翻译 / 总结 → 流式结果 → 停止生成 → 历史记录 |
| **Agent Chat（加分）** | WebSocket 多轮对话，ReAct 步骤展示，与会话持久化（SQLite） |

### 功能一览

- **工作台**：双卡片入口（文本翻译、智能要点总结）+ 快捷输入智能跳转 + Mock 模式徽章
- **文本翻译**：10 种源/目标语言、5 种语调、双栏对照、SSE 打字机 + 停止生成
- **智能要点总结**：要点数 / 字数上限 / 语调、文件导入、概述 + 要点结构化展示
- **运行日志**：记录每次调用的输入、输出、耗时与状态（内存环形缓冲，分页查询）
- **智能体对话**：GLM/Gemini/Mock Agent，WebSocket 流式回复
- **CLI + SKILL.md**：`ai-app translate` / `summarize` / `list`，供 Claude Code 等 Agent 调用
- **工程加分**：明暗主题（Ant Design + `theme.css` 语义变量）、响应式布局、任务刷新恢复、16ms 流式渲染缓冲、统一错误处理与 Request ID

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
| 前端 | Vue 3 + TypeScript + Vite | Composition API、Vue Router 4 |
| UI | Ant Design Vue + Tailwind CSS v4 | `a-config-provider` + `theme.css` 语义色板 |
| 状态 | Pinia | `workspace`（跨页）+ `chat`（Agent） |
| 流式 | `useSSE` / `useTask` / `useStreamBuffer` | fetch SSE 解析、16ms 批量渲染、取消闭环 |
| 导航 | Vue Router 4 | `/dashboard` `/translation` `/summarization` 等 |
| 后端 | Python FastAPI + Uvicorn | Sidecar 端口 **18765** |
| LLM | 智谱 GLM / Gemini / Mock | `LLM_MODE=mock\|real`；密钥 `GLM_*` |
| 持久化 | SQLite + 内存日志 | Agent 会话 SQLite；翻译/总结日志内存（max 500 条） |
| CLI | Python Click + httpx | `cli/ai_app.py` |
| 测试 | pytest + vitest | `make test` 一键运行 |

### 仓库结构

```
AdaAgent/
├── frontend/src/
│   ├── components/          # DashboardView, TranslationView, SummarizationView, ...
│   ├── composables/         # useSSE, useTask, useStreamBuffer, useTaskRecovery, ...
│   ├── services/            # linguistApi.ts（SSE task）, api.ts（Chat REST）
│   ├── stores/              # workspace.ts, chat.ts
│   ├── router/              # 路由表 + 流式任务离开守卫
│   └── styles/theme.css     # 明/暗语义 CSS 变量
├── backend/adaagent/
│   ├── main.py              # FastAPI 入口
│   ├── api/                 # functions, task, schemas
│   └── services/            # llm, prompt, task_manager, task_sweeper
├── cli/                     # ai-app CLI
├── .claude/skills/SKILL.md  # Agent 技能描述
├── docs/
│   ├── architecture.md      # 模块架构说明（Backend/Frontend/CLI 结构与依赖）
│   ├── manual.md            # 系统使用手册
│   ├── spec/                # 规范契约：需求、API 设计、页面原型、开发标准、任务拆分
│   ├── ai-native/           # 笔试相关：原始需求、技术方案、实现任务、异常清单
│   └── verification/        # 手动验收截图（light/dark/mobile）+ 清单
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
# 或在仓库根目录：cp .env.example .env
```

**后端（Sidecar）**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MODE` | `mock` 本地流 / `real` 真实 GLM | `mock` |
| `GLM_API_KEY` | 智谱 API Key（与 Agent Chat 共用） | 空 |
| `GLM_MODEL` | GLM 模型 ID | `glm-4-flash` |
| `GLM_API_BASE` | OpenAI 兼容网关 | 智谱默认 |
| `GEMINI_API_KEY` | Gemini（GLM 未配置时 Chat 使用） | 空 |
| `TASK_TIMEOUT_SECONDS` | 单任务超时 | `60` |
| `MAX_CONCURRENT_TASKS` | 并发任务上限 | `3` |
| `MAX_LOGS` | 内存日志环形缓冲上限 | `500` |

**前端（Vite，见 `frontend/.env.development`）**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_BASE` | REST API 前缀 | `http://127.0.0.1:18765/api` |
| `VITE_WS_BASE` | WebSocket 前缀 | `ws://127.0.0.1:18765` |

> 开发时前端直连 Sidecar；若修改端口或部署分离，需同步调整 `VITE_API_BASE` / `VITE_WS_BASE`。

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

Sidecar 须先启动；默认连接 `http://127.0.0.1:18765`，可通过环境变量 `BASE_URL` 覆盖。

### 5. 测试与构建

```bash
make test                    # 后端 pytest + CLI + 前端 vitest
npm run build --prefix frontend
```

> 后端测试建议在 `LLM_MODE=mock` 且无 `GLM_API_KEY` 干扰的环境下运行，以确保 mock 链路断言稳定。

---

## API 接口文档

完整规范见 [`docs/spec/api-design.md`](docs/spec/api-design.md)。

Base URL：`http://127.0.0.1:18765`

### GET /api/functions

```bash
curl http://127.0.0.1:18765/api/functions
```

返回 `translate`、`summarize` 两项及参数 schema。

### POST /api/task（SSE）

```bash
curl -N -X POST http://127.0.0.1:18765/api/task \
  -H "Content-Type: application/json" \
  -d '{"type":"translate","params":{"text":"你好","sourceLang":"zh","targetLang":"en","tone":"Professional"}}'
```

SSE 事件：`task_start` → `token`（多次，含 `seq` 序号）→ `task_done` / `task_error`

**summarize 示例**

```bash
curl -N -X POST http://127.0.0.1:18765/api/task \
  -H "Content-Type: application/json" \
  -d '{"type":"summarize","params":{"text":"长文本…","keyPointsCount":3,"wordLimit":250,"tone":"Professional"}}'
```

### GET /api/task/{taskId}

查询任务状态（加分项：刷新恢复、轮询）。

```bash
curl http://127.0.0.1:18765/api/task/{taskId}
# {"taskId":"...","status":"pending|running|done|failed|cancelled"}
```

### DELETE /api/task/{taskId}

```bash
curl -X DELETE http://127.0.0.1:18765/api/task/{taskId}
```

### 辅助接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | `{ status, llm, keyLoaded }` |
| GET | `/api/logs?page=1&size=20` | 翻译/总结内存日志（分页） |

所有 HTTP 响应含 `X-Request-ID` 头，便于日志关联。

### Agent Chat

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/sessions` | 会话 CRUD |
| POST | `/api/chat` | 发送消息 |
| WebSocket | `/ws/chat/{session_id}` | 流式 Agent 事件 |

---

## Mock / Real 模式

```bash
# backend/.env 或根目录 .env
LLM_MODE=mock    # 零配置演示，本地预设逐字流
LLM_MODE=real    # 需 GLM_API_KEY
```

| 模式 | 需要 Key | 适用场景 |
|------|----------|----------|
| `mock` | 否 | 联调、CI、笔试演示 |
| `real` | 是 | 真实模型输出 |

工作台在 `mock` 模式下显示 **Mock 模式** 徽章；`/api/health` 返回当前 `llm` 模式与 `keyLoaded` 状态。

---

## Docker（可选）

```bash
docker compose up --build
curl -sf http://127.0.0.1:18765/api/functions
```

默认 `LLM_MODE=mock`，无需 API 密钥。当前 `docker-compose.yml` 仅打包 **Sidecar 后端**；前端开发仍用 `npm run dev` 连接 18765。

---

## 笔试交付物对照

| 交付物 | 路径 | 状态 |
|--------|------|------|
| 项目源码 | 本仓库 | ✅ |
| README（介绍 / 技术栈 / 运行 / API） | `README.md` | ✅ |
| CLI 工具 | `cli/ai_app.py` | ✅ |
| SKILL.md | `.claude/skills/SKILL.md` | ✅ |
| Agent 调用截图 | `docs/verification/agent-skill-invoke.png` | ✅ |
| agent.md | `agent.md` | ✅ |
| spec/ 规范目录 | `docs/spec/` | ✅ |
| 系统使用手册 | `docs/manual.md` | ✅ |
| 手动验收截图 | `docs/verification/`（light/dark/mobile） | ✅ |
| Docker | `Dockerfile` + `docker-compose.yml` | ✅（后端） |
| 异常场景清单 | `docs/ai-native/exception-checklist.md` | ✅ |

详见 [`docs/verification/README.md`](docs/verification/README.md)。

---

## 相关文档

**快速理解项目**（推荐阅读顺序）：

| 顺序 | 文档 | 说明 |
|------|------|------|
| 1 | [docs/architecture.md](docs/architecture.md) | **模块架构说明**（Backend/Frontend/CLI 结构与依赖） |
| 2 | 本文件 README.md | 项目介绍、运行指南、API 文档 |
| 3 | [docs/manual.md](docs/manual.md) | 系统使用手册 |

**规范与实现**：

| 文档 | 说明 |
|------|------|
| [docs/spec/](docs/spec/) | 需求、API 契约、页面原型、开发规范 |
| [docs/ai-native/ai-requirement.md](docs/ai-native/ai-requirement.md) | 笔试原始需求 |
| [docs/ai-native/exception-checklist.md](docs/ai-native/exception-checklist.md) | 异常场景评估与验收（57 条） |

**Agent 与交付**：

| 文档 | 说明 |
|------|------|
| [agent.md](agent.md) | AI Agent 角色与协作决策 |
| [.claude/skills/SKILL.md](.claude/skills/SKILL.md) | CLI Agent 技能描述 |
| [docs/verification/](docs/verification/) | 手动验收清单与截图 |

---

## License

© 2026 RenXiaodi. All rights reserved.

本仓库为 AI Native 开发工程师笔试作品，仅供招聘方评估候选人能力使用。
未经作者书面许可，禁止复制、修改、分发或用于任何商业目的。
