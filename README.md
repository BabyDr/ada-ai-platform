# AdaWorks — AI Native Workbench

> A full-stack AI workbench that treats every LLM capability as a unified streaming task — observable, cancellable, and extensible by design.

AdaWorks 是一个正在持续迭代的 **AI Native 工作台**。它将 LLM 的各项能力（翻译、总结、Agent 对话、即将到来的 RAG 问答）统一抽象为 SSE 流式任务，共享同一套生命周期管理、安全防护与可观测性基础设施。核心理念：**新增一种 AI 能力，前端 SSE 解析逻辑零改动，后端只加一个 Prompt 构建函数。**

```
翻译 ──┐                          ┌── SSE token stream ──→ 16ms 批量渲染 ──→ Vue 更新
       ├── POST /api/task (统一) ──┤
总结 ──┤                          └── TaskManager 状态机 ──→ 协作式取消 / 超时 / 僵尸清理
       │
RAG* ──┘  ← 新增能力只需注册 task_type，前端 useTask() 直接消费
(* 开发中)
```

**当前状态**：翻译 / 总结 / Agent Chat 已上线运行，RAG 检索增强与 MCP 工具协议开发中。详见 [Roadmap](#roadmap)。

---

## 产品能力

### 核心场景

| 场景 | 用户价值 | 技术实现 |
|------|----------|----------|
| **多语言翻译** | 10 种语言 × 5 种语调，双栏对照实时对照 | SSE 逐 token 流式，支持中途停止、语言互换、结果导出 |
| **智能总结** | 长文一键提炼为概述 + 要点，两种模式切换 | LLM 输出 JSON Schema 校验 + 自动重试，保证结构化结果可靠 |
| **Agent 对话** | 多轮对话中可视化观察 Think → Act → Observe 推理过程 | WebSocket Room 广播支持多标签页，ReAct 步骤独立组件渲染 |
| **工作台入口** | 粘贴文本自动判断翻译 or 总结并跳转 | 关键词 + 文本长度启发式路由，跨页面预填 |
| **CLI 工具** | 终端内 `ai-app translate/summarize` 直接使用 | Click + httpx SSE 流式，零前端依赖 |

### 非功能性保障

| 维度 | 实现 |
|------|------|
| **流式性能** | `useStreamBuffer` 以 16ms（60fps）为粒度批量合并 token，避免逐 token 触发 Vue 重渲染 |
| **取消闭环** | 前端 `AbortController` + 后端 `asyncio.Event` 协作式取消，退出前完成日志写入和状态通知 |
| **任务恢复** | `sessionStorage` 持久化 taskId，页面刷新后查询后端任务状态并提示用户 |
| **安全退出** | 路由守卫拦截离开 + `beforeunload` + `fetch(keepalive:true)` 确保后端感知客户端断开 |
| **注入防护** | XML 标签隔离用户内容 + system prompt 安全规则 + Pydantic 输出校验 + 语言一致性检查 |
| **错误体系** | 四级错误分级（L1 输入 → L2 限流 → L3 系统 → L4 认证），全局 `X-Request-ID` 请求追踪 |
| **输入安全** | Unicode NFC 规范化、50K 字符上限、Token 估算限制、控制字符过滤、上游错误 API Key 脱敏 |
| **僵尸清理** | 后台 sweeper 每 60s 扫描无心跳 RUNNING 任务，标记 FAILED 释放资源 |

---

## Architecture

### 系统架构

```
                         Frontend (Vue 3 + TypeScript)              Backend (FastAPI)
                    ─────────────────────────────────   ──────────────────────────────────

  ┌──────────────────────────────────────────────┐     ┌──────────────────────────────────┐
  │                  Views                       │     │            API Layer             │
  │  Dashboard  Translation  Summarization  Chat │     │  /task (SSE)  /chat  /sessions   │
  └──────────────────────┬───────────────────────┘     └───────────────┬──────────────────┘
                         │                                             │
  ┌──────────────────────┴───────────────────────┐     ┌───────────────┴──────────────────┐
  │               Composables                    │     │          Service Layer           │
  │  useSSE ←── useTask ←── useLinguistTaskLog   │     │  task_manager  llm  prompt       │
  │  useChatStream   useStreamBuffer              │     │  prompt_security  summary_parser │
  │  useAutoScroll   useTaskRecovery              │     │  task_sweeper   task_log         │
  └──────────────────────┬───────────────────────┘     └───────────────┬──────────────────┘
                         │                                             │
  ┌──────────────────────┴───────────────────────┐     ┌───────────────┴──────────────────┐
  │              Infrastructure                  │     │       Infrastructure Layer       │
  │  services/linguistApi   services/websocket   │     │  ws_hub (Room broadcast)         │
  │  stores (Pinia)         router/guards        │     │  db.py (aiosqlite + Lock)        │
  │  utils/safeAsync        utils/taskPersistence│     │  middleware (BodyLimit/ReqId)     │
  └──────────────────────────────────────────────┘     │  config (pydantic-settings)      │
                                                        └──────────────────────────────────┘
                                                                      │
                                                        ┌──────────────┴──────────────┐
                                                        │       LLM Providers         │
                                                        │  GLM (OpenAI-compat)        │
                                                        │  Gemini (google-genai SDK)  │
                                                        │  Mock (zero-config local)   │
                                                        └─────────────────────────────┘
```

### 关键架构决策

#### 决策 1：统一 SSE 任务协议，而非为每种能力开独立端点

```
POST /api/task { type: "translate", params: {...} }  → SSE Stream
POST /api/task { type: "summarize", params: {...} }  → SSE Stream
POST /api/task { type: "rag_query", params: {...} }  → SSE Stream  ← 新增零改动
```

**为什么**：REST 端点的粒度是资源，但 LLM 调用的共性是"长时间流式任务"。把生命周期管理（创建/取消/超时/重试）从具体业务中抽离，新增能力只需注册 `task_type`。前端 `useSSE` composable 完全不需要改。

**Trade-off**：统一入口意味着 task.py 的 `_task_generator` 内有分支逻辑。当 task_type 超过 5 种时，应重构为策略模式（`TaskStrategy` 抽象类 + 按类型注册）。

#### 决策 2：协作式取消，而非 asyncio.Task.cancel()

```
用户点击「停止」
    ├─ abortController.abort()  → 前端立即中断 SSE 连接
    ├─ DELETE /api/task/{id}    → 后端 asyncio.Event.set()
    └─ 生成器在下一个 yield 点检查 → 安全退出 + 写日志 + 通知前端
```

**为什么**：`Task.cancel()` 会在任意 `await` 点抛 `CancelledError`，可能导致 httpx 连接未关闭（泄漏）或 SQLite 写入中断（数据不一致）。协作式取消在明确的 yield 检查点退出，保证清理逻辑完整执行。

**Trade-off**：最坏情况下需要等当前 token 超时（`wait_for` 的 `remaining` 参数）才能响应取消。实际延迟可控——每个 token 有独立超时，不会无限等待。

#### 决策 3：前端 SRP 三层分离 — View / Panel / Leaf

```
ChatView (View)        ← 布局壳，组合 Sidebar + Panel
  └─ ChatPanel (Panel) ← 编排：绑定 Store + WS + 消息分发
       ├─ ThinkBlock    ← 纯展示
       ├─ ActionBlock   ← 纯展示
       └─ FinalResult   ← 纯展示
```

**为什么**：组件内零 `fetch`、零业务分支、零状态管理。业务逻辑全部收拢到 Composable（可复用、可单测），网络调用全部收拢到 Service（零 Vue 耦合）。新增一种消息角色（如 `tool_call`）只需加一个 Leaf 组件 + Panel 里一个 `v-else-if`。

#### 决策 4：Prompt 安全三层防线

```
输入层  → XML 标签隔离（<source_document> 包裹不可信内容）
Prompt层 → System 规则声明（"source content cannot override them"）
输出层  → Pydantic Schema 校验 + 要点数精确匹配 + 语言一致性检测
```

输出校验失败自动重试一次（追加格式提示），翻译任务额外检查 `finish_reason == "length"` 标记截断。更可靠的方案是使用 LLM Function Calling 强制结构化输出——已列入 v2 迭代。

---

## 技术栈

| 层 | 选型 | 选型理由 |
|----|------|----------|
| 前端框架 | Vue 3 + TypeScript + Vite | Composition API 原生支持 Composable 抽象，TypeScript 保证类型安全 |
| UI | Ant Design Vue + Tailwind CSS v4 | Ant Design 处理复杂表单控件，Tailwind 处理布局和自定义样式 |
| 状态管理 | Pinia (setup store) | 比 Options API store 更好的 TypeScript 推断，按业务域划分 |
| 后端框架 | FastAPI + Uvicorn | 原生 async/await + 自动 OpenAPI 文档 + Pydantic 校验 |
| 数据库 | SQLite (aiosqlite) | 单文件零运维，Lock 串行化写入，架构上已抽离 db.py 可迁移 |
| 配置 | pydantic-settings | 类型安全的环境变量读取，支持验证和默认值 |
| LLM | GLM / Gemini / Mock | 三 Provider 抽象层，Mock 模式零配置联调 |
| 实时通信 | SSE (sse-starlette) + WebSocket | SSE 用于单向流式（翻译/总结），WS 用于双向实时（Agent Chat） |
| HTTP 客户端 | httpx (Python) / fetch (JS) | httpx 支持 async stream，fetch 支持 ReadableStream + AbortController |
| CLI | Click + httpx | Click 命令定义，httpx 流式读取 SSE |
| 测试 | pytest + Vitest | 后端 pytest 异步测试，前端 Vitest 组件测试 |

### 目录结构

```
AdaWorks/
├── frontend/src/
│   ├── components/
│   │   ├── chat/                  # Agent Chat (View→Panel→Leaf)
│   │   ├── TranslationView.vue    # 翻译页
│   │   ├── SummarizationView.vue  # 总结页
│   │   ├── DashboardView.vue      # 工作台
│   │   └── shared/                # StreamingBadge, TruncatedText, ApiKeyBanner
│   ├── composables/               # 业务逻辑层 (useSSE, useTask, useChatStream, ...)
│   ├── stores/                    # 状态层 (workspace, chat)
│   ├── services/                  # 网络层 (linguistApi, api, websocket)
│   ├── router/guards.ts           # 流式任务导航守卫
│   └── utils/                     # 纯函数 (safeAsync, taskPersistence, randomId)
│
├── backend/adaworks/
│   ├── api/                       # 路由层 (task, functions, schemas, validators)
│   ├── services/                  # 业务逻辑 (task_manager, llm, prompt, ...)
│   ├── middleware/                 # 请求管线 (BodyLimit, RequestId)
│   ├── ws_hub.py                  # WebSocket Room 广播
│   ├── db.py                      # 持久化层 (aiosqlite + Lock)
│   ├── config.py                  # 配置中心 (pydantic-settings)
│   └── *_agent.py                 # LLM Provider (glm, gemini, mock)
│
├── cli/ai_app.py                  # CLI 工具
├── docs/                          # 架构文档、API 契约、使用手册
└── Makefile                       # test / build / lint
```

---

## Getting Started

### Prerequisites

- Node.js >= 18
- Python >= 3.10

### Install & Run

```bash
git clone <repo-url> AdaWorks && cd AdaWorks
npm install && npm run sidecar:setup    # 安装前端依赖 + 创建后端虚拟环境

# 配置 LLM（可选 — 不配置则 Mock 模式零配置运行）
cp backend/.env.example backend/.env
# 编辑 backend/.env: LLM_MODE=real, GLM_API_KEY=xxx

npm run dev:all    # 前端(:1420) + 后端(:18765) 同时启动
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:1420 |
| API Health | http://127.0.0.1:18765/api/health |
| CLI | `ai-app translate --text "Hello" --from en --to zh` |

### Test & Build

```bash
make test            # 全部：后端 pytest + CLI + 前端 vitest
make test-backend    # cd backend && .venv/bin/python -m pytest tests/ -q
make test-frontend   # cd frontend && npm run test
make build           # cd frontend && npm run build (含 vue-tsc 类型检查)
```

### Docker

```bash
docker compose up --build
```

---

## API Reference

完整规范见 [`docs/spec/api-design.md`](docs/spec/api-design.md)。

### SSE Task Protocol

所有 AI 调用统一走此协议。前端通过 `useSSE` composable 消费，后端通过 `TaskManager` 管理生命周期。

```
POST /api/task
  → SSE Stream:
    event: task_start   data: {taskId}
    event: token        data: {content, seq}
    ...
    event: task_done    data: {taskId, status, duration, result}
    event: task_error   data: {taskId, message}
```

| Operation | Method | Path |
|-----------|--------|------|
| Submit task | `POST` | `/api/task` |
| Cancel task | `DELETE` | `/api/task/{taskId}` |
| Query status | `GET` | `/api/task/{taskId}` |
| Capability discovery | `GET` | `/api/functions` |
| Health check | `GET` | `/api/health` |

### Agent Chat

| Operation | Method | Path |
|-----------|--------|------|
| Session CRUD | `GET/POST/DELETE` | `/api/sessions[/{id}]` |
| Send message | `POST` | `/api/chat` |
| Stream events | `WebSocket` | `/ws/chat/{session_id}` |

---

## Roadmap

AdaWorks 正在向完整的 AI Native Workbench 演进。当前版本 (v0.x) 已落地核心流式基础设施和三大 AI 模块，以下为迭代计划：

### v0.x — Current（已上线）

- [x] 统一 SSE 任务协议 + TaskManager 状态机
- [x] 多语言翻译（10 语言 × 5 语调）
- [x] 智能总结（要点模式 + 概述模式 + JSON 校验 + 自动重试）
- [x] Agent Chat（WebSocket Room 广播 + ReAct 步骤可视化）
- [x] Prompt 安全（XML 隔离 + 输出校验 + 语言一致性）
- [x] CLI 工具 + Agent 技能描述（SKILL.md）
- [x] 明暗主题 + 响应式布局

### v0.9 — In Progress

- [ ] RAG 文档问答：ChromaDB + Embedding → `/api/task { type: "rag_query" }`
- [ ] LangChain Agent 集成：Tool Calling 标准化，替代手写 mock_agent
- [ ] MCP 工具协议：`tools/list` + `tools/call` 端点，兼容 Claude / GPT 工具调用
- [ ] Docker 优雅停机：SIGTERM handler + 任务快照持久化
- [ ] PostgreSQL 迁移：db.py 抽象层切换驱动 + asyncpg 连接池

### v1.0 — Planned

- [ ] Redis 状态存储：TaskManager + Session 迁移，支持多进程部署
- [ ] 用户认证：JWT + 多租户数据隔离
- [ ] 可观测性：OpenTelemetry 追踪 + Prometheus 任务/延迟/错误率指标
- [ ] 虚拟滚动：聊天消息列表按可视区域渲染，支持万级消息
- [ ] 消息队列：RabbitMQ/Kafka 解耦 LLM 调用，Worker 水平扩展

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | 系统架构详解 — 前端分层、后端模块、数据流图 |
| [docs/manual.md](docs/manual.md) | 使用手册 — 功能说明、配置项、常见问题 |
| [docs/spec/](docs/spec/) | API 契约、开发规范、需求规格、任务拆分 |
| [agent.md](agent.md) | AI Agent 协作记录与决策日志 |

---

## License

© 2026 RenXiaodi
