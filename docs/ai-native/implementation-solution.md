# AI TextFlow — 技术实现方案

> 基于 [plan.md](./plan.md) 的落地实现指南，面向 3 天交付
> 技术栈：Vue 3 + TypeScript + Vite + Ant Design Vue + Tailwind + FastAPI + Python Click
> **在现有 AdaWorks /AdaWorks AI代码上增量改造**，UI 样式保留，底层接入 SSE task 契约。

### 改造原则（与 plan.md §〇 对齐）

| 原则       | 说明                                                                               |
| ---------- | ---------------------------------------------------------------------------------- |
| UI 不动    | 保留 `DashboardView` / `TranslationView` / `SummarizationView` 等现有页面样式      |
| Vue Router | `activeView` → Vue Router 4 + `<router-view>`；跨页状态进 `stores/workspace.ts`    |
| 多语言翻译 | task `type: translate`，params 含 `sourceLang/targetLang/tone`（10 语言 + 5 语调） |
| 后端增量   | 在 `backend/adaworks/` 包内新增 `config.py`、`services/`、`api/`                   |
| 主题       | Ant Design Vue `a-config-provider` 切换 `darkAlgorithm` / `defaultAlgorithm`       |

### 交付范围说明

本期实现 **Step 0–6**（Router 迁移 + 核心 SSE + CLI + 主题 + 文档），以下项标注为后续或可选：

| 项                 | 说明                                                      |
| ------------------ | --------------------------------------------------------- |
| 统一错误处理中间件 | `middleware/error_handler.py`，加分项，可增量接入         |
| Docker 部署        | `Dockerfile` + `docker-compose.yml`，加分项               |
| Agent Chat         | **已有**，保留为加分展示（WebSocket 流式），本期不改造    |
| HistoryView        | **已有**（内存日志），保留现状，SSE 完成后写入同一套 logs |

---

## 一、项目初始化

### 1.1 仓库结构（现有 AdaWorks，增量扩展）

```
AdaWorks/
├── frontend/              # 现有 Vue 3 + Ant Design Vue + Tailwind
├── backend/adaworks/      # 现有 FastAPI 包，增量新增 services/ api/
├── cli/                   # 新增
├── .claude/skills/        # 新增 SKILL.md
├── docs/docs/spec/              # 新增规范目录
├── scripts/sidecar.mjs    # 已有 — 启动 Sidecar :18765
└── README.md
```

### 1.2 后端依赖追加

在现有 `backend/requirements.txt` 追加：

```
pydantic-settings>=2.*
sse-starlette>=2.*
```

### 1.3 前端依赖追加

在现有 `frontend/package.json` 追加：

```bash
cd frontend && npm install vue-router@4
```

> UI 栈为 **Ant Design Vue + Tailwind CSS + lucide-vue-next**（已有），不新建 Vite 工程。

### 1.4 环境变量设计

**根目录 `.env.example`**

```env
# 后端
LLM_MODE=mock                          # mock | real
LLM_API_KEY=                           # 真实模式时填写
LLM_API_BASE=https://api.deepseek.com  # OpenAI 兼容 API 地址
LLM_MODEL=deepseek-chat                # 模型名
TASK_TIMEOUT_SECONDS=60                # 任务超时时间

# 前端（Sidecar 默认 18765，见 frontend/.env.development）
VITE_API_BASE=http://127.0.0.1:18765/api
```

---

## 二、后端实现（FastAPI）

### 2.1 应用入口 — 在 `backend/adaworks/main.py` 挂载新路由

在现有 `create_app()` 中 `include_router(api_router, prefix="/api")`，**保留** sessions/chat/logs/health 等已有路由。

新增模块位于 `backend/adaworks/api/router.py`，聚合 `functions` 与 `task` 子路由。

### 2.2 配置管理 — `backend/adaworks/config.py`

使用 `pydantic-settings` 读取环境变量，统一管理所有配置项。

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_mode: str = "mock"              # mock | real
    llm_api_key: str = ""
    llm_api_base: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    task_timeout_seconds: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2.3 LLM 调用层 — `backend/adaworks/services/llm.py`

核心设计：统一的 `AsyncIterator[str]` 接口，mock/real 通过 `config.settings.llm_mode` 切换。

```python
import asyncio
from typing import AsyncIterator
from config import settings

class LLMService:
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        if settings.llm_mode == "mock":
            async for token in self._mock_stream(prompt):
                yield token
        else:
            async for token in self._real_stream(prompt):
                yield token

    async def _mock_stream(self, prompt: str) -> AsyncIterator[str]:
        """Mock 模式：逐字返回预设文本"""
        # 判断是翻译还是总结，返回不同的 mock 内容
        if "翻译" in prompt or "translate" in prompt.lower():
            mock_text = "This is a mock translation result for demonstration purposes."
        else:
            mock_text = "1. 这是第一个要点\n2. 这是第二个要点\n3. 这是第三个要点"
        for char in mock_text:
            yield char
            await asyncio.sleep(0.05)  # 模拟逐字输出

    async def _real_stream(self, prompt: str) -> AsyncIterator[str]:
        """真实模式：调用 OpenAI 兼容 API"""
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{settings.llm_api_base}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                },
                timeout=60.0,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content

llm_service = LLMService()
```

### 2.4 Prompt 模板 — `backend/adaworks/services/prompt.py`

承接现有 `linguist_service.py` 的 system prompt 逻辑：

```python
def build_translate_prompt(text: str, source_lang: str, target_lang: str, tone: str = "Professional") -> str:
    """多语言翻译 prompt；source_lang 可为 auto"""
    ...

def build_summarize_prompt(text: str, key_points_count: int = 5, word_limit: int = 250, tone: str = "Professional") -> str:
    """总结 prompt，与 SummarizationView 参数对齐"""
    ...
```

### 2.5 任务管理器 — `backend/adaworks/services/task_manager.py`

纯内存字典，`asyncio.Task` 引用实现取消。不做过度设计。

```python
import asyncio
import uuid
from enum import Enum
from dataclasses import dataclass, field

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskContext:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    async_task: asyncio.Task | None = field(default=None, repr=False)

class TaskManager:
    def __init__(self):
        self._tasks: dict[str, TaskContext] = {}

    def create(self) -> str:
        task_id = uuid.uuid4().hex[:12]
        self._tasks[task_id] = TaskContext(task_id=task_id)
        return task_id

    def get(self, task_id: str) -> TaskContext | None:
        return self._tasks.get(task_id)

    def cancel(self, task_id: str) -> bool:
        ctx = self._tasks.get(task_id)
        if ctx and ctx.async_task and not ctx.async_task.done():
            ctx.async_task.cancel()
            ctx.status = TaskStatus.CANCELLED
            return True
        return False

task_manager = TaskManager()
```

### 2.6 API 路由 — `backend/api/`

#### `router.py` — 总路由聚合

```python
from fastapi import APIRouter
from api.functions import router as functions_router
from api.task import router as task_router

api_router = APIRouter()
api_router.include_router(functions_router)
api_router.include_router(task_router)
```

#### `schemas.py`

```python
class TaskCreateRequest(BaseModel):
    type: str                          # translate | summarize
    params: dict                       # 见下方 params 约定

class FunctionItem(BaseModel):
    id: str
    name: str
    description: str
    params: dict | None = None
```

#### `functions.py` — GET /api/functions [F6]

返回 **translate + summarize** 两项（供 CLI / SKILL.md；前端工作台不消费）：

```python
FUNCTIONS = [
    FunctionItem(id="translate", name="文本翻译", description="多语言翻译，支持源/目标语言与语调", params={...}),
    FunctionItem(id="summarize", name="智能要点总结", description="长文本总结，支持要点数/字数/语调", params={...}),
]
```

#### `task.py` — POST /api/task (SSE) [F7] + DELETE [F8]

```python
@router.post("/task")
async def create_task(req: TaskCreateRequest):
    task_id = task_manager.create()
    text = req.params.get("text", "")

    if req.type == "translate":
        prompt = build_translate_prompt(
            text,
            req.params.get("sourceLang", "auto"),
            req.params.get("targetLang", "zh"),
            req.params.get("tone", "Professional"),
        )
    elif req.type == "summarize":
        prompt = build_summarize_prompt(
            text,
            req.params.get("keyPointsCount", 5),
            req.params.get("wordLimit", 250),
            req.params.get("tone", "Professional"),
        )
    else:
        raise HTTPException(status_code=400, detail="unknown task type")

    return EventSourceResponse(_task_generator(task_id, prompt, req.type))
```

> 任务结束时调用 `linguist_service.add_log` / `update_log` 写入 History；总结类 `task_done.result` 携带 `{overview, keyPoints}`。

---

## 三、前端实现（基于现有 AdaWorks AI，UI 不动）

### 3.1 Vite 配置 — `frontend/vite.config.ts`

现有 Sidecar 端口 **18765**；若需 dev proxy 可加：

```typescript
server: {
  port: 1420,
  proxy: {
    '/api': { target: 'http://127.0.0.1:18765', changeOrigin: true },
  },
},
```

### 3.2 路由 — `frontend/src/router/index.ts` [F0]

```typescript
import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("../components/DashboardView.vue"),
    },
    {
      path: "/translation",
      name: "translation",
      component: () => import("../components/TranslationView.vue"),
    },
    {
      path: "/summarization",
      name: "summarization",
      component: () => import("../components/SummarizationView.vue"),
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("../views/ChatView.vue"),
    },
    {
      path: "/history",
      name: "history",
      component: () => import("../components/HistoryView.vue"),
    },
    {
      path: "/settings",
      name: "settings",
      component: () => import("../components/SettingsView.vue"),
    },
  ],
});

export default router;
```

`main.ts` 增加 `app.use(router)`；`App.vue` 主内容区改为 `<router-view />`，移除 `activeView` / `<component :is>`。

### 3.3 跨页状态 — `frontend/src/stores/workspace.ts`

从 `App.vue` props 下沉：

```typescript
export const useWorkspaceStore = defineStore('workspace', () => {
  const logs = ref<LogEntry[]>([])
  const quickText = ref('')
  const apiConnected = ref(false)
  // handleAddLog / handleUpdateLog / fetchHealth / fetchLogs ...
  return { logs, quickText, apiConnected, ... }
})
```

各 View 通过 store 读写，不再经 App 透传 props。

### 3.4 API 层 — 改造 `frontend/src/services/linguistApi.ts`

在现有 `translate()` / `summarize()` 旁新增 task 契约方法；迁移完成后移除旧 POST 接口调用：

```typescript
export async function getFunctions() {
  const res = await fetch(`${API_BASE}/functions`);
  return res.json(); // { functions: FunctionItem[] }
}

export function createTaskSSE(body: {
  type: string;
  params: Record<string, unknown>;
}) {
  return fetch(`${API_BASE}/task`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function cancelTask(taskId: string) {
  return fetch(`${API_BASE}/task/${taskId}`, { method: "DELETE" });
}
```

task 参数约定：

- `translate`: `{ text, sourceLang, targetLang, tone? }`
- `summarize`: `{ text, keyPointsCount?, wordLimit?, tone? }`

### 3.5 Composables — `frontend/src/composables/`

#### `useSSE.ts` [F4] — 核心 composable

```typescript
import { ref } from "vue";

export function useSSE() {
  const result = ref("");
  const isStreaming = ref(false);
  const error = ref("");
  const currentTaskId = ref("");
  let abortController: AbortController | null = null;

  async function startSSE(url: string, body: Record<string, unknown>) {
    result.value = "";
    error.value = "";
    isStreaming.value = true;
    abortController = new AbortController();

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortController.signal,
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No readable stream");

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            // 事件类型在下一行 data 中处理
            continue;
          }
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);
              // 根据不同 SSE 事件处理（event 信息在上一行）
              if (data.taskId && !data.content) {
                currentTaskId.value = data.taskId;
              } else if (data.content) {
                result.value += data.content;
              }
            } catch {
              // 非 JSON 数据，跳过
            }
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // 用户主动取消，不算错误
      } else {
        error.value = e instanceof Error ? e.message : String(e);
      }
    } finally {
      isStreaming.value = false;
    }
  }

  function stop() {
    abortController?.abort();
    isStreaming.value = false;
  }

  return { result, isStreaming, error, currentTaskId, startSSE, stop };
}
```

#### `useTask.ts` [F5, F7, F8]

```typescript
import { useSSE } from "./useSSE";
import { cancelTask } from "../services/linguistApi";

export function useTask() {
  const { result, isStreaming, error, currentTaskId, startSSE, stop } =
    useSSE();
  const baseUrl = import.meta.env.VITE_API_BASE || "/api";

  async function submitTask(type: string, params: Record<string, unknown>) {
    await startSSE(`${baseUrl}/task`, { type, params });
  }

  async function cancelCurrentTask() {
    stop();
    if (currentTaskId.value) await cancelTask(currentTaskId.value);
  }

  return {
    result,
    isStreaming,
    error,
    currentTaskId,
    submitTask,
    cancelCurrentTask,
  };
}
```

### 3.6 现有页面改造要点（UI 布局不动）

#### `DashboardView.vue` [F1] — 保留现状

- 双卡片「文本翻译空间」「智能要点总结」+ 快捷输入框
- 卡片点击：`router.push({ name: 'translation' })` / `router.push({ name: 'summarization' })`
- 快捷输入：写入 `workspaceStore.quickText` 后 `router.push`

#### `TranslationView.vue` [F2] — 仅改数据层

- **保留**：10 种源/目标语言、5 种语调、双栏布局、复制/下载
- **改造**：`api.translate()` 非流式调用 → `useTask().submitTask('translate', { text, sourceLang, targetLang, tone })`
- 结果区在现有 `outputText` 上逐字追加 `result`；流式中显示「停止生成」按钮

#### `SummarizationView.vue` [F3] — 仅改数据层

- **保留**：要点数/字数上限/语调/文件导入、概述+要点结构化展示
- **改造**：`submitTask('summarize', { text, keyPointsCount, wordLimit, tone })`
- 流式阶段在现有区域追加 raw 文本；`task_done` 后解析 `overview` / `keyPoints` 渲染

#### `Sidebar.vue` — Router 导航

- `router-link` 替代 `emit('update:activeView')`；`useRoute().name` 控制高亮

### 3.7 主题切换 [F19] — Ant Design Vue

在 `App.vue` 中：

```vue
<script setup lang="ts">
import { ref, computed } from "vue";
import { theme } from "ant-design-vue";

const isDark = ref(true);
const antTheme = computed(() => ({
  algorithm: isDark.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
  token: { colorPrimary: "#00A67E" /* 沿用现有 token */ },
}));
</script>

<template>
  <a-config-provider :theme="antTheme">
    <!-- Sidebar 内增加主题切换按钮 toggle isDark -->
    <router-view />
  </a-config-provider>
</template>
```

> 不使用独立 `theme.css` / `@vueuse/useDark`；Tailwind 布局类保持不变。

---

## 四、CLI 实现（Python Click）

### 4.1 `cli/ai_app.py`

```python
import click
import httpx
import sys
import json

BASE_URL = "http://127.0.0.1:18765"

@click.group()
def cli():
    """AI TextFlow CLI - 翻译与总结工具"""
    pass

@cli.command()
@click.option("--text", required=True, help="要翻译的文本")
@click.option("--from", "from_lang", required=True, help="源语言代码，如 zh/en/ja")
@click.option("--to", "to_lang", required=True, help="目标语言代码")
@click.option("--tone", default="formal", help="语调")
def translate(text, from_lang, to_lang, tone):
    """翻译文本"""
    _stream_task("translate", {
        "text": text,
        "sourceLang": from_lang,
        "targetLang": to_lang,
        "tone": tone,
    })

@cli.command()
@click.option("--text", required=True, help="要总结的文本")
@click.option("--max-points", "key_points", default=3, help="要点数量")
@click.option("--word-limit", default=0, help="字数上限，0 表示不限")
def summarize(text, key_points, word_limit):
    """总结文本"""
    params = {"text": text, "keyPointsCount": key_points}
    if word_limit:
        params["wordLimit"] = word_limit
    _stream_task("summarize", params)

@cli.command("list")
def list_functions():
    """查看可用功能"""
    resp = httpx.get(f"{BASE_URL}/api/functions")
    data = resp.json()
    for fn in data["functions"]:
        click.echo(f"  {fn['id']:20s} {fn['name']:8s} - {fn['description']}")

def _stream_task(task_type: str, params: dict):
    """调用后端 SSE 接口，终端逐字打印"""
    with httpx.stream(
        "POST",
        f"{BASE_URL}/api/task",
        json={"type": task_type, "params": params},
        timeout=60.0,
    ) as resp:
        for line in resp.iter_lines():
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        click.echo(data["content"], nl=False)
                        sys.stdout.flush()
                except json.JSONDecodeError:
                    pass
    click.echo()  # 最终换行

if __name__ == "__main__":
    cli()
```

### 4.2 `cli/setup.py`

```python
from setuptools import setup

setup(
    name="ai-textflow-cli",
    version="0.1.0",
    py_modules=["ai_app"],
    install_requires=["click", "httpx"],
    entry_points={
        "console_scripts": ["ai-app=ai_app:cli"],
    },
)
```

安装后即可全局使用：

```bash
cd cli && pip install -e .
ai-app translate --text "你好" --from zh --to en
ai-app summarize --text "长文本" --max-points 3
```

---

## 五、SKILL.md 编写 [F11]

文件位置：`.claude/skills/SKILL.md`

```markdown
---
name: ai-textflow
description: AI text processing tool — translate between Chinese/English and summarize long text
---

# AI TextFlow CLI

This tool provides AI-powered text translation and summarization.

## Commands

### translate

Translate text between Chinese and English.
Usage: `ai-app translate --text "TEXT" --from zh|en --to zh|en`

### summarize

Summarize long text into key points.
Usage: `ai-app summarize --text "TEXT" --max-points N`

### list

List all available functions.
Usage: `ai-app list`

## Prerequisites

- Backend server running at http://127.0.0.1:18765
- CLI installed: `cd cli && pip install -e .`

## Examples

ai-app translate --text "Hello world" --from en --to zh
ai-app translate --text "你好世界" --from zh --to en
ai-app summarize --text "Very long text here..." --max-points 3
```

---

## 六、文档交付物

### `agent.md` [F13]

记录 AI Agent 在开发中的角色：

- Agent 承担的职责：架构设计、代码生成、测试用例编写
- 人类决策：技术栈选型、功能优先级、UI 交互设计
- Agent 执行：代码编写、bug 修复、文档生成
- 协作工具：Claude Code（本项目即用此开发）

### `docs/spec/` 目录 [F14]

| 文件                          | 内容                                |
| ----------------------------- | ----------------------------------- |
| `docs/spec/requirements.md`   | 功能清单，来源于 plan.md Phase 1-3  |
| `docs/spec/api-design.md`     | 接口规范，包含本方案的 API 设计     |
| `docs/spec/page-mockup.md`    | 页面线框图，包含本方案的 ASCII 原型 |
| `docs/spec/task-breakdown.md` | 任务分解，来源于 plan.md 排期       |

### `README.md`

结构：

1. 项目介绍 + 功能截图（含 Agent Chat）
2. 技术栈说明（Vue 3 + Ant Design Vue + FastAPI adaworks）
3. 本地运行：`npm run dev:all`（sidecar 18765 + frontend 1420）；`LLM_MODE=mock` 零配置
4. API 接口文档（functions / task SSE / cancel 三端点）
5. CLI 使用说明 + SKILL.md 路径
6. Docker（可选）与 mock/real 切换说明

---

## 七、实现顺序（开发检查清单）

按依赖关系排序，每一步都是可验证的增量。

### Step 0: Vue Router 迁移 [F0]

- [ ] 安装 `vue-router@4`；新增 `router/index.ts`
- [ ] `App.vue` 改 `<router-view>`；`Sidebar` 改 `router-link`
- [ ] 新增 `stores/workspace.ts`；各 View 从 store 读写 logs/quickText

### Step 1: 后端 SSE + Mock LLM

- [ ] `adaworks/config.py` + `services/llm.py`（mock）+ `services/prompt.py`
- [ ] `GET /api/functions`、`POST /api/task` SSE、`DELETE /api/task/{id}`
- [ ] **验证**：`curl http://127.0.0.1:18765/api/functions` 返回 translate/summarize
- [ ] **验证**：`POST /api/task` type=translate + sourceLang/targetLang 看到 SSE 流

### Step 2: 前端 SSE 对接（UI 不动）

- [ ] `useSSE.ts` + `useTask.ts`；改造 `linguistApi.ts`
- [ ] `TranslationView` / `SummarizationView` 接入流式 + 停止按钮
- [ ] **验证**：工作台 → 翻译页，mock 下结果区逐字输出

### Step 3: 任务取消 + real 模式

- [ ] `task_manager.py` 取消 + 超时
- [ ] 接入真实 GLM（`LLM_MODE=real`）；mock 路径保留

### Step 4: CLI + SKILL.md

- [ ] `cli/ai_app.py` + `setup.py` + `.claude/skills/SKILL.md`
- [ ] **验证**：`ai-app translate --text "Hello" --from en --to zh` 终端流式输出

### Step 5: 工程增强

- [ ] Ant Design Vue 明暗主题（`a-config-provider` algorithm 切换）
- [ ] 响应式：已有 Tailwind 断点，核对即可

### Step 6: 文档交付

- [ ] `agent.md` + `docs/spec/` + `README.md`

> **可选加分**：统一错误处理中间件、Docker 部署。

---

## 八、关键技术决策说明

| 决策       | 选择                         | 理由                                           |
| ---------- | ---------------------------- | ---------------------------------------------- |
| 改造策略   | 现有AdaWorks AI增量演进      | UI 已完备，只改底层 SSE/task 契约              |
| 导航       | Vue Router 4                 | 替代 activeView；URL 可直达、支持浏览器历史    |
| 前端 UI    | Ant Design Vue + Tailwind    | 已有工程栈；主题用 ConfigProvider algorithm    |
| SSE 客户端 | 原生 fetch + ReadableStream  | 不引入 eventsource 库                          |
| 状态管理   | Pinia workspace + composable | logs/quickText 跨页；流式数据在 composable ref |
| LLM 调用   | httpx 流式 + mock 开关       | 复用 glm_agent SSE 解析；无 Key 可演示         |
| 任务队列   | 纯内存 dict + asyncio.Task   | 足够演示 cancel/timeout                        |
| 翻译参数   | 多语言 translate type        | 与现有 TranslationView 10 语言 + 语调对齐      |
