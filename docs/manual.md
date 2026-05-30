# AI TextFlow /AdaWorks AI— 系统使用手册

> 活文档：与 [`implementation-tasks.md`](./ai-native/implementation-tasks.md) 各任务「手册更新」章节对应。  
> 最后核对：2026-05-30

---

## 0. 快速开始

### 环境要求

- Node.js ≥ 18
- Python ≥ 3.10

### 安装与启动

```bash
git clone <repo-url> AdaWorks && cd AdaWorks
npm install
npm run sidecar:setup          # 创建 backend/.venv 并安装依赖
cp backend/.env.example backend/.env   # 或 cp .env.example .env
npm run dev:all
```

| 服务         | 地址                              |
| ------------ | --------------------------------- |
| 前端 Web UI  | http://localhost:1420             |
| 后端 Sidecar | http://127.0.0.1:18765            |
| 健康检查     | http://127.0.0.1:18765/api/health |

验证 Sidecar：

```bash
curl -sf http://127.0.0.1:18765/api/functions
```

### 前端 API 地址

开发环境默认配置见 `frontend/.env.development`：

| 变量            | 默认值                       | 说明                 |
| --------------- | ---------------------------- | -------------------- |
| `VITE_API_BASE` | `http://127.0.0.1:18765/api` | REST 请求前缀        |
| `VITE_WS_BASE`  | `ws://127.0.0.1:18765`       | Agent Chat WebSocket |

修改 Sidecar 端口或部署分离时，须同步调整上述变量后重新 `npm run dev`。

### Mock / Real 模式

| 模式   | 配置                            | 说明                       |
| ------ | ------------------------------- | -------------------------- |
| `mock` | `LLM_MODE=mock`（默认）         | 本地预设逐字流，零配置演示 |
| `real` | `LLM_MODE=real` + `GLM_API_KEY` | 调用智谱 GLM 流式接口      |

工作台在 mock 模式下显示 **Mock 模式** 琥珀色徽章；`/api/health` 返回 `{ status, llm, keyLoaded }`。

### Docker 一键启动（可选）

```bash
docker compose up --build
curl -sf http://127.0.0.1:18765/api/functions
```

当前 Docker 仅打包 Sidecar；前端仍通过 `npm run dev` 连接 18765。

### 运行测试

```bash
make test    # 后端 pytest + CLI + 前端 vitest
```

---

## 1. 产品概览

AdaWorks（AdaWorks AI）提供两条能力线：

1. **文本处理主线**：工作台 → 翻译 / 总结 → SSE 流式输出 → 停止生成 → 历史记录
2. **Agent Chat（加分）**：WebSocket 多轮对话，ReAct 步骤展示，会话 SQLite 持久化

文本处理主线路径已实现：输入校验（最长 50,000 字符）、并发限制（最多 3 个运行中任务）、任务超时（默认 60s）、刷新恢复提示、流式离开路由守卫等。详见 [`exception-checklist.md`](./ai-native/exception-checklist.md)。

---

## 2. 导航与页面入口

应用使用 **Vue Router 4**，Sidebar 左侧导航，浏览器后退/前进与刷新均保持当前页（Chat 页除外，使用 `keep-alive` 排除）。

| 路径             | 页面       | 说明                                    |
| ---------------- | ---------- | --------------------------------------- |
| `/`              | 重定向     | → `/dashboard`                          |
| `/dashboard`     | 工作台     | 指标概览、功能卡片、快捷输入、Mock 徽章 |
| `/translation`   | 文本翻译   | 10 语言 × 5 语调，双栏对照              |
| `/summarization` | 智能总结   | 要点数 / 字数 / 语调，结构化输出        |
| `/chat`          | 智能体对话 | WebSocket Agent Chat                    |
| `/history`       | 运行日志   | 翻译/总结调用记录（分页加载）           |
| `/settings`      | 设置       | API 密钥状态、默认语调（模型只读占位）  |

**快捷输入**：在工作台底部输入文本并发送，系统根据长度与关键词识别意图（`useQuickRoute`），跳转到翻译或总结页并将文本预填至输入框（`workspace.quickText`）。

**流式中离开页面**：翻译/总结 SSE 进行中切换路由时，弹出确认 Modal；确认离开会自动取消后端任务（`router/guards.ts`）。

---

## 3. 核心功能

### 3.1 查看可用功能（CLI / API）

**HTTP：**

```bash
curl http://127.0.0.1:18765/api/functions
```

返回 `translate`、`summarize` 两项及参数 schema。

**CLI：**

```bash
ai-app list
```

### 3.2 翻译

#### 界面操作

1. 打开 **文本翻译**（`/translation`）或从工作台卡片进入
2. 输入源文本（`maxlength=50000`），选择源语言、目标语言、语调
3. 点击 **开始翻译** — 结果区逐字流式输出（16ms 渲染缓冲，打字机效果）
4. 流式过程中控件锁定，仅 **停止生成** 可点击
5. 未配置 `GLM_API_KEY` 时顶部显示琥珀色 `ApiKeyBanner`（mock 模式仍可演示）
6. 完成后可复制、下载；记录写入 **运行日志**

Sidecar 未启动时，提交前 `fetchHealth()` 失败会立即提示「服务未就绪」。

#### API 示例

```bash
curl -N -X POST http://127.0.0.1:18765/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "translate",
    "params": {
      "text": "你好世界",
      "sourceLang": "zh",
      "targetLang": "en",
      "tone": "Professional"
    }
  }'
```

**SSE 事件序列：** `task_start` → `token`（多次，含 `seq`）→ `task_done` / `task_error`

**参数说明：**

| 参数         | 类型   | 必填 | 说明                                                            |
| ------------ | ------ | ---- | --------------------------------------------------------------- |
| `text`       | string | 是   | 待翻译文本，最长 50,000 字符                                    |
| `sourceLang` | string | 否   | 源语言代码，默认 `auto`                                         |
| `targetLang` | string | 否   | 目标语言代码，默认 `zh`                                         |
| `tone`       | string | 否   | Professional / Conversational / Technical / Academic / Creative |

### 3.3 总结

#### 界面操作

1. 打开 **智能要点总结**（`/summarization`）
2. 粘贴文本或拖放 `.txt` / `.md` 文件（`useFileImport`）
3. 调整概述字数上限（50–2000）、要点数量（3–10，**默认 3**）、语气风格
4. 点击 **生成总结** — 流式阶段显示原始 JSON，完成后解析为「概述 + 要点列表」
5. 可停止生成、复制、下载；超长结果默认截断预览（`TruncatedText`）

#### API 示例

```bash
curl -N -X POST http://127.0.0.1:18765/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "summarize",
    "params": {
      "text": "长文本内容…",
      "keyPointsCount": 3,
      "wordLimit": 250,
      "tone": "Professional"
    }
  }'
```

后端对总结结果做 Pydantic Schema 校验；失败时最多自动重试 1 次。

### 3.4 停止生成

**界面：** 流式过程中点击 **停止生成** 按钮。

**API：**

```bash
# 从 task_start 事件获取 taskId
curl -X DELETE http://127.0.0.1:18765/api/task/{taskId}
```

前端会先 abort 本地 SSE 连接，再调用 DELETE 通知后端取消。对已结束任务 DELETE 返回 404（幂等）。

### 3.5 任务状态查询与刷新恢复

**API（加分）：**

```bash
curl http://127.0.0.1:18765/api/task/{taskId}
# {"taskId":"...","status":"pending|running|done|failed|cancelled"}
```

**界面：** 流式开始后 `taskId` 写入 `sessionStorage`（`taskPersistence.ts`）。页面 F5 刷新后，`useTaskRecovery` 调用 `GET /api/task/{id}` 并提示：

- `running` → 无法恢复流式连接，请重新提交
- `done` → 任务已完成，请查看运行历史
- `failed` / `cancelled` → 任务已结束

> 当前不支持 partial result 续写打字机，仅状态提示。

---

## 4. CLI 使用

```bash
cd cli && pip install -e .

ai-app --help
ai-app list
ai-app translate --text "Hello world" --from en --to zh
ai-app summarize --text "长文本…" --max-points 3 --word-limit 250
```

| 选项           | 说明         | 默认         |
| -------------- | ------------ | ------------ |
| `--max-points` | 总结要点数   | 3            |
| `--word-limit` | 概述字数上限 | 250          |
| `--tone`       | 语调         | Professional |

默认连接 `http://127.0.0.1:18765`（环境变量 `BASE_URL` 可覆盖）。**须先启动 Sidecar**。

---

## 5. 作为 Agent 工具被调用

技能描述文件：`.claude/skills/SKILL.md`

Claude Code 等 Agent 可发现 `ai-app` 命令并调用翻译/总结能力，也可直接 HTTP 调用 `/api/functions` + `/api/task`。

**前置条件：**

1. Sidecar 已启动（`npm run sidecar` 或 `npm run dev:all`）
2. 可选：`pip install -e cli/` 安装全局 `ai-app`

**示例对话：**

> 用户：把 "Good morning" 翻译成中文  
> Agent：执行 `ai-app translate --text "Good morning" --from en --to zh`

**笔试交付：** 需保存 Agent 发现并执行 CLI 的截图至 [`docs/verification/agent-skill-invoke.png`](./verification/README.md)（当前待补）。

---

## 6. 运行日志与 Agent Chat

### 运行日志

路径 `/history`，展示翻译/总结的输入摘要、输出、耗时与状态。

- 数据存于 Sidecar **进程内存**，环形缓冲最多 **500** 条，重启后重置（保留种子示例）
- API 支持分页：`GET /api/logs?page=1&size=20`
- 前端 HistoryView 支持「加载更多」（`workspace.loadMoreLogs`）

### Agent Chat

路径 `/chat`，通过 WebSocket `/ws/chat/{session_id}` 流式对话。需配置 `GLM_API_KEY` 或 `GEMINI_API_KEY`（与翻译/总结 SSE 管线独立）。Mock Agent 可演示 ReAct 步骤，无真实 Tool Calling。

---

## 7. 体验与工程

### 7.1 深色/浅色主题

Sidebar 底部点击 **太阳/月亮** 图标切换主题。选择持久化至 `localStorage`（键 **`adaworks-dark`**，`true` 为深色），刷新后保持。

实现层次：

1. `workspace.isDark` + `App.vue` 中 `a-config-provider` 切换 `theme.darkAlgorithm` / `defaultAlgorithm`
2. `useThemeAttribute` 同步 `document.documentElement[data-theme="dark"|"light"]`
3. `styles/theme.css` 提供页面语义 CSS 变量（Tailwind 自定义色引用 `--color-*`）

### 7.2 响应式布局

各页面使用 Tailwind 断点（`md:` 768px、`lg:` 1024px）。建议在以下宽度手动验收：

| 宽度    | 检查项                                       |
| ------- | -------------------------------------------- |
| 375px   | 移动端：Sidebar 折叠、双栏变单栏、按钮不溢出 |
| 768px   | 平板：网格列数切换正常                       |
| 1280px+ | 桌面：最大宽度 `max-w-6xl` 居中              |

验收截图说明见 [`docs/verification/`](./verification/README.md)。

### 7.3 流式渲染与错误处理

- **16ms 缓冲**：`useStreamBuffer` 批量 flush token，降低高频重渲染卡顿
- **SSE 乱序/去重**：`token.seq` + `seenSeqs` 防御网络抖动
- **断网 MVP**：流异常结束无 `task_done` 时提示「连接已断开，请重新提交」
- **HTTP 错误分级**：非法请求体返回标准 JSON（422 等）；响应含 `X-Request-ID`
- **单任务超时**：`TASK_TIMEOUT_SECONDS`（默认 60s）；僵尸任务 5 分钟 sweeper 清理

---

## 8. 相关文档

| 文档                                                                        | 说明                   |
| --------------------------------------------------------------------------- | ---------------------- |
| [README.md](../README.md)                                                   | 项目概览与 API 速查    |
| [spec/api-design.md](spec/api-design.md)                                    | API 完整规范           |
| [agent.md](../agent.md)                                                     | AI Agent 协作记录      |
| [.claude/skills/SKILL.md](../.claude/skills/SKILL.md)                       | CLI Agent 技能         |
| [docs/ai-native/](./ai-native/)                                             | 笔试需求与实现方案     |
| [docs/ai-native/exception-checklist.md](./ai-native/exception-checklist.md) | 异常场景 Checklist     |
| [docs/verification/](./verification/)                                       | 手动验收清单与截图目录 |
