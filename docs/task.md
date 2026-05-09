# task.md — 按 [plan.md](./plan.md) 拆解的实现任务

> 依据 [plan.md](./plan.md) 的 SRP 分层、组件映射、样式栈 §5.0 与最小代码骨架 §5.1–§5.6 生成；详细 API 与产品行为以 [spec.md](./spec.md) 为准。  
> **路径约定**：下文中的 `src/` 均指仓库内 **`frontend/src/`**。  
> 完成项请将 `- [ ]` 改为 `- [x]`。

---

## 阶段 A：样式栈与工程底座（对应 plan §5.0）

- [x] 安装依赖：`vue`、`typescript`、`vite`、`ant-design-vue`、`tailwindcss`、`postcss`、`autoprefixer`、`pinia`、`vue-router`（与 spec 技术栈一致）
- [x] 配置 `tailwind.config.js`：`content` 覆盖 `./index.html` 与 `./src/**/*.{vue,ts,...}`；设置 `corePlugins.preflight: false`（与 plan 一致，避免与 Ant Design Vue reset 冲突）
- [x] 配置 `postcss.config.js`：启用 `tailwindcss`、`autoprefixer`
- [x] 编写 `src/style.css`：先 `@import "ant-design-vue/dist/reset.css"`，再依次 `@tailwind base;`、`@tailwind components;`、`@tailwind utilities;`
- [x] 编写 `src/main.ts`：最先 `import "./style.css"`，再 `createApp(App)`、`app.use(Antd)`（或按需 + `unplugin-vue-components` / `AntDesignVueResolver`，与团队选型一致即可）
- [x] 根布局用 `a-config-provider` 包裹应用（`theme` / `algorithm`），对齐 spec §4 视觉与暗色策略
- [x] 遵守 plan 分工：**表单/按钮/反馈** 用 Ant Design Vue；**页面外壳布局、间距、响应式** 用 Tailwind；禁止大量 Tailwind 覆盖 Ant 组件内部结构

---

## 阶段 B：类型与传输层（对应 plan §5.1、§5.2；SRP：仅传输）

- [x] 新增 `src/types/chat.ts`：实现 `Session`、`ChatMessage`、`ChatRequest`、`ChatAck`（字段与 spec §5.1 对齐）
- [x] 在 `src/types/index.ts`（若存在）中导出对话相关类型
- [x] 新增 `src/services/api.ts`：实现 `BASE = http://localhost:18765/api`（与 spec §8.2）；实现 `postChat`、`getSessions`；错误时 `throw`，不包含 Vue/Pinia
- [x] 新增 `src/services/websocket.ts`：单例或工厂封装 WebSocket 连接与重连；**不包含**组件逻辑（对应 plan §3 反例表）

---

## 阶段 C：状态层（对应 plan §5.3；SRP：单一业务域）

- [x] 安装并注册 Pinia（`main.ts` 中 `app.use(pinia)`）
- [x] 新增 `src/stores/chat.ts`：`sessions`、`messages`、`activeSessionId`、`currentModelId`；实现 `loadSessions`、`sendUserMessage`（内部仅调用 `services/api`，不写 DOM）
- [x] 为 store 内异步方法补充中文注释（符合 spec §8.1）

---

## 阶段 D：对话 MVP 组件（对应 plan §2 映射与 §5.4–§5.6）

- [x] 新增 `src/components/chat/MessageBubble.vue`：仅 `defineProps` 展示 `role` / `content`；使用 `a-card` + plan 中 Tailwind 辅助类；**禁止**调用 `fetch` 或 `useChatStore`
- [x] 新增 `src/components/chat/InputBar.vue`：本地 `ref` + `emit('submit', value)`；使用 `a-row` / `a-col` / `a-input` / `a-button`；**禁止**发起 HTTP
- [x] 新增 `src/components/chat/ChatPanel.vue`：`storeToRefs` + `onMounted` 调 `loadSessions`；模板组合 `MessageBubble` 与 `InputBar`；`@submit` 绑定 `chat.sendUserMessage`；**禁止**内联实现 Markdown 或 WS 解析
- [x] 新增 `src/views/ChatView.vue`：路由级壳层，拼装 `ChatPanel`（及后续侧栏等）；**禁止**写业务 `fetch` URL

---

## 阶段 E：组合逻辑与流式（对应 plan composables 约定、§6）

- [x] 新增 `src/composables/useChatStream.ts`（或等价命名）：封装「订阅 WebSocket → 解析事件 → 追加/更新 `messages`」的流程；**不**持有与对话无关的全局状态
- [x] 在 `ChatPanel.vue` 或 `useChatStore` 中于合适生命周期调用 composable（挂载订阅、卸载取消）；保持 Panel 内代码以拼装为主，单文件逻辑过长时继续下沉到 composable

---

## 阶段 F：ReAct 展示叶子组件（对应 plan §2 映射）

- [x] 新增 `src/components/chat/ThinkBlock.vue`：仅展示 Think 步骤 UI（可折叠用局部 `ref`）；props 由父级传入
- [x] 新增 `src/components/chat/ActionBlock.vue`：仅展示 Act 步骤（工具名、参数展示）
- [x] 新增 `src/components/chat/ObservationBlock.vue`：仅展示 Observe 结果（如代码块样式）
- [x] 新增 `src/components/chat/FinalResult.vue`：仅展示最终回答区域（Markdown 容器可占位，解析逻辑不放此处）
- [x] 在 `ChatPanel.vue`（或子列表组件）中按消息类型组合上述块，仍保持 **不调 API**

---

## 阶段 G：SRP 自检（对应 plan §1、§3、§6）

- [x] 每新增/修改 `.vue`：对照 plan §1 表格，确认「变更理由」是否唯一（UI / 协议 / 状态分离）
- [x] 对照 plan §3：确认不存在「Panel 内 fetch + Markdown + 列表」等上帝组件反例
- [x] 对照 plan §4 数据流：View → Panel → Leaf；Panel → Store → Service，无逆向绕路

---

## 参考索引

| plan.md 章节 | task.md 阶段 |
|---------------|--------------|
| §5.0 样式栈 | A |
| §5.1–§5.2 类型与服务 | B |
| §5.3 Store | C |
| §5.4–§5.6 对话组件骨架 | D |
| composables / §6 WebSocket | E |
| §2 ReAct 子组件 | F |
| §1 / §3 / §6 清单 | G |
