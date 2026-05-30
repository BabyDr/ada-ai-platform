# AI Agent 在本项目中的角色与协作方式

> AdaAgent / Linguist AI · AI TextFlow 笔试交付  
> 开发方式：Vibe Coding + 规范驱动（SDD），Human-in-the-loop

---

## 1. Agent 承担的角色

| 角色 | 说明 |
|------|------|
| **需求分析** | 阅读 `docs/ai-native/ai-requirement.md`，对照现有 Linguist AI 代码库，输出增量改造方案（`plan.md` / `implementation-solution.md`） |
| **任务拆分** | 将方案拆为可验收的小任务（`implementation-tasks.md`），标注依赖与并行项 |
| **实现编码** | 后端 SSE 契约、前端 composable、Vue Router 迁移、CLI、测试用例 |
| **测试与验证** | 编写 pytest / vitest，运行 `make test` 确认 mock 全链路 |
| **文档交付** | 维护 README、`docs/spec/`、SKILL.md、本文件 |

Agent **不负责**的最终决策（由人类确认）：

- 与现有代码冲突时的方案选择（如 LLM 变量命名：采用 `GLM_*` 与 Agent Chat 共用密钥）
- UI 视觉改动（约束为「UI 不动，仅改数据层」）
- 是否提交 git / 推送远程

---

## 2. 协作流程

```
人类：笔试需求 + 现有仓库
        │
        ▼
Agent：plan.md / implementation-solution.md / implementation-tasks.md
        │
        ▼
人类：审阅方案、确认冲突决策（如 GLM_* vs LLM_API_*）
        │
        ▼
Agent：按阶段 0→7 实施 + 测试
        │
        ▼
人类：手动验收 dev:all、CLI、Agent 调用 skill 截图
```

### 规范驱动（SDD）

1. **先 spec 后 code**：`docs/spec/requirements.md`、`docs/spec/api-design.md` 定义契约
2. **开发规范**：`docs/spec/development-standards.md`（SRP、注释、try/catch、后端兜底）
3. **测试即验收**：每个任务自带测试用例；后端 pytest、前端 vitest 覆盖核心 composable
4. **活文档**：README 与 API 示例与实现保持一致

### 工具链

| 工具 | 用途 |
|------|------|
| Cursor Agent | 主开发、多文件改造、测试运行 |
| Claude Code + SKILL.md | 外部 Agent 发现 `ai-app` CLI 并调用 |
| `make test` | 统一后端 + CLI 测试入口 |
| `npm run test --prefix frontend` | 前端 vitest |

---

## 3. 人类决策记录

| 日期 | 议题 | 决策 |
|------|------|------|
| 2026-05 | LLM 环境变量 | **方案 A**：task 管线与 Agent Chat 共用 `GLM_API_KEY` / `GLM_API_BASE` / `GLM_MODEL`，`LLM_MODE=mock\|real` 控制翻译/总结 |
| 2026-05 | UI 策略 | 保留现有 Dashboard / Translation / Summarization 页面，不新建 HomeView |
| 2026-05 | 工作台入口 | 双卡片 + 快捷输入，非三卡片 functions 列表 |
| 2026-05 | 文本处理能力 | 翻译/总结统一经 `POST /api/task` SSE 契约（`type`: translate \| summarize） |

---

## 4. 执行记录（里程碑）

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M1 | Vue Router + 后端 mock SSE + 前端流式翻译 | ✅ |
| M2 | 任务取消 + summarize + 旧接口移除 | ✅ |
| M3 | CLI + SKILL.md + `dev:all` | ✅ |
| M4 | agent.md + docs/spec/ + docs/manual.md + vitest + README + Docker | ✅ |

---

## 5. Future Scope（本期未实现）

见 `docs/spec/task-breakdown.md`：Tauri 桌面壳、RAG 知识库、MCP 工具、Redis 任务队列等。Docker 一键部署见根目录 `docker-compose.yml`。
