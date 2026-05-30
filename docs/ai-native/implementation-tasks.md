# AI TextFlow — 实现任务清单（Implementation Tasks）

> 来源：[plan.md](./plan.md) + [implementation-solution.md](./implementation-solution.md)
> 策略：**现有AdaWorks AI/ AdaWorks 增量改造**，UI 不动，底层接入 SSE task 契约
> 原则：每个任务足够小、可独立验收、自带测试用例；按「必做 → 加分 → 文档」优先级排序，可并行任务标注 `[P]`。

---

## 0. 阅读指南

### 任务编号规则

- `T<阶段>.<序号>`，例如 `T0.1`（阶段 0 = Router 迁移）、`T2.3`。
- `[P]` 表示**该任务与同阶段其他 `[P]` 任务无依赖，可并行执行**。
- 无 `[P]` 的任务通常是该阶段的前置依赖或汇总验收点，需串行。

### 优先级分层

| 层级           | 含义                               | 阶段       |
| -------------- | ---------------------------------- | ---------- |
| `P0` 必做-核心 | 不完成则项目不可用                 | 阶段 0 ~ 4 |
| `P1` 必做-完整 | 基础交付门槛（CLI / skill / 启动） | 阶段 5 ~ 6 |
| `P2` 加分项    | 提升体验与工程质量                 | 阶段 7     |
| `P3` 文档      | 交付文档与使用手册                 | 阶段 8     |

### 改造约束（贯穿全部任务）

- **UI 不动**：沿用 `DashboardView` / `TranslationView` / `SummarizationView` / `HistoryView` / `SettingsView` / `ChatView`，不新建 `HomeView`、`StreamOutput`、`FunctionCard`。
- **导航改 Router**：`App.vue` 的 `activeView` → Vue Router 4 + `<router-view>`。
- **后端在 adaworks 包内扩展**：`backend/adaworks/` 增量新增模块，保留会话/聊天/WebSocket/日志等已有路由。
- **Sidecar 端口 18765**（非 8000）；根目录 `npm run dev:all` 一键启动。
- **task 类型**：`translate` | `summarize`（非 `translate_zh2en`）；翻译参数含 `sourceLang` / `targetLang` / `tone`。

### 关于外部依赖（LLM API）的统一约定

- LLM 调用必须**具备真实对接能力**（OpenAI 兼容协议 `/chat/completions`，`stream=true`），复用现有 `glm_agent` SSE 解析。
- 通过环境变量 `LLM_MODE=mock|real` 做**功能开关**：
  - `mock`：本地预设逐字流，**前端/CLI 联调不依赖任何外部网络与密钥**。
  - `real`：读取 `LLM_API_KEY / LLM_API_BASE / LLM_MODEL` 调真实接口。
- 测试默认在 `mock` 下进行；`real` 模式提供一条**带密钥才运行、否则自动跳过**的集成测试。

### 关于数据存储

- 任务状态用进程内内存字典（`task_manager.py`）。
- **History 已有**：`linguist_service` 内存日志 + `HistoryView`，保持现状，**不在范围外**。
- Agent Chat（WebSocket）为加分模块，改造时不破坏。

---

## 阶段 0：Vue Router 迁移（P0）

> 目标：导航与跨页状态就绪，为 SSE 改造铺路。依赖现有前端工程。

### T0.1 安装 vue-router 并创建路由表 [F0]

- 交付物：`frontend/package.json` 增加 `vue-router@4`；`frontend/src/router/index.ts`。
- 实现要点：路由 `/dashboard`、`/translation`、`/summarization`、`/chat`、`/history`、`/settings`；`/` redirect `/dashboard`；组件路径指向现有 `components/` 与 `views/ChatView.vue`。
- 测试用例：`cd frontend && npm run build` 通过；手动访问各路径不白屏。
- 手册更新：手册「2. 导航与页面入口」。

### T0.2 App.vue + Sidebar 迁移 [F0]

- 交付物：改造 `App.vue`（`<router-view />`，移除 `activeView` / `<component :is>`）；改造 `Sidebar.vue`（`router-link` + `useRoute` 高亮）。
- 实现要点：`DashboardView` 卡片与快捷输入改用 `router.push`；`main.ts` 注册 `app.use(router)`。
- 测试用例：手动验收：Sidebar 切换 URL 变化；浏览器后退/前进正常；刷新后停留在当前页。

### T0.3 workspace Pinia Store [F0]

- 交付物：`frontend/src/stores/workspace.ts`。
- 实现要点：从 `App.vue` 下沉 `logs`、`quickText`、`apiConnected` 及 `fetchHealth` / `fetchLogs` / `handleAddLog` 等；各 View 改从 store 读写。
- 测试用例：`vitest` store 单测：写入 `quickText` 后 `TranslationView` 能读取（mock store）；`npm run build` 无类型错误。

---

## 阶段 1：后端 SSE 模块（P0）

> 目标：在 `backend/adaworks/` 内新增 task 契约，mock 模式可流式输出。依赖现有 FastAPI 入口。

### T1.1 [P] 配置管理 `adaworks/config.py` [F9]

- 交付物：`backend/adaworks/config.py`（`Settings` + `settings` 单例）。
- 实现要点：`pydantic-settings` 读 `.env`；含 `llm_mode`、`llm_api_key`、`llm_api_base`、`llm_model`、`task_timeout_seconds`、端口默认 **18765**。
- 测试用例：`backend/tests/test_config.py`：默认 `llm_mode == "mock"`；设 `LLM_MODE=real` 后重载断言生效。

### T1.2 LLM 服务 — mock 流 [F9]

- 交付物：`backend/adaworks/services/llm.py`（`LLMService.stream()` + `_mock_stream()`）。
- 实现要点：统一 `AsyncIterator[str]`；mock 按 type/prompt 返回翻译/总结预设文本，逐字 yield；real 模式复用 `glm_agent` 流式解析。
- 测试用例：`backend/tests/test_llm_mock.py`：`LLM_MODE=mock` 下 `async for` 收集 token 数量 > 1 且拼接非空。

### T1.3 [P] LLM 服务 — real 流 [F9]

- 交付物：`LLMService._real_stream()`（httpx 调 OpenAI 兼容 API）。
- 测试用例：单元测试用 MockTransport 伪造 SSE；集成测试 `@pytest.mark.skipif(not LLM_API_KEY)` 真连一次。

### T1.4 [P] Prompt 模板 [F9]

- 交付物：`backend/adaworks/services/prompt.py`（承接/迁移 `linguist_service` 翻译与总结 prompt）。
- 实现要点：支持多语言 `sourceLang`/`targetLang`、语调 `tone`；总结含 `keyPointsCount` / `wordLimit`。
- 测试用例：`backend/tests/test_prompt.py`：translate prompt 含目标语言；summarize prompt 含要点数。

### T1.5 请求/响应模型

- 交付物：`backend/adaworks/api/schemas.py`（`TaskCreateRequest`、`FunctionItem`、`FunctionsResponse` 等）。
- 测试用例：`TaskCreateRequest(type="translate", params={"text":"x","sourceLang":"zh","targetLang":"en"})` 成功；缺字段抛 `ValidationError`。

### T1.6 功能列表 `GET /api/functions` [F6]

- 交付物：`backend/adaworks/api/functions.py` + 注册到 `main.py`。
- 实现要点：返回 **translate**、**summarize** 两项（供 CLI/skill 使用；前端 Dashboard 不依赖）。
- 测试用例：`backend/tests/test_functions_api.py`：`GET /api/functions` 200，`functions` 长度 == 2 且含 `translate`、`summarize`。
- 手册更新：手册「3.1 查看可用功能（CLI）」。

### T1.7 任务流式 `POST /api/task` (SSE) [F7]

- 交付物：`backend/adaworks/api/task.py`（`create_task` + `_task_generator`；事件 `task_start` / `token` / `task_done` / `task_error`）。
- 实现要点：按 `type` 构 prompt；逐 token 推 SSE；结束写 History 日志（复用 `linguist_service`）。
- 测试用例：`backend/tests/test_task_sse.py`（mock）：POST `{"type":"translate","params":{"text":"你好","sourceLang":"zh","targetLang":"en"}}`，断言首事件 `task_start`、≥1 个 `token`、末事件 `task_done`。
- 手册更新：手册「3.2 翻译」「3.3 总结」（API 示例）。

---

## 阶段 2：前端 SSE 对接（P0）

> 目标：现有翻译/总结页在 mock 后端下流式输出。依赖阶段 0、1。

### T2.1 [P] 改造 `linguistApi.ts`

- 交付物：新增 `getFunctions`、`createTaskSSE`、`cancelTask`；保留旧接口直至 T2.4 完成。
- 测试用例：`vitest` mock `fetch`，断言 URL 为 `/api/task`、`/api/functions`。

### T2.2 `useSSE` composable [F4]

- 交付物：`frontend/src/composables/useSSE.ts`。
- 实现要点：fetch + ReadableStream 解析 `data:`；`AbortController`；Abort 不计 error。
- 测试用例：`vitest`：可控 ReadableStream 断言 `result` 累加、`stop()` 生效。

### T2.3 `useTask` composable [F5/F7/F8]

- 交付物：`frontend/src/composables/useTask.ts`（`submitTask` + `cancelCurrentTask`）。
- 测试用例：`vitest`：mock 断言 cancel 先 abort 再 DELETE。

### T2.4 改造 `TranslationView.vue` [F2]

- 交付物：非流式 `api.translate()` → `useTask().submitTask('translate', { text, sourceLang, targetLang, tone })`。
- 实现要点：**UI 布局不动**；结果区逐字追加；流式中显示「停止生成」。
- 测试用例：手动验收 mock 后端：输入文本点翻译，结果区打字机输出；点停止中断。
- 手册更新：手册「3.2 翻译（界面）」。

### T2.5 改造 `SummarizationView.vue` [F3]

- 交付物：`submitTask('summarize', { text, keyPointsCount, wordLimit, tone })`。
- 实现要点：保留概述+要点结构；流式阶段 raw 追加，`task_done` 后解析渲染。
- 测试用例：组件单测断言 `submitTask` 参数；手动验收 mock 流式 + 停止。
- 手册更新：手册「3.3 总结（界面）」。

### T2.6 [P] 改造 `DashboardView.vue` [F1]

- 交付物：卡片 `router.push`；快捷输入写 `workspaceStore.quickText` 后跳转。
- 测试用例：手动：工作台 → 翻译页，`quickText` 已预填。

---

## 阶段 3：任务取消 + real 模式（P0）

> 目标：取消能力 + 真实 LLM；移除旧 REST 接口。

### T3.1 任务管理器 `task_manager.py` [F21]

- 交付物：`backend/adaworks/services/task_manager.py`（状态机 pending→running→done/failed/cancelled）。
- 测试用例：`backend/tests/test_task_manager.py`：create/get/cancel 基本路径。

### T3.2 取消接口 `DELETE /api/task/{taskId}` [F8]

- 交付物：`task.py` 的 `cancel_task`；generator 内检测 `CANCELLED`。
- 测试用例：`backend/tests/test_task_cancel.py`：运行中任务 DELETE 后流提前结束。
- 手册更新：手册「3.4 停止生成」。

### T3.3 接入 real LLM + 任务超时 [F9/F18]

- 交付物：`LLM_MODE=real` 走真实 GLM；`task_timeout_seconds` 超时终止。
- 测试用例：mock 测试保留；real 集成 skip 无密钥。

### T3.4 移除旧接口

- 交付物：前端仅通过 `POST /api/task` SSE 提交 translate/summarize；后端无独立 REST 翻译/总结路由。
- 测试用例：回归 `backend/tests/test_api.py` 更新为新契约；前端 build 通过。

---

## 阶段 4：CLI + SKILL.md（P1 必做-完整）

> 依赖后端 mock 可用（18765）。

### T4.1 CLI 主程序 `cli/ai_app.py` [F10]

- 交付物：`translate` / `summarize` / `list`；`_stream_task` 终端逐字打印。
- 实现要点：`BASE_URL=http://127.0.0.1:18765`；translate 传 `type=translate` + `sourceLang`/`targetLang`。
- 测试用例：`cli/tests/test_cli.py`：`ai-app list` 含 `translate`；`ai-app translate --text Hello --from en --to zh` 退出码 0。
- 手册更新：手册「4. CLI 使用」。

### T4.2 [P] CLI 打包 `cli/setup.py`

- 交付物：`console_scripts: ai-app=ai_app:cli`。
- 测试用例：`pip install -e . && ai-app --help` 列出三命令。

### T4.3 [P] `.claude/skills/SKILL.md` [F11/F12]

- 交付物：SKILL.md（name/description + 三命令 + 前置条件 18765 + 示例）。
- 测试用例：frontmatter 校验；人工：Claude Code 发现并调用（截图存 `docs/`）。
- 手册更新：手册「5. 作为 Agent 工具被调用」。

---

## 阶段 5：启动与联调（P1 必做-完整）

### T5.1 验证根目录 `npm run dev:all`

- 交付物：确认/补充根 `package.json` scripts；`.env.example` 含 `LLM_MODE=mock`。
- 实现要点：sidecar **18765** + frontend **1420**；可选 Vite proxy `/api` → 18765。
- 测试用例：`npm run dev:all` 后 `curl -sf http://127.0.0.1:18765/api/functions` 200；前端翻译页 mock 流式可用。
- 手册更新：手册「0. 快速开始」。

### T5.2 [P] 统一测试入口

- 交付物：根 `Makefile` 或 `package.json` script：`make test` = 后端 pytest + 前端 vitest。
- 测试用例：`make test` 退出码反映结果。

---

## 阶段 6：加分项（P2）

> 与核心无强依赖，可并行。

### T6.1 [P] Ant Design Vue 明暗主题 [F19]

- 交付物：`App.vue` 中 `a-config-provider` + `theme.darkAlgorithm` / `defaultAlgorithm` 切换；Sidebar 增加切换按钮。
- 实现要点：**不用** `useTheme.ts` / `theme.css` / `@vueuse/useDark`。
- 测试用例：手动：切换后 Ant 组件色板变化；刷新持久化（localStorage 存 `isDark`）。
- 手册更新：手册「7.1 深色/浅色主题」。

### T6.2 [P] 响应式布局核对 [F20]

- 交付物：核对现有 Tailwind 断点（375px / 768px）无溢出。
- 测试用例：手动截图存 `docs/`。
- 手册更新：手册「7.2 响应式」。

### T6.3 [P] 统一错误处理 + traceId [F15/F16/F17]（可选）

- 交付物：FastAPI 异常中间件；请求头 `X-Trace-Id`。
- 测试用例：故意传非法 body 返回标准 JSON 错误。

### T6.4 [P] Docker [F24]（可选）

- 交付物：`Dockerfile` + `docker-compose.yml`。
- 测试用例：`docker compose up` 后 functions 端点可达。

---

## 阶段 7：文档交付（P3）

### T7.1 [P] `agent.md` [F13]

- 交付物：Agent 角色/人类决策/协作工具记录。
- 测试用例：含职责/决策/执行/工具四要素。

### T7.2 [P] `docs/spec/` 目录 [F14]

- 交付物：`requirements.md`、`api-design.md`、`page-mockup.md`、`task-breakdown.md`（标注 future scope：Tauri/RAG/MCP 等）。
- 测试用例：四文件非空；`api-design.md` 含 functions/task/cancel 三端点。

### T7.3 [P] `README.md` 更新

- 交付物：API/CLI/Docker/mock/Agent Chat 说明；`npm run dev:all` 快速开始。
- 测试用例：按 README 从零跑通 mock 链路。

### T7.4 系统使用手册 `docs/manual.md`（活文档）

- 章节映射见各任务「手册更新」标记；交付前逐章核对与行为一致。

---

## 8. 整体任务执行说明

### 8.1 执行顺序与里程碑

```
阶段0(Router) ──► 阶段1(后端SSE) ──► 阶段2(前端SSE) ──► 阶段3(取消+real)
   P0/必做           P0/必做            P0/必做             P0/必做
                                                          │
                              ┌───────────────────────────┼───────────────────┐
                              ▼                           ▼                   ▼
                        阶段4(CLI/skill)            阶段5(启动联调)        阶段6(加分)
                          P1/必做                     P1/必做               P2
                              └───────────────────────────┼───────────────────┘
                                                          ▼
                                                    阶段7(文档) P3
```

- **M1**：阶段 0–2 → 浏览器翻译页 mock 流式输出。
- **M2**：阶段 3 → 取消 + summarize + 旧接口移除。
- **M3**：阶段 4–5 → CLI + skill + `dev:all`。
- **M4**：阶段 6–7 → 加分 + 文档。

### 8.2 并行执行策略

- 阶段 0：`T0.1` → `T0.2` / `T0.3`（T0.3 可与 T0.2 部分并行）。
- 阶段 1：`T1.3` / `T1.4` 与 `T1.2` 并行；schemas 完成后 `T1.6` / `T1.7`。
- 阶段 2：`T2.1` / `T2.2` 并行；`T2.4` / `T2.5` / `T2.6` 在 composable 就绪后可并行。
- 阶段 6、7 内部任务可大量并行。

### 8.3 Definition of Done

1. 交付物实现并通过本任务测试用例；
2. 不破坏既有测试（含 Agent Chat / History）；
3. 带「手册更新」的任务同步补写 `docs/manual.md`；
4. `LLM_MODE=mock` + `npm run dev:all` 可零配置演示全链路。

### 8.4 明确保留（不破坏、不重做）

| 模块                      | 说明                   |
| ------------------------- | ---------------------- |
| `HistoryView` + 内存日志  | 已有调用记录，保持现状 |
| `ChatView` + WebSocket    | Agent Chat 加分模块    |
| `SettingsView`            | 设置页保持             |
| 10 语言 + 5 语调翻译 UI   | 仅改数据层             |
| Ant Design Vue + Tailwind | 不引入其他 UI 库       |

### 8.5 后续扩展（本期不实现，见 plan.md §6.6）

Tauri 桌面壳、RAG 知识库、MCP 工具接入等——仅在 `docs/spec/` 标注 future scope。
