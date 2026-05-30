# 模块架构说明

> 本文档描述 AdaWorks 三大模块（Backend · Frontend · CLI）的目录结构、各模块功能与依赖关系。
> 建议阅读顺序：先通读本页，再按 Backend → Frontend → CLI 逐层深入。

---

## 全局依赖关系

```
┌──────────────────────────────────────────────────────────┐
│                      用户入口                             │
│  Browser (http://localhost:1420)  ·  Terminal (ai-app)   │
└───────────┬──────────────────────────────┬───────────────┘
            │ HTTP / SSE / WebSocket       │ HTTP / SSE
            ▼                              ▼
┌───────────────────┐            ┌─────────────────┐
│   Frontend (Vue)  │            │    CLI (Click)   │
│  port 1420 (Vite) │            │   ai-app 命令    │
└────────┬──────────┘            └────────┬────────┘
         │ REST / SSE / WS                │ REST / SSE
         ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                       │
│                   port 18765                              │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │ SSE API │  │ Chat API  │  │  Agent   │  │   LLM    │ │
│  │ /task   │  │ /sessions │  │ (WS Hub) │  │ Service  │ │
│  └────┬────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │              │              │       │
│  ┌────▼─────────────▼──────────────▼──────────────▼─────┐ │
│  │              Task Manager + SQLite                    │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**关键契约**：Frontend 和 CLI 均通过 `POST /api/task` SSE 端点完成翻译/总结，不直接调用 LLM。

---

## 一、Backend（Python FastAPI）

### 目录结构

```
backend/
├── adaworks/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 环境变量配置（pydantic-settings）
│   ├── db.py                   # SQLite 持久层（会话 + 消息）
│   ├── ws_hub.py               # WebSocket 连接管理
│   ├── http_safe.py            # 全局异常处理
│   ├── linguist_service.py     # 翻译/总结内存日志（环形缓冲）
│   ├── env_secrets.py          # API Key 安全处理
│   ├── bootstrap_env.py        # .env 文件加载
│   ├── api/                    # ── API 路由层（薄层，委托 service）──
│   │   ├── router.py           #   路由聚合（functions + task）
│   │   ├── functions.py        #   GET /api/functions — 能力发现
│   │   ├── task.py             #   POST/DELETE/GET /api/task — SSE 任务
│   │   ├── schemas.py          #   Pydantic 请求/响应模型
│   │   └── validators.py       #   输入校验（长度、控制字符、注入检测）
│   ├── services/               # ── 业务逻辑层 ──
│   │   ├── llm.py              #   LLM 统一流式服务（mock/real）
│   │   ├── task_manager.py     #   任务状态机（pending→running→done/failed/cancelled）
│   │   ├── task_sweeper.py     #   僵尸任务后台清理
│   │   ├── task_log.py         #   SSE 任务日志辅助
│   │   ├── prompt.py           #   Prompt 构建（翻译/总结）
│   │   ├── prompt_security.py  #   Prompt 防注入（XML 标签包装）
│   │   ├── summary_parser.py   #   总结结果 JSON 解析与校验
│   │   └── log_sanitize.py     #   日志字段脱敏
│   ├── middleware/
│   │   ├── request_id.py       #   X-Request-ID 注入
│   │   └── body_limit.py       #   请求体大小限制（1MB）
│   ├── glm_agent.py            # 智谱 GLM 流式 Agent
│   ├── gemini_agent.py         # Google Gemini 流式 Agent
│   └── mock_agent.py           # Mock Agent（无 Key 演示）
└── tests/                      # pytest 测试用例
```

### 模块依赖关系

```
                    main.py（应用入口）
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   api/router.py    ws_hub.py     linguist_service.py
        │               │               │
   ┌────┴────┐          │          ┌────┴─────┐
   ▼         ▼          │          ▼          ▼
functions  task.py      │    log_sanitize  config.py
   │         │          │
   ▼    ┌────┼────┐     │
schemas  │    │    │     │
   │    ▼    ▼    ▼     ▼
validators llm prompt task_log task_manager
              │    │              │
              ▼    ▼              ▼
          config  prompt_security config
              │    │
              ▼    ▼
         env_secrets  summary_parser
                        │
                        ▼
                   prompt_security
```

### 按功能阅读顺序

1. **config.py** → 理解全局配置项（LLM_MODE、超时、并发上限等）
2. **api/schemas.py** + **api/validators.py** → 理解输入校验规则
3. **services/task_manager.py** → 理解任务状态机生命周期
4. **services/llm.py** + **services/prompt.py** → 理解 LLM 调用与 Prompt 构建
5. **api/task.py** → 理解 SSE 流式任务端点（核心 API）
6. **api/functions.py** → 理解能力发现端点
7. **main.py** → 理解应用组装、路由注册、中间件链

---

## 二、Frontend（Vue 3 + TypeScript）

### 目录结构

```
frontend/src/
├── main.ts                     # Vue 应用入口（Pinia + Router + Ant Design）
├── App.vue                     # 根组件（主题切换 + 响应式布局）
├── index.css                   # 全局基础样式
├── types.ts                    # 共享类型定义
├── types/
│   └── chat.ts                 # Chat 模块类型
│
├── router/                     # ── 路由 ──
│   ├── index.ts                #   路由表（6 页面 + 懒加载）
│   └── guards.ts               #   流式任务离开守卫 + beforeunload
│
├── stores/                     # ── Pinia 全局状态 ──
│   ├── workspace.ts            #   工作区状态（日志、健康、主题、活跃任务）
│   └── chat.ts                 #   Chat 状态（会话列表、消息、WS 事件）
│
├── services/                   # ── API 客户端（无 Vue 逻辑）──
│   ├── linguistApi.ts          #   SSE Task API 客户端（/health, /logs, /task）
│   ├── api.ts                  #   Chat REST 客户端（/sessions, /chat）
│   └── websocket.ts            #   WebSocket URL 构造
│
├── composables/                # ── 可复用组合函数 ──
│   │
│   │  ── SSE 流式核心 ──
│   ├── useSSE.ts               #   SSE 解析器（fetch + ReadableStream）
│   ├── useStreamBuffer.ts      #   16ms 批量渲染缓冲
│   ├── useTask.ts              #   任务编排（提交、取消、恢复）
│   │
│   │  ── Chat 流式 ──
│   ├── useChatStream.ts        #   WebSocket 生命周期管理
│   │
│   │  ── Linguist 功能 ──
│   ├── useLinguistTaskLog.ts   #   SSE 任务 → 运行日志集成
│   ├── useFileImport.ts        #   文件拖拽导入（TXT/MD）
│   ├── useQuickTextPrefill.ts  #   快捷文本路由预填
│   ├── useDashboardMetrics.ts  #   仪表盘指标计算
│   ├── useTaskRecovery.ts      #   刷新恢复（sessionStorage）
│   │
│   │  ── UI 工具 ──
│   ├── useAutoScroll.ts        #   自动滚动（O(1) tick）
│   ├── useBreakpoint.ts        #   响应式断点检测
│   ├── useThemeAttribute.ts    #   暗色模式属性管理
│   ├── useExportActions.ts     #   复制反馈 + 文件下载
│   ├── useLogHistory.ts        #   日志分页逻辑
│   └── useQuickRoute.ts        #   智能路由（根据输入内容判断跳转）
│
├── views/                      # ── 页面壳（View → Panel → Leaf）──
│   └── ChatView.vue            #   Chat 页面布局
│
├── components/                 # ── 组件 ──
│   ├── DashboardView.vue       #   工作台（指标 + 功能卡片 + 快捷输入）
│   ├── TranslationView.vue     #   翻译页（双栏 + SSE 流式）
│   ├── SummarizationView.vue   #   总结页（配置 + 结构化结果）
│   ├── HistoryView.vue         #   运行日志（分页列表）
│   ├── SettingsView.vue        #   设置页（环境信息）
│   ├── Sidebar.vue             #   全局侧边栏导航
│   ├── chat/                   #   ── Chat 子组件（Leaf 层）──
│   │   ├── ChatPanel.vue       #     消息面板（消息列表 + 输入栏）
│   │   ├── ChatHeader.vue      #     对话头部
│   │   ├── ChatSidebar.vue     #     会话列表
│   │   ├── InputBar.vue        #     输入栏（自动调整 + 模式切换）
│   │   ├── MessageBubble.vue   #     用户消息气泡
│   │   ├── ThinkBlock.vue      #     ReAct Think 步骤
│   │   ├── ActionBlock.vue     #     ReAct Action 步骤
│   │   ├── ObservationBlock.vue#     ReAct Observation 步骤
│   │   └── FinalResult.vue     #     最终结果块
│   └── shared/                 #   ── 共享组件 ──
│       ├── ApiKeyBanner.vue    #     API Key 配置提示
│       ├── StreamingBadge.vue  #     流式进行中标记
│       └── TruncatedText.vue   #     文本截断展开
│
├── utils/                      # ── 工具函数 ──
│   ├── safeAsync.ts            #   runSafe() 统一异步错误处理
│   ├── randomId.ts             #   UUID 生成（跨浏览器兼容）
│   ├── taskPersistence.ts      #   任务 sessionStorage 持久化
│   └── linguistFormat.ts       #   总结结果格式化（复制/下载）
│
└── styles/
    ├── theme.css               # 明/暗语义 CSS 变量
    └── ant-controls.css        # Ant Design 控件样式覆盖
```

### 模块依赖关系

```
                 App.vue（根组件）
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    router/      stores/     composables/
   (路由守卫)   (workspace   (业务逻辑)
    │           chat)           │
    ▼            │    ┌─────────┼──────────┐
  Views/         ▼    ▼         ▼          ▼
 (页面壳)    services/  useSSE  useTask  useChat
    │        (API 客户端)  │       │        │
    ▼            ▲        ▼       ▼        ▼
 Components  ────┘   useStream  useTask  useChatStream
 (功能组件)        Buffer    Recovery  (WebSocket)
    │                 │
    ▼                 ▼
  utils/         linguistApi.ts
 (工具函数)      (SSE HTTP 调用)
```

### 数据流

**SSE 翻译/总结流程**：
```
TranslationView / SummarizationView
  → useTask.submitTask()
    → linguistApi.createTaskSSE()     # POST /api/task
      → useSSE.startSSE()             # ReadableStream 解析
        → useStreamBuffer             # 16ms 批量渲染
          → Vue reactive 更新
  → useLinguistTaskLog                # 完成后写入运行日志
    → workspace.addLog()
```

**Chat WebSocket 流程**：
```
ChatView
  → ChatPanel.onSubmitMessage()
    → chat.sendUserMessage()          # POST /api/chat
  ← useChatStream                     # WebSocket 事件
    → chat.applyAgentEvent()          # ReAct 步骤处理
      → MessageBubble / ThinkBlock / ActionBlock...
```

### 按功能阅读顺序

1. **router/index.ts** → 理解页面结构与路由表
2. **stores/workspace.ts** → 理解跨页状态（主题、日志、健康检查）
3. **services/linguistApi.ts** → 理解 SSE API 客户端
4. **composables/useSSE.ts** + **useStreamBuffer.ts** → 理解 SSE 流式核心
5. **composables/useTask.ts** → 理解任务编排
6. **components/TranslationView.vue** / **SummarizationView.vue** → 理解页面集成
7. **stores/chat.ts** + **composables/useChatStream.ts** → 理解 Chat 流程

---

## 三、CLI（Python Click）

### 目录结构

```
cli/
├── ai_app.py                   # CLI 主文件（Click 命令定义 + SSE 解析）
├── setup.py                    # 包安装配置（ai-textflow-cli v0.1.0）
└── tests/
    ├── conftest.py             # 测试配置
    └── test_cli.py             # 命令行测试（CliRunner + mock httpx）
```

### 模块功能

| 模块 | 功能 | 关键依赖 |
|------|------|----------|
| `ai_app.py` | CLI 入口，提供 `list`/`translate`/`summarize` 三个命令 | `click`（命令框架）、`httpx`（HTTP/SSE 客户端） |
| `setup.py` | 定义 `ai-app` console_script 入口点 | `click`, `httpx` |
| `tests/` | 功能测试：list 输出、translate 退出码 | `pytest`, `click.testing.CliRunner` |

### CLI 与 Backend 的交互

```
ai-app list        →  GET  /api/functions
ai-app translate   →  POST /api/task (SSE: task_start → token* → task_done)
ai-app summarize   →  POST /api/task (SSE: task_start → token* → task_done)
```

**环境变量**：
- `AI_APP_BASE_URL`：Backend 地址（默认 `http://127.0.0.1:18765`）

### Agent 集成

CLI 通过 `.claude/skills/SKILL.md` 被外部 Agent（如 Claude Code）发现。SKILL.md 描述了命令用法与 API 契约，Agent 可直接调用 `ai-app` 或 HTTP 端点。

---

## 四、关键设计模式

| 模式 | 位置 | 说明 |
|------|------|------|
| **统一 SSE 契约** | `api/task.py` | 翻译/总结共用 `POST /api/task`，通过 `type` 字段区分 |
| **任务状态机** | `services/task_manager.py` | pending → running → done / failed / cancelled |
| **协作式取消** | `asyncio.Event` | 前端 `DELETE /api/task/{id}` → 后端设置取消事件 → SSE 发 task_done |
| **16ms 渲染缓冲** | `useStreamBuffer.ts` | Token 到达后批量更新 Vue reactive，避免逐 token 重渲染 |
| **View → Panel → Leaf** | Chat 模块 | `ChatView` → `ChatPanel` → `MessageBubble`/`ThinkBlock` 严格分层 |
| **Mock / Real 双模式** | `services/llm.py` | `LLM_MODE=mock` 本地预设流 / `LLM_MODE=real` 真实 GLM 调用 |
| **Prompt 防注入** | `prompt_security.py` | XML 标签包装用户输入，系统 Prompt 白名单 |
