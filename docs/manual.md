# AI TextFlow / Linguist AI — 系统使用手册

> 活文档：与 `implementation-tasks.md` 各任务「手册更新」章节对应。  
> 最后核对：2026-05-30

---

## 0. 快速开始

### 环境要求

- Node.js ≥ 18
- Python ≥ 3.10

### 安装与启动

```bash
git clone <repo-url> AdaAgent && cd AdaAgent
npm install
npm run sidecar:setup          # 创建 backend/.venv 并安装依赖
cp backend/.env.example backend/.env   # 或 cp .env.example .env
npm run dev:all
```

| 服务 | 地址 |
|------|------|
| 前端 Web UI | http://localhost:1420 |
| 后端 Sidecar | http://127.0.0.1:18765 |
| 健康检查 | http://127.0.0.1:18765/api/health |

验证 Sidecar：

```bash
curl -sf http://127.0.0.1:18765/api/functions
```

### Mock / Real 模式

| 模式 | 配置 | 说明 |
|------|------|------|
| `mock` | `LLM_MODE=mock`（默认） | 本地预设逐字流，零配置演示 |
| `real` | `LLM_MODE=real` + `GLM_API_KEY` | 调用智谱 GLM 流式接口 |

### Docker 一键启动（可选）

```bash
docker compose up --build
curl -sf http://127.0.0.1:18765/api/functions
```

### 运行测试

```bash
make test    # 后端 pytest + CLI + 前端 vitest
```

---

## 1. 产品概览

AdaAgent（Linguist AI）提供两条能力线：

1. **文本处理主线**：工作台 → 翻译 / 总结 → SSE 流式输出 → 停止生成 → 历史记录
2. **Agent Chat（加分）**：WebSocket 多轮对话，ReAct 步骤展示

---

## 2. 导航与页面入口

应用使用 **Vue Router 4**，Sidebar 左侧导航，浏览器后退/前进与刷新均保持当前页。

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | 重定向 | → `/dashboard` |
| `/dashboard` | 工作台 | 指标概览、功能卡片、快捷输入 |
| `/translation` | 文本翻译 | 10 语言 × 5 语调，双栏对照 |
| `/summarization` | 智能总结 | 要点数 / 字数 / 语调，结构化输出 |
| `/chat` | 智能体对话 | WebSocket Agent Chat |
| `/history` | 运行日志 | 翻译/总结调用记录 |
| `/settings` | 设置 | 应用设置 |

**快捷输入**：在工作台底部输入文本并发送，系统自动识别意图并跳转到翻译或总结页，文本预填至输入框。

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
2. 输入源文本，选择源语言、目标语言、语调
3. 点击 **开始翻译** — 结果区逐字流式输出（打字机效果）
4. 流式过程中可点击 **停止生成** 中断
5. 完成后可复制、下载；记录写入 **运行日志**

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

**SSE 事件序列：** `task_start` → `token`（多次）→ `task_done` / `task_error`

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 待翻译文本 |
| `sourceLang` | string | 否 | 源语言代码，默认 `zh` |
| `targetLang` | string | 否 | 目标语言代码，默认 `en` |
| `tone` | string | 否 | Professional / Conversational / Technical / Academic / Creative |

### 3.3 总结

#### 界面操作

1. 打开 **智能要点总结**（`/summarization`）
2. 粘贴文本或拖放 `.txt` / `.md` 文件
3. 调整概述字数上限、要点数量、语气风格
4. 点击 **生成总结** — 流式阶段显示原始 JSON，完成后解析为「概述 + 要点列表」
5. 可停止生成、复制、下载

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

### 3.4 停止生成

**界面：** 流式过程中点击 **停止生成** 按钮。

**API：**

```bash
# 从 task_start 事件获取 taskId
curl -X DELETE http://127.0.0.1:18765/api/task/{taskId}
```

前端会先 abort 本地 SSE 连接，再调用 DELETE 通知后端取消。

---

## 4. CLI 使用

```bash
cd cli && pip install -e .

ai-app --help
ai-app list
ai-app translate --text "Hello world" --from en --to zh
ai-app summarize --text "长文本…" --max-points 3 --word-limit 250
```

默认连接 `http://127.0.0.1:18765`，可通过环境变量 `BASE_URL` 覆盖。

---

## 5. 作为 Agent 工具被调用

技能描述文件：`.claude/skills/skill.md`

Claude Code 等 Agent 可发现 `ai-app` 命令并调用翻译/总结能力。

**前置条件：**

1. Sidecar 已启动（`npm run sidecar` 或 `npm run dev:all`）
2. 可选：`pip install -e cli/` 安装全局 `ai-app`

**示例对话：**

> 用户：把 "Good morning" 翻译成中文  
> Agent：执行 `ai-app translate --text "Good morning" --from en --to zh`

人工验收截图存放于 [`docs/verification/`](./verification/README.md)。

---

## 6. 运行日志与 Agent Chat

### 运行日志

路径 `/history`，展示翻译/总结的输入摘要、输出、耗时与状态。数据存于进程内存，重启后重置（保留种子示例）。

### Agent Chat

路径 `/chat`，通过 WebSocket `/ws/chat/{session_id}` 流式对话。需配置 `GLM_API_KEY` 或 `GEMINI_API_KEY`（与翻译/总结管线独立）。

---

## 7. 体验与工程

### 7.1 深色/浅色主题

Sidebar 底部点击 **太阳/月亮** 图标切换主题。选择持久化至 `localStorage`（键 `linguist-theme-dark`），刷新后保持。

实现：`App.vue` 中 `a-config-provider` 切换 `theme.darkAlgorithm` / `defaultAlgorithm`。

### 7.2 响应式布局

各页面使用 Tailwind 断点（`md:` 768px、`lg:` 1024px）。建议在以下宽度手动验收：

| 宽度 | 检查项 |
|------|--------|
| 375px | 移动端：Sidebar 折叠、双栏变单栏、按钮不溢出 |
| 768px | 平板：网格列数切换正常 |
| 1280px+ | 桌面：最大宽度 `max-w-6xl` 居中 |

验收截图说明见 [`docs/verification/`](./verification/README.md)。

### 7.3 错误处理与请求追踪

- 非法请求体返回标准 JSON 错误（HTTP 422 等）
- 每个 HTTP 响应含 `X-Request-ID` 头，便于日志关联
- 单任务超时由 `TASK_TIMEOUT_SECONDS` 控制（默认 60s）

---

## 8. 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目概览与 API 速查 |
| [spec/api-design.md](../spec/api-design.md) | API 完整规范 |
| [agent.md](../agent.md) | AI Agent 协作记录 |
| [.claude/skills/skill.md](../.claude/skills/skill.md) | CLI Agent 技能 |
| [docs/ai-native/](../ai-native/) | 笔试需求与实现方案 |
