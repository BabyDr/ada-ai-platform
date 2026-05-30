# AdaWorks 文档中心

> 本目录包含 AdaWorks 项目的完整技术文档。从需求分析到架构设计、从开发规范到验证交付，覆盖工程化全生命周期。

---

## 📖 文档导航

### 快速了解

| 文档 | 说明 | 适合谁 |
|---|---|---|
| [使用手册](manual.md) | 安装、配置、功能说明、常见问题 | 用户 / 运维 |
| [架构详解](architecture.md) | 模块划分、依赖关系、关键契约 | 全栈开发者 |

### 工程化设计（spec/）

| 文档 | 说明 | 体现的设计思想 |
|---|---|---|
| [需求规格](spec/requirements.md) | 功能需求 + 非功能需求 + 约束条件 | **需求驱动**：先定义做什么，再决定怎么做 |
| [API 设计规范](spec/api-design.md) | 统一 SSE 任务协议、请求/响应 Schema、错误码 | **契约先行**：前后端、CLI、Agent 共享同一套 API 契约 |
| [开发规范](spec/development-standards.md) | SRP 分层、注释要求、错误处理、禁止重复逻辑 | **约束出质量**：统一的代码标准保证团队协作一致性 |
| [页面原型](spec/page-mockup.md) | 路由表、组件映射、UI 布局规范 | **原型即文档**：UI 结构与组件边界提前确定 |
| [任务拆分](spec/task-breakdown.md) | 分阶段交付计划、优先级、测试要求 | **增量交付**：每个阶段独立可验证 |

### AI Native 开发（ai-native/）

| 文档 | 说明 | 体现的设计思想 |
|---|---|---|
| [需求原文](ai-native/ai-requirement.md) | 原始需求定义 | **原始需求保留**：可追溯到最初的产品意图 |
| [技术方案](ai-native/plan.md) | 功能清单、改造原则、Phase 划分 | **渐进式改造**：不重写，在现有代码上增量演进 |
| [实现方案](ai-native/implementation-solution.md) | 仓库结构、依赖选型、交付范围 | **技术选型有据**：每个选型都有理由 |
| [任务清单](ai-native/implementation-tasks.md) | 编号任务、依赖关系、并行标记 | **精细化排期**：任务粒度到可执行级别 |
| [异常场景清单](ai-native/exception-checklist.md) | 57 项异常场景覆盖 | **防御性编程**：从设计阶段就考虑异常 |

### 验证交付（verification/）

| 文档 | 说明 |
|---|---|
| [验证记录](verification/README.md) | 交付清单 + 截图证据 |

截图目录：
- `verification/light/` — 浅色主题 6 张
- `verification/dark/` — 深色主题 7 张
- `verification/mobile/` — 移动端适配 4 张

---

## 🏛️ 工程化设计思想

### 1. 契约驱动开发（Contract-First）

```
需求规格 → API 契约 → 前后端并行开发 → 集成测试
```

API 设计规范（`spec/api-design.md`）在编码前就定义了统一 SSE 协议。前端 `useSSE` composable、后端 `TaskManager`、CLI `httpx` 流式消费，三者共享同一契约，互不阻塞。

**收益**：前端、后端、CLI 可以完全并行开发，只要契约不变就不会集成冲突。

### 2. 增量演进（Incremental Evolution）

```
现有代码 → Router 迁移 → SSE 接入 → 功能增强 → 安全加固
```

不是推倒重来。`ai-native/plan.md` 明确了 7 条改造原则：UI 不动、后端在 `adaworks/` 内扩展、Agent Chat 解耦保留。每个 Phase 独立可验证，上一个 Phase 交付后才进入下一个。

**收益**：随时可以停下，已交付的部分就是可工作的系统。

### 3. 分层职责隔离（SRP Layer Separation）

```
View（布局壳）→ Panel（编排）→ Leaf（纯展示）→ Composable（流程）→ Service（网络）→ Store（状态）
```

`spec/development-standards.md` 强制定义了各层职责边界。组件内零 `fetch`、零业务分支、零状态管理。新增一种消息角色只需加一个 Leaf 组件。

**收益**：代码定位可预测——改 UI 找 View/Leaf，改业务找 Composable，改接口找 Service。

### 4. 防御性编程（Defensive Programming）

```
输入校验 → XML 标签隔离 → Prompt 安全规则 → 输出 Schema 校验 → 异常场景清单
```

`ai-native/exception-checklist.md` 列出了 57 项异常场景。从输入层（Unicode NFC、50K 上限）到输出层（Pydantic 校验、语言一致性检测），层层防护。

**收益**：不是出了 Bug 才补错误处理，而是在设计阶段就穷举异常路径。

### 5. 统一抽象（Unified Abstraction）

```
翻译 ──┐
总结 ──┤── POST /api/task (统一 SSE) ──→ TaskManager ──→ LLM Provider
RAG* ──┘
```

所有 LLM 调用抽象为统一的流式任务。新增一种 AI 能力（如 RAG 问答），前端 `useTask()` 零改动，后端只需注册新的 `task_type` + 写一个 Prompt 构建函数。

**收益**：能力扩展的成本是 O(1) 而非 O(n)。

---

## 📐 文档依赖关系

```
ai-requirement.md                        ← 原始需求
    ↓
requirements.md                          ← 需求规格（结构化）
    ↓
plan.md → implementation-tasks.md        ← 技术方案 + 任务拆分
    ↓
api-design.md                            ← API 契约（前后端共享）
development-standards.md                 ← 开发规范（团队约束）
page-mockup.md                           ← 页面原型（UI 边界）
    ↓
architecture.md                          ← 架构文档（实现后总结）
manual.md                                ← 使用手册（面向用户）
    ↓
verification/                            ← 验证证据（交付证明）
```

建议阅读顺序：从上到下，与开发流程一致。

---

## 🔧 开发者快速参考

| 我想... | 看哪个文档 |
|---|---|
| 了解项目是做什么的 | `manual.md` → `architecture.md` |
| 加一个新 API 端点 | `spec/api-design.md`（先看契约） |
| 加一个新的 AI 能力 | `spec/development-standards.md`（SRP 分层）+ `architecture.md` |
| 修改前端页面 | `spec/page-mockup.md`（组件映射）+ `spec/development-standards.md`（View→Panel→Leaf） |
| 查看原始需求 | `ai-native/ai-requirement.md` |
| 了解技术选型理由 | `ai-native/implementation-solution.md` |
| 排查异常处理 | `ai-native/exception-checklist.md` |
