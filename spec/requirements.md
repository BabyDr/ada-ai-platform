# 需求规格 — AI TextFlow

> 来源：[docs/ai-navitve/ai-requirement.md](../docs/ai-navitve/ai-requirement.md)  
> 策略：在现有 Linguist AI 上**增量改造**，UI 保持现状

---

## 1. 功能需求

### 1.1 前端

| ID | 需求 | 实现 |
|----|------|------|
| F-UI-01 | 功能入口与工作台 | `DashboardView` 双卡片 + 快捷输入跳转 |
| F-UI-02 | 翻译页：多语言、语调、双栏、流式结果 | `TranslationView` + `useTask` |
| F-UI-03 | 总结页：要点数/字数/语调、文件导入、结构化展示 | `SummarizationView` + `useTask` |
| F-UI-04 | SSE 打字机效果 | `useSSE` composable |
| F-UI-05 | 停止生成（中断 SSE + 取消后端任务） | `cancelCurrentTask` → DELETE `/api/task/{id}` |
| F-UI-06 | 调用记录页 | `HistoryView` + 内存日志（已有） |
| F-UI-07 | Agent 对话（加分） | `ChatView` + WebSocket（已有，不破坏） |
| F-UI-08 | Vue Router 导航 | `/dashboard` `/translation` `/summarization` 等 |
| F-UI-09 | 明暗主题（加分） | `a-config-provider` + `workspace.isDark` |

### 1.2 后端

| ID | 需求 | 实现 |
|----|------|------|
| F-API-01 | `GET /api/functions` | `api/functions.py` |
| F-API-02 | `POST /api/task` SSE | `api/task.py` |
| F-API-03 | `DELETE /api/task/{taskId}` | `api/task.py` + `task_manager` |
| F-API-04 | 参数校验 | `api/schemas.py` (Pydantic) |
| F-API-05 | Mock / Real LLM | `services/llm.py`，`LLM_MODE=mock\|real` |
| F-API-06 | 任务超时 | `config.task_timeout_seconds` |
| F-API-07 | 调用记录写入 | task 结束时 `linguist_service` 内存日志 |

### 1.3 CLI & Agent

| ID | 需求 | 实现 |
|----|------|------|
| F-CLI-01 | `ai-app translate` | `cli/ai_app.py` |
| F-CLI-02 | `ai-app summarize` | `cli/ai_app.py` |
| F-CLI-03 | `ai-app list` | `cli/ai_app.py` |
| F-CLI-04 | skill.md 供 Agent 发现 | `.claude/skills/skill.md` |

---

## 2. 非功能需求

| ID | 需求 | 说明 |
|----|------|------|
| NF-01 | 零配置演示 | `LLM_MODE=mock` + `npm run dev:all` 无需 API Key |
| NF-02 | Sidecar 端口 | **18765**（非 8000） |
| NF-03 | 前端端口 | **1420** |
| NF-04 | 测试可重复 | 后端 pytest + 前端 vitest，mock 模式默认 |

---

## 3. 不在本期范围（Future Scope）

- Tauri 桌面壳
- RAG / 知识库
- MCP 工具接入
- Redis / Celery 分布式队列
- SQLite 持久化翻译日志（当前内存）
- Docker / docker-compose（加分项，可选）
- 前端任务状态轮询 UI（后端已有 GET `/api/task/{id}`）
