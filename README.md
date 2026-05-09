# AdaAgent

本地运行的对话型智能体示例：**Vue 3 前端**通过 HTTP + WebSocket 与 **Python Sidecar（FastAPI）** 通信；Sidecar 负责会话持久化（SQLite）、调用大模型（智谱 GLM / Google Gemini，或 Mock），并以**流式**事件把生成过程推给浏览器。

适合边做边学：**前端状态与网络分层**、**异步 Web 框架**、**流式 SSE / 异步迭代器**、**环境变量与密钥管理**等。

**界面**：对话页采用薄荷绿主色（约 `#00A67E`）、浅灰绿画布（`#F7F9F8`）、深绿文案（`#004D3D`）与 **Think / Act / Observe** 分块样式；主题色与 Tailwind 扩展见 `frontend/tailwind.config.js` 中的 `arch.*` 色板与 `frontend/src/views/ChatView.vue` 布局。

---

## 一、仓库顶层目录

| 路径 | 作用 |
|------|------|
| `package.json` | 根级 npm 脚本：一键同时启动 Sidecar + Vite（`dev:all`） |
| `scripts/sidecar.mjs` | 用 Node 拉起 `uvicorn`：指定 `backend` 为工作目录、端口 `18765` |
| `frontend/` | **Vue 3 + Vite + TypeScript + Pinia + Ant Design Vue** 单页应用 |
| `backend/` | **Python 3.11+** Sidecar：`requirements.txt`、`adaagent` 包、单测 |
| `docs/` | 需求与设计文档（如 `spec.md`），与可运行代码相互对照阅读 |
| `data/db/` | 默认 SQLite 文件目录（运行时自动创建，勿把含隐私的 `.db` 提交仓库） |

---

## 二、后端模块 `backend/adaagent/`

| 文件 | 功能说明 |
|------|----------|
| `main.py` | **应用入口**：`create_app()` 注册路由；`lifespan` 里连接数据库、挂载 `ChatHub`；`POST /api/chat` 写入用户消息后**异步**启动 `run_glm_agent` / `run_gemini_agent` / `run_mock_agent`；`GET /api/health` 返回当前 LLM 模式（`glm` / `gemini` / `mock`） |
| `db.py` | **SQLite**：`connect()` 建表；`sessions` / `messages` 表结构；`row_to_session` / `row_to_message` 把查询行转成 API 用的字典 |
| `ws_hub.py` | **WebSocket 房间**：按 `session_id` 维护连接列表；`broadcast()` 向该会话所有客户端发送 `{ type, payload }` JSON 文本帧 |
| `bootstrap_env.py` | **环境变量**：依次加载仓库根 `.env` 与 `backend/.env`（后者覆盖同名键），便于密钥放在任意一层 |
| `env_secrets.py` | **密钥解析**：支持 `KEY="[\"a\",\"b\"]"` 形式把多段拼成一条字符串，兼容整条密钥 |
| `glm_agent.py` | **智谱 GLM**：OpenAI 兼容 `POST .../chat/completions`，`stream: true` 解析 **SSE**，逐段 `agent:delta`，结束 `agent:final` 并落库 |
| `gemini_agent.py` | **Google Gemini**：`google-genai` 异步 `generate_content_stream`，逐块 `chunk.text` → `agent:delta`，结束 `agent:final` 并落库 |
| `mock_agent.py` | **无 API Key 时**：模拟 ReAct 步骤（think/act/observe），最终回答也拆成多段 `agent:delta` 便于体验流式 UI |

**WebSocket 事件约定（与前端 `applyAgentEvent` 对齐）**

- `agent:delta`：增量正文 `{ "content": "..." }`
- `agent:final`：本轮流式结束，前端会重新拉取消息列表与 SQLite 对齐
- `agent:error`：错误说明
- `agent:think` / `agent:act` / `agent:observe`：主要由 Mock 使用

---

## 三、前端模块 `frontend/src/`（摘要）

| 路径 | 功能说明 |
|------|----------|
| `main.ts` | 应用入口：创建 Vue 应用、Pinia、路由、Ant Design Vue |
| `services/api.ts` | **HTTP**：`fetch` 调用 Sidecar 的 `/api/sessions`、`/api/chat` 等；`VITE_API_BASE` 指向 `http://127.0.0.1:18765/api` |
| `services/websocket.ts` | **纯函数**：根据 `VITE_WS_BASE` 拼出 `ws://.../ws/chat/{sessionId}` |
| `composables/useChatStream.ts` | **订阅 WebSocket**：随当前会话 ID 变化重连；`onmessage` 解析 JSON 后交给 Pinia |
| `stores/chat.ts` | **Pinia 状态**：会话列表、消息列表、`agent:delta` 拼接到同一条 assistant 气泡、`agent:final` 后 `loadMessages` |
| `types/chat.ts` | TypeScript 类型：会话、消息角色、API 请求/响应形状 |

---

## 四、启动手册

### 4.1 环境要求

- **Node.js** 18+（用于 Vite、npm 脚本）
- **Python** 3.11+（Sidecar；推荐在 `backend/` 下使用虚拟环境）

### 4.2 安装依赖

在仓库根目录 `AdaAgent/`：

```bash
npm install
npm run install
```

首次使用 Python 依赖（在 `backend` 创建 `.venv` 并安装包）：

```bash
npm run sidecar:setup
```

或手动：

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

### 4.3 配置密钥（二选一或同时配置，优先级见下）

在 **`backend/.env`** 或 **仓库根目录 `.env`** 中配置（详见 `backend/.env.example`）：

- **智谱 GLM（优先）**：`GLM_API_KEY` 或 `ZHIPU_API_KEY`
- **Gemini（未配置 GLM 时）**：`GEMINI_API_KEY` 或 `GOOGLE_API_KEY`

未配置任何密钥时，走 **Mock**，无需外网即可联调 UI。

### 4.4 启动开发环境

在仓库根目录：

```bash
npm run dev:all
```

- 前端：<http://localhost:1420/>（Vite 默认端口，见 `frontend/vite.config.ts`）
- Sidecar：<http://127.0.0.1:18765>

**仅启动后端**（调试 API）：

```bash
npm run sidecar
```

**仅启动前端**（需 Sidecar 已在别处运行）：

```bash
npm run dev
```

### 4.5 自检

浏览器或命令行访问：

```text
http://127.0.0.1:18765/api/health
```

期望 JSON 中含 `"status":"ok"`，且 `"llm"` 为 `glm`、`gemini` 或 `mock`。

### 4.6 生产构建（前端静态资源）

```bash
npm run build
```

---

## 五、边做边学：建议阅读顺序

1. `README.md`（本文）→ 建立全局地图  
2. `backend/adaagent/main.py` → 路由与异步任务如何触发模型  
3. `frontend/src/services/api.ts` + `useChatStream.ts` → HTTP 发消息与 WebSocket 收流式事件如何分工  
4. `backend/adaagent/glm_agent.py` 或 `gemini_agent.py` → 流式响应如何变成 `agent:delta`  
5. `docs/spec.md` → 产品层需求与当前实现的差距（扩展功能时的清单）

单测（后端）在 `backend/tests/`，可在 `backend` 目录执行：

```bash
.venv/bin/pytest tests/ -q
```

---

## 六、常见问题

| 现象 | 可能原因 |
|------|----------|
| 前端能开但发消息失败 | Sidecar 未启动或端口不是 `18765`；检查 `frontend/.env.development` 里 `VITE_API_BASE` / `VITE_WS_BASE` |
| `/api/health` 一直是 `mock` | `.env` 未加载或变量名写错；修改后需**重启** Sidecar |
| 改代码后模型行为没变 | Python 进程未重启；`npm run dev:all` 需整段 Ctrl+C 再启动 |

祝学习愉快。
