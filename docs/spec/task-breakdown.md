# 任务拆分与交付状态

> 详细任务见 [implementation-tasks.md](../ai-native/implementation-tasks.md)

---

## 阶段概览

| 阶段 | 主题 | 优先级 | 状态 |
|------|------|--------|------|
| 0 | Vue Router 迁移 | P0 | ✅ |
| 1 | 后端 SSE 模块 | P0 | ✅ |
| 2 | 前端 SSE 对接 | P0 | ✅ |
| 3 | 任务取消 + real 模式 | P0 | ✅ |
| 4 | CLI + SKILL.md | P1 | ✅ |
| 5 | 启动联调 + 统一测试 | P1 | ✅ |
| 6 | 加分项（主题/响应式/traceId/Docker） | P2 | 部分 |
| 7 | 文档交付 | P3 | ✅ |
| 8 | 前端 vitest | P1 | ✅ |

---

## 阶段 0–3（P0 核心）

| 任务 | 交付物 | 测试 |
|------|--------|------|
| T0.1–T0.3 | router、App.vue、workspace store | vitest store |
| T1.1–T1.7 | config、llm、prompt、schemas、functions、task SSE | pytest 25 项 |
| T2.1–T2.6 | linguistApi、useSSE、useTask、View 改造 | vitest + 手动 |
| T3.1–T3.4 | task_manager、cancel、real LLM、移除旧 REST | pytest |

---

## 阶段 4–5（P1 完整交付）

| 任务 | 交付物 | 测试 |
|------|--------|------|
| T4.1–T4.2 | `cli/ai_app.py`、`setup.py` | pytest 2 项 |
| T4.3 | `.claude/skills/SKILL.md` | 人工 Agent 截图 |
| T5.1 | `npm run dev:all`、`.env.example` | curl + 手动 |
| T5.2 | 根 `Makefile` `make test` | 退出码 |

---

## 阶段 6（P2 加分 — Future / 部分完成）

| 任务 | 状态 | 说明 |
|------|------|------|
| T6.1 明暗主题 | ✅ | App.vue `a-config-provider` + Sidebar 切换 |
| T6.2 响应式布局 | ✅ | 现有 Tailwind 断点保持 |
| T6.3 traceId 统一错误 | ⏳ Future | 未实现中间件 |
| T6.4 Docker | ⏳ Future | 未提供 Dockerfile |

---

## 阶段 7（P3 文档）

| 任务 | 文件 |
|------|------|
| T7.1 | `agent.md` |
| T7.2 | `spec/` 四文件 |
| T7.3 | `README.md` 更新 |
| T7.4 | `docs/manual.md`（可选活文档） |

---

## Future Scope（明确不本期实现）

以下仅在 spec / plan 中标注，**不阻塞笔试基础交付**：

1. **Tauri 桌面壳** — 当前 Web + Sidecar 架构已满足
2. **RAG 知识库** — 无向量库与文档 ingest
3. **MCP 工具接入** — Agent Chat 为独立 WS 模块
4. **Redis / Celery 任务队列** — 内存 `task_manager` 已满足取消与状态
5. **前端任务轮询 UI** — 后端 GET `/api/task/{id}` 已有，UI 未做进度条
6. **SQLite 翻译日志** — History 仍为内存；Agent 会话用 SQLite
7. **Docker 一键部署** — 加分项待定
8. **虚拟滚动大文本优化** — 未专项优化

---

## 验收命令

```bash
npm run dev:all                    # mock 全链路
make test                          # 后端 + CLI
npm run test --prefix frontend     # vitest
npm run build --prefix frontend    # 生产构建
cd cli && pip install -e . && ai-app list
```
