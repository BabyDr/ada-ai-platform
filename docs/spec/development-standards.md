# 开发规范

> AdaAgent / Linguist AI 前后端统一约定。新代码与重构均须遵守。

---

## 1. 单一职责（SRP）

详见 `../ai-native/plan.md` §6.3。

| 层级 | 路径 | 职责 |
|------|------|------|
| View | `frontend/src/views/*.vue` | 页面壳、布局拼装 |
| Panel | `*Panel.vue` | 组合子组件、调 store |
| Leaf | `MessageBubble.vue` 等 | 纯展示 |
| Composable | `composables/*.ts` | 单场景流程，可复用 |
| Store | `stores/*.ts` | 单一业务域状态 |
| Service | `services/*.ts` | HTTP/WS，无 Vue 逻辑 |
| Backend API | `backend/adaagent/api/` | 路由与契约 |
| Backend Service | `backend/adaagent/services/` | 业务逻辑、LLM、日志 |

**禁止**：同一逻辑在多个 View/组件中各写一遍；应抽取 composable / service 共用。

**View → Panel → Leaf 的适用边界：**

- **Chat 模块（硬性）**：`ChatView` → `ChatPanel` → 多种消息 Leaf；WS 流与多 role 分发必须 Panel 层。
- **Linguist 工作台（可接受简化）**：Translation / Summarization 以 **composable 编排 + 单页双栏模板** 为主；可抽共享 Leaf（`components/shared/`），**不必**再拆 `TranslationPanel` + Input/Result Leaf，除非 UI 大规模独立迭代。

---

## 2. 注释（必须）

**所有模块、函数、方法必须有备注**，说明「做什么、边界条件、与谁协作」。

| 语言 | 要求 |
|------|------|
| TypeScript / Vue | 文件顶部的模块说明；导出函数用 `/** JSDoc */`；组件 `<script>` 首行说明页面/组件职责 |
| Python | 模块 docstring；公开函数/方法 docstring；非显而易见的分支加行内注释 |

纯展示 Leaf 组件至少保留一行组件职责说明。禁止无注释的 exported 函数。

---

## 3. 错误处理（必须）

### 3.1 前端

凡涉及 **async/await、fetch、剪贴板、文件读写** 的代码，**必须**使用 `try/catch`（或项目提供的 `runSafe` 封装）。

- UI 层：捕获后更新 `error` 状态或 `message.error`，禁止静默吞掉异常（除非明确标注为可忽略）。
- Service 层：捕获网络/解析异常，抛出带上下文的 `Error` 或返回结构化失败。
- Composable 层：对外暴露的 async 方法内部兜底，避免未处理的 Promise rejection。

推荐工具：`frontend/src/utils/safeAsync.ts` 中的 `runSafe()`。

### 3.2 后端

凡涉及 **路由 handler、外部 HTTP（LLM）、文件/DB、SSE 生成器** 的代码，**必须**有错误兜底：

- 路由：`register_global_exception_handler(app)` 捕获未预期异常并返回 `500` + `detail`；业务错误用 `HTTPException`。
- SSE 任务：生成器内 `try/except`，向客户端发送 `task_error` 并更新日志终态。
- 内存/DB 操作：失败时记录日志，必要时降级（如前端日志 fallback）。

推荐工具：`backend/adaagent/http_safe.register_global_exception_handler(app)`。

## 4. API 契约

文本翻译与智能总结 **仅** 通过 SSE Task 契约调用：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/functions` | 能力发现 |
| POST | `/api/task` | 提交任务（`type`: `translate` \| `summarize`） |
| DELETE | `/api/task/{taskId}` | 取消任务 |
| GET | `/api/task/{taskId}` | 查询状态 |

**不提供** 也 **禁止新增** 独立的 `POST /api/translate`、`POST /api/summarize` 等非流式路由。详见 `api-design.md`。

---

## 5. 自检清单（提交前）

- [ ] 新增/修改的函数均有注释
- [ ] async 与 IO 操作有 try/catch 或 `runSafe` / 后端等价兜底
- [ ] 未复制粘贴已在 composable/service 中存在的逻辑
- [ ] 未引入已废弃的 REST 路径
- [ ] `make test` / `npm test` 通过
