# AdaAgent - 桌面端智能体平台 需求规格文档

> 版本: v1.0
> 日期: 2026-05-09
> 状态: 规划阶段

---

## 1. 项目概述

### 1.1 产品定位

AdaAgent 是一个本地运行的桌面端 AI 智能体平台，用户通过自然语言与智能体交互，智能体能够自主思考、调用工具、检索知识库，并返回最终结果。

### 1.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 桌面框架 | **Tauri v2** | Rust 内核 + Web 前端，轻量高性能 |
| 前端 | **Vue 3 + TypeScript + Ant Design Vue + Tailwind CSS** | 组件与 Design Token 以 Ant Design Vue 为主；布局、间距、响应式与细粒度修饰可用 Tailwind 辅助 |
| 后端 | **Python (Sidecar)** | AI 逻辑、工具执行、数据处理 |
| AI 框架 | **LangChain** | Agent 编排、工具调用、RAG 管线 |
| 向量数据库 | **ChromaDB** | 本地嵌入数据库，RAG 知识检索 |
| 会话存储 | **SQLite** | 对话历史持久化，跨会话恢复 |
| 通信协议 | **HTTP + WebSocket** | 前后端通信，WebSocket 用于流式输出 |

### 1.3 目标平台

- macOS（首要支持）
- 架构后续可扩展 Windows / Linux

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                   Tauri v2 主进程                     │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │           Vue 3 前端 (WebView)                 │   │
│  │                                                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │   │
│  │  │ 对话界面  │ │ 设置面板  │ │ 知识库管理    │  │   │
│  │  └──────────┘ └──────────┘ └───────────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │   │
│  │  │ 技能管理  │ │ MCP 管理 │ │ 模型切换      │  │   │
│  │  └──────────┘ └──────────┘ └───────────────┘  │   │
│  └───────────────────┬───────────────────────────┘   │
│                      │ HTTP / WebSocket              │
│                      │ (localhost)                    │
│  ┌───────────────────┴───────────────────────────┐   │
│  │         Python Sidecar 后端                     │   │
│  │                                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │   │
│  │  │ Agent    │  │ Tool     │  │ RAG         │  │   │
│  │  │ Engine   │  │ Manager  │  │ Pipeline    │  │   │
│  │  └──────────┘  └──────────┘  └─────────────┘  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │   │
│  │  │ Model    │  │ Skill    │  │ MCP         │  │   │
│  │  │ Manager  │  │ Runner   │  │ Client      │  │   │
│  │  └──────────┘  └──────────┘  └─────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │                    │               │
   ┌────┴────┐         ┌────┴────┐    ┌─────┴─────┐
   │ SQLite  │         │ChromaDB │    │ MCP       │
   │ (会话)   │         │ (向量)   │    │ Servers   │
   └─────────┘         └─────────┘    └───────────┘
```

### 2.2 通信流程

```
用户输入 → Vue前端 → HTTP POST /api/chat → Python后端
                                           │
                                           ├→ Agent Engine 解析意图
                                           ├→ ReAct 循环（思考→行动→观察）
                                           │   ├→ 调用 Tool / Skill / RAG / MCP
                                           │   └→ WebSocket 推送中间步骤到前端
                                           │
                                           └→ HTTP Response 返回最终结果
                                              + WebSocket 流式推送过程
```

### 2.3 项目目录结构

**当前仓库约定**：业务实现代码分两层目录——**`frontend/`** 存放前端（Vue + Vite 等），**`backend/`** 存放 Python Sidecar。下述树状图中根下的 `src/` 逻辑上对应 **`frontend/src/`**；原 `python/` 对应 **`backend/`**（树中已写为 `backend/`）。

```
AdaAgent/
├── docs/
│   ├── spec.md                      # 需求规格（本文档）
│   ├── plan.md                      # 架构与 SRP 约定、示例代码骨架
│   └── task.md                      # 按 plan 拆解的实现任务清单
├── CLAUDE.md                        # Claude Code 指引
│
├── src-tauri/                       # Tauri v2 后端 (Rust)
│   ├── Cargo.toml
│   ├── tauri.conf.json              # Tauri 配置（含 sidecar 声明）
│   ├── capabilities/                # Tauri v2 权限配置
│   ├── src/
│   │   ├── main.rs                  # Tauri 入口
│   │   └── lib.rs                   # Tauri 初始化逻辑
│   └── icons/                       # 应用图标
│
├── frontend/                        # 前端工程（Vue3 + Vite + TS + Ant Design Vue + Tailwind）
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/                         # 应用源码：components、views、stores、services、types、router、assets 等（结构见上文逻辑树）
│
├── backend/                         # Python Sidecar（HTTP + WebSocket；实现代码集中于此）
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── adaagent/                    # FastAPI 应用包（main、db、mock_agent、ws_hub 等）
│   └── tests/
│   （规划中扩展：core/、tools/、rag/、mcp/、storage/、api/ 等子包，分层见原规格）
│
├── data/                            # 运行时数据目录（gitignore）
│   ├── db/                          # SQLite 数据库文件
│   ├── chroma/                      # ChromaDB 数据
│   ├── uploads/                     # 上传的文档
│   └── skills/                      # 用户自定义技能
│
├── package.json                     # 仓库根：一键脚本（如 dev:all、sidecar）；前端依赖在 frontend/package.json
├── scripts/                         # 辅助脚本（如启动 Sidecar）
└── .gitignore
```

---

## 3. 功能需求

### 3.1 对话系统

#### 3.1.1 基本问答

- 用户输入自然语言问题，智能体返回回答
- 支持流式输出（打字机效果），通过 WebSocket 实时推送
- 支持 Markdown 渲染，包含代码高亮
- 支持代码块一键复制

#### 3.1.2 ReAct 交互循环

智能体采用 ReAct (Reasoning + Acting) 模式：

```
用户问题
  │
  ▼
┌─────────────┐
│  思考 Think  │ ◄── Agent 分析问题，决定下一步行动
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  行动 Act    │ ◄── Agent 调用工具/技能/RAG/MCP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 观察 Observe │ ◄── 获取工具执行结果
└──────┬──────┘
       │
       ├── 结果不足，继续循环 ──→ 回到 Think
       │
       ├── 结果充足
       │       │
       ▼       ▼
┌──────────────┐
│ 最终结果      │ ◄── 整合所有信息，返回最终回答
└──────────────┘
```

**前端展示要求：**

| 步骤 | 展示样式 | 说明 |
|------|----------|------|
| Think | 可折叠卡片，默认展开，半透明背景 | 显示 Agent 的推理过程 |
| Act | 带工具图标的操作卡片 | 显示调用了哪个工具、参数是什么 |
| Observe | 代码块样式的结果卡片 | 显示工具返回的结果 |
| 最终结果 | 普通消息气泡，Markdown 渲染 | 最终回答 |

**循环控制：**
- 最大循环次数：可配置，默认 10 次
- 超过限制时自动中断并返回已有结果
- 用户可手动中断执行

#### 3.1.3 会话管理

- 支持多会话，左侧侧边栏显示会话列表
- 会话自动命名（取用户第一条消息前 20 字符）
- 支持新建、删除、重命名会话
- 会话历史持久化到 SQLite，重启后恢复
- 支持清空当前会话

### 3.2 模型管理

#### 3.2.1 支持的模型类型

| 模型类型 | Provider | 说明 |
|----------|----------|------|
| Google Gemini | google | Gemini 系列模型（首要接入，开发阶段优先使用）|
| OpenAI 兼容 | openai | GPT-4 / GPT-3.5 以及所有 OpenAI 兼容接口 |
| Claude | anthropic | Claude 系列模型 |
| Ollama (本地) | ollama | 本地部署的开源模型 |
| Mock (测试) | mock | 不需要 API Key，返回预设回复，用于开发测试 |

#### 3.2.2 模型切换

- 设置面板中可配置多个模型
- 每个模型需要配置：名称、Provider 类型、API Key、Base URL（可选）、模型 ID
- 对话界面顶部可快速切换当前使用的模型
- 切换模型不影响当前对话上下文

#### 3.2.3 Mock 模型

Mock 模型用于开发测试阶段，行为如下：

- 收到消息后，模拟 ReAct 循环过程
- 返回预设的思考、行动、观察步骤
- 最终返回一个示例回答
- 延迟 0.5-1 秒模拟网络请求

### 3.3 工具系统

#### 3.3.1 内置工具

| 工具名称 | 功能 | 参数 | 安全限制 |
|----------|------|------|----------|
| `file_read` | 读取文件内容 | `path: str` 文件路径 | 限制在工作目录内，禁止读取系统敏感文件 |
| `file_write` | 写入文件 | `path: str`, `content: str` | 限制在工作目录内，覆盖前需确认 |
| `terminal_execute` | 执行终端命令 | `command: str` 命令字符串 | 黑名单机制：禁止 `rm -rf /`、`sudo` 等危险命令；设置超时时间（默认 30 秒）|

#### 3.3.2 工具安全机制

- **工作目录隔离**：文件操作限定在用户指定的工作目录中
- **命令黑名单**：终端执行维护一个禁止命令列表
- **超时控制**：所有工具执行有超时限制，防止挂起
- **执行确认**：高风险操作（如文件覆盖、终端命令）在前端弹出确认框
- **用户可配置**：用户可以在设置中调整安全策略（工作目录路径、黑名单等）

### 3.4 RAG 知识库

#### 3.4.1 文档管理

- 支持上传文档：PDF、TXT、Markdown、DOCX
- 文档自动分块（chunking）
- 支持查看已上传文档列表
- 支持删除已上传文档
- 文档存储在本地 `data/uploads/` 目录

#### 3.4.2 索引与检索流程

```
上传文档 → 文档加载 → 文本分块 → 向量嵌入 → 存入 ChromaDB

用户提问 → 问题向量嵌入 → ChromaDB 相似度检索 → Top-K 结果
         → 将检索结果作为上下文注入 Agent → 生成回答
```

#### 3.4.3 分块策略

- 默认分块大小：500 字符
- 分块重叠：50 字符
- 分块参数可在设置中调整
- 支持按段落智能分块

#### 3.4.4 嵌入模型

- 默认使用 OpenAI Embedding（text-embedding-3-small）
- 支持配置其他嵌入模型
- 本地模式可使用 Ollama 的嵌入模型

### 3.5 技能系统 (Skills)

#### 3.5.1 概念

技能是一组预定义的工作流，封装了特定的任务逻辑。用户可以通过自然语言触发技能。

#### 3.5.2 技能定义

每个技能包含：

```yaml
name: "代码审查"              # 技能名称
description: "审查代码质量"    # 技能描述（用于匹配）
trigger: ["审查代码", "review"] # 触发关键词
prompt_template: "..."         # 注入给 Agent 的提示模板
tools: ["file_read"]           # 该技能可用的工具
```

#### 3.5.3 技能管理

- 内置几个示例技能（代码审查、文档生成等）
- 用户可在 `data/skills/` 目录下创建自定义技能（YAML 格式）
- 技能面板中显示所有可用技能
- 用户可启用/禁用技能

### 3.6 MCP (Model Context Protocol)

#### 3.6.1 客户端模式

AdaAgent 作为 MCP Client，可连接外部 MCP Server 获取额外能力。

#### 3.6.2 支持的传输方式

| 传输方式 | 说明 | 适用场景 |
|----------|------|----------|
| stdio | 通过标准输入/输出通信 | 本地 MCP Server |
| SSE (Server-Sent Events) | 通过 HTTP SSE 通信 | 远程 MCP Server |

#### 3.6.3 MCP 管理功能

- 添加 MCP Server 连接配置（名称、传输方式、命令/URL）
- 启动/停止 MCP Server 连接
- 查看已连接 Server 提供的工具列表
- 启用/禁用特定 MCP 工具
- Agent 自动发现并调用 MCP 提供的工具

#### 3.6.4 配置示例

```json
{
  "mcpServers": [
    {
      "name": "文件系统",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
      "enabled": true
    },
    {
      "name": "远程搜索",
      "transport": "sse",
      "url": "http://localhost:3001/sse",
      "enabled": true
    }
  ]
}
```

---

## 4. UI/UX 设计

### 4.1 设计风格

参考 apple.com 设计语言：

- **简洁**：大量留白，内容层次清晰
- **统一**：一致的间距、圆角、阴影
- **科技感**：深色模式为主，精致的动画过渡
- **字体**：SF Pro 风格，中文使用系统默认

### 4.2 色彩方案

```
背景色系：
  主背景      #000000 / #0A0A0A (纯黑/深灰黑)
  卡片背景    #1C1C1E
  侧边栏背景  #161618
  悬停背景    #2C2C2E

文字色系：
  主文字      #F5F5F7 (苹果白)
  次要文字    #86868B (苹果灰)
  强调文字    #10B981 (翡翠绿)

功能色：
  思考 (Think)      #BF5AF2 (紫色)
  行动 (Act)        #FF9F0A (橙色)
  观察 (Observe)    #30D158 (绿色)
  最终结果          #10B981 (翡翠绿)

边框：
  默认边框    rgba(255,255,255,0.08)
  悬停边框    rgba(255,255,255,0.15)
```

### 4.3 布局结构

```
┌──────────────────────────────────────────────────┐
│  AdaAgent          [模型选择 ▼]          [⚙ 设置] │  ← 顶部导航栏 (h: 52px)
├────────┬─────────────────────────────────────────┤
│        │                                          │
│ 会话1  │    对话消息区域                            │
│ 会话2  │                                          │
│ 会话3  │    ┌──────────────────────┐              │
│        │    │ Think: 分析用户需求    │              │
│ ────── │    └──────────────────────┘              │
│ 知识库 │    ┌──────────────────────┐              │
│ 技能   │    │ ACT: file_read       │              │
│ MCP    │    └──────────────────────┘              │
│        │    ┌──────────────────────┐              │
│        │    │ OBSERVE: 文件内容...  │              │
│ [+新建]│    └──────────────────────┘              │
│        │                                          │
│        │    ┌──────────────────────┐              │
│        │    │ 最终结果              │              │
│        │    └──────────────────────┘              │
│        │                                          │
│        ├──────────────────────────────────────────┤
│        │  [附件📎]  输入消息...          [发送 ➤]   │  ← 输入栏
├────────┴──────────────────────────────────────────┤
│  状态栏：Agent 就绪 | 模型: GPT-4 | 工具: 3 个就绪   │  ← 底部状态栏
└──────────────────────────────────────────────────┘
     │                                                │
     └── 侧边栏 w: 240px，可折叠                       │
```

### 4.4 组件设计规范

#### 消息气泡

```
用户消息：右对齐，圆角 18px，背景 #10B981，白色文字
AI 消息：  左对齐，圆角 18px，背景 #1C1C1E，浅色文字
```

#### ReAct 步骤卡片

```
┌─ 💭 Think ──────────────────────── ──┐
│ 分析用户的需求，需要读取配置文件...     │  ← 可折叠，左侧有紫色竖线
└──────────────────────────────────────┘

┌─ ⚡ Act: file_read ─────────────────┐
│ 参数: path = "/project/config.json" │  ← 左侧有橙色竖线，显示工具名和参数
└──────────────────────────────────────┘

┌─ 👁 Observe ────────────────────────┐
│ { "name": "my-project", ... }      │  ← 左侧有绿色竖线，代码块样式
└──────────────────────────────────────┘
```

#### 动画效果

- 消息出现：淡入 + 轻微上移 (fade-in-up, 200ms)
- ReAct 步骤展开：高度动画 (200ms)
- 思考中状态：呼吸灯效果的省略号动画
- 模型切换：平滑过渡
- 侧边栏折叠/展开：宽度动画 (300ms)
- 按钮/卡片悬停：轻微缩放 + 阴影变化

---

## 5. API 接口设计

### 5.1 HTTP API

基础路径: `http://localhost:{port}/api`

#### 对话接口

```
POST /api/chat
  请求: { session_id: string, message: string, model_id: string }
  响应: { session_id: string, message_id: string }
  说明: 发送消息，Agent 开始 ReAct 循环，过程通过 WebSocket 推送

GET /api/sessions
  响应: { sessions: Session[] }
  说明: 获取会话列表

POST /api/sessions
  请求: { title?: string }
  响应: { session: Session }
  说明: 创建新会话

DELETE /api/sessions/:id
  响应: { success: boolean }
  说明: 删除会话

GET /api/sessions/:id/messages
  响应: { messages: Message[] }
  说明: 获取会话消息历史
```

#### 模型接口

```
GET /api/models
  响应: { models: ModelConfig[] }
  说明: 获取已配置的模型列表

POST /api/models
  请求: { name, provider, api_key?, base_url?, model_id }
  响应: { model: ModelConfig }
  说明: 添加模型配置

PUT /api/models/:id
  请求: { name?, api_key?, base_url?, ... }
  响应: { model: ModelConfig }
  说明: 更新模型配置

DELETE /api/models/:id
  响应: { success: boolean }
  说明: 删除模型配置

POST /api/models/:id/test
  响应: { success: boolean, message: string }
  说明: 测试模型连接
```

#### 知识库接口

```
POST /api/knowledge/upload
  请求: multipart/form-data, file 字段
  响应: { document: Document }
  说明: 上传文档到知识库

GET /api/knowledge/documents
  响应: { documents: Document[] }
  说明: 获取已上传文档列表

DELETE /api/knowledge/documents/:id
  响应: { success: boolean }
  说明: 删除文档及索引

POST /api/knowledge/search
  请求: { query: string, top_k?: number }
  响应: { results: SearchResult[] }
  说明: 知识库检索
```

#### 技能接口

```
GET /api/skills
  响应: { skills: Skill[] }
  说明: 获取所有技能

PUT /api/skills/:id/toggle
  响应: { skill: Skill }
  说明: 启用/禁用技能
```

#### MCP 接口

```
GET /api/mcp/servers
  响应: { servers: McpServer[] }
  说明: 获取 MCP Server 配置列表

POST /api/mcp/servers
  请求: { name, transport, command?, args?, url? }
  响应: { server: McpServer }
  说明: 添加 MCP Server 配置

POST /api/mcp/servers/:id/start
  响应: { success: boolean, tools: Tool[] }
  说明: 启动 MCP Server 连接

POST /api/mcp/servers/:id/stop
  响应: { success: boolean }
  说明: 停止 MCP Server 连接

DELETE /api/mcp/servers/:id
  响应: { success: boolean }
  说明: 删除 MCP Server 配置
```

### 5.2 WebSocket 事件

连接地址: `ws://localhost:{port}/ws/chat/{session_id}`

```
# 服务端 → 客户端 事件

agent:think       { content: string }              # 思考过程
agent:act         { tool: string, params: object } # 行动（调用工具）
agent:observe     { result: string }               # 观察结果
agent:final       { content: string }              # 最终结果
agent:error       { message: string }              # 错误信息
agent:stream      { content: string }              # 流式文本（逐字推送）

# 客户端 → 服务端 事件

user:interrupt    {}                                # 用户中断执行
```

---

## 6. 数据模型

### 6.1 会话 (Session)

```sql
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,    -- UUID
    title       TEXT NOT NULL,       -- 会话标题
    model_id    TEXT,                -- 当前使用的模型 ID
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 消息 (Message)

```sql
CREATE TABLE messages (
    id          TEXT PRIMARY KEY,    -- UUID
    session_id  TEXT NOT NULL,       -- 所属会话
    role        TEXT NOT NULL,       -- 'user' | 'assistant' | 'think' | 'act' | 'observe'
    content     TEXT NOT NULL,       -- 消息内容
    metadata    TEXT,                -- JSON: 工具名、参数、额外信息
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

### 6.3 模型配置 (Model Config)

```sql
CREATE TABLE model_configs (
    id          TEXT PRIMARY KEY,    -- UUID
    name        TEXT NOT NULL,       -- 显示名称
    provider    TEXT NOT NULL,       -- 'openai' | 'anthropic' | 'ollama' | 'mock'
    model_id    TEXT NOT NULL,       -- 模型标识 (如 gpt-4, claude-3-sonnet)
    api_key     TEXT,                -- 加密存储的 API Key
    base_url    TEXT,                -- 自定义 API 地址
    is_default  INTEGER DEFAULT 0,  -- 是否默认模型
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.4 文档 (Document)

```sql
CREATE TABLE documents (
    id          TEXT PRIMARY KEY,    -- UUID
    filename    TEXT NOT NULL,       -- 原始文件名
    file_path   TEXT NOT NULL,       -- 本地存储路径
    file_type   TEXT NOT NULL,       -- 'pdf' | 'txt' | 'md' | 'docx'
    chunk_count INTEGER DEFAULT 0,  -- 分块数量
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.5 MCP Server 配置

```sql
CREATE TABLE mcp_servers (
    id          TEXT PRIMARY KEY,    -- UUID
    name        TEXT NOT NULL,       -- 显示名称
    transport   TEXT NOT NULL,       -- 'stdio' | 'sse'
    command     TEXT,                -- stdio 传输的启动命令
    args        TEXT,                -- JSON: 命令参数列表
    url         TEXT,                -- SSE 传输的服务地址
    enabled     INTEGER DEFAULT 1,  -- 是否启用
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. 开发计划

### 阶段一：基础骨架 (MVP)

> 目标：能跑通基本对话流程

- [ ] 初始化 Tauri v2 + Vue 3 + TS + Ant Design Vue + Tailwind 项目
- [ ] Python Sidecar 基础框架 (FastAPI)
- [ ] 前后端通信 (HTTP + WebSocket)
- [ ] Mock 模型实现
- [ ] 基本对话界面（发送消息，接收回复）
- [ ] ReAct 循环核心逻辑（Think → Act → Observe）
- [ ] 前端 ReAct 步骤展示组件
- [ ] SQLite 会话持久化

### 阶段二：工具与模型

> 目标：接入真实模型和工具

- [ ] OpenAI / Claude 模型接入
- [ ] Ollama 本地模型接入
- [ ] 模型切换 UI
- [ ] file_read / file_write / terminal_execute 工具实现
- [ ] 工具安全机制
- [ ] 工具执行确认弹窗

### 阶段三：RAG 知识库

> 目标：文档上传和检索

- [ ] 文档上传和解析 (PDF/TXT/MD/DOCX)
- [ ] 文档分块处理
- [ ] ChromaDB 向量存储
- [ ] 相似度检索
- [ ] RAG 注入 Agent 上下文
- [ ] 知识库管理界面

### 阶段四：技能与 MCP

> 目标：扩展能力

- [ ] 技能系统框架
- [ ] 技能加载与注册
- [ ] 内置示例技能
- [ ] MCP Client 实现 (stdio)
- [ ] MCP Client 实现 (SSE)
- [ ] MCP Server 管理界面
- [ ] MCP 工具自动发现和调用

### 阶段五：打磨优化

> 目标：体验优化

- [ ] UI 动画和过渡效果
- [ ] 错误处理和用户提示优化
- [ ] 性能优化
- [ ] 快捷键支持
- [ ] 应用打包和分发

---

## 8. 技术约束与约定

### 8.1 代码规范

- **所有代码必须添加中文注释**，说明模块用途、函数功能、关键逻辑
- Python 使用 type hints
- TypeScript 严格模式
- 组件使用 `<script setup lang="ts">` 语法
- **Ant Design Vue**：表单、表格、反馈、导航等标准交互与主题 Token
- **Tailwind CSS**：页面级布局（flex/grid）、间距、响应式断点、Ant 未覆盖的微调类名
- 二者 reset 可能重叠：优先在 `tailwind.config.js` 关闭 `preflight`，由 Ant Design Vue 样式承担基础归一化（详见 [plan.md](./plan.md) §5.0，与本文档同目录）；避免用 Tailwind 重绘 Ant 组件内部结构

### 8.2 端口约定

| 服务 | 默认端口 | 说明 |
|------|----------|------|
| Python Sidecar | 18765 | HTTP + WebSocket 服务 |
| Vite Dev | 1420 | 前端开发服务器 |

### 8.3 数据存储

所有运行时数据存放在项目根目录 `data/` 下：

```
data/
├── db/adaagent.db       # SQLite 数据库
├── chroma/              # ChromaDB 向量数据
├── uploads/             # 上传文档
└── skills/              # 用户自定义技能 YAML
```

### 8.4 Sidecar 管理策略

- Tauri 启动时自动拉起 Python Sidecar 进程
- 前端通过 Sidecar 状态检测确认后端就绪
- Tauri 关闭时自动清理 Sidecar 进程
- Sidecar 崩溃时自动重启（最多重试 3 次）
- Python 依赖使用虚拟环境管理

---

## 9. 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 首屏加载 < 2s，消息发送响应 < 500ms（不含模型推理） |
| 内存 | 常驻内存 < 200MB（不含模型推理） |
| 安全 | API Key 加密存储，文件操作限制在工作目录 |
| 可靠性 | Sidecar 崩溃自动恢复，数据不丢失 |
| 可维护性 | 模块化设计，新工具/技能可热插拔 |
| 体验 | Apple 级别的 UI 流畅度和一致性 |
