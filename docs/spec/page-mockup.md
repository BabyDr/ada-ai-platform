# 页面原型说明

> **原则**：沿用现有AdaWorks AIUI，不重做视觉；仅导航改为 Vue Router，数据层改为 SSE。

---

## 路由表

| 路径             | 组件                    | 说明         |
| ---------------- | ----------------------- | ------------ |
| `/`              | redirect → `/dashboard` | 默认入口     |
| `/dashboard`     | `DashboardView`         | 工作台       |
| `/translation`   | `TranslationView`       | 文本翻译     |
| `/summarization` | `SummarizationView`     | 智能要点总结 |
| `/chat`          | `ChatView`              | 智能体对话   |
| `/history`       | `HistoryView`           | 运行日志     |
| `/settings`      | `SettingsView`          | 设置         |

布局：`App.vue` = Sidebar + `<router-view>`，`a-config-provider` 包裹全局主题。

---

## 1. 工作台 `/dashboard`

```
┌────────────────────────────────────────────────────────────┐
│ Sidebar │ AdaWorks AI工作台                               │
│         │  ┌─────────────────┐  ┌─────────────────┐        │
│ 工作台  │  │ 文本翻译空间     │  │ 智能要点总结     │        │
│ 翻译    │  │ 多语言·语调      │  │ 要点·字数控制    │        │
│ 总结    │  └────────┬────────┘  └────────┬────────┘        │
│ 对话    │           │ router.push         │                  │
│ 日志    │  ┌──────────────────────────────────────────┐    │
│ 设置    │  │ 快捷输入框 → 智能跳转 translation/summary │    │
│         │  └──────────────────────────────────────────┘    │
│         │  统计卡片：总处理数、平均延迟、API 状态            │
└────────────────────────────────────────────────────────────┘
```

交互：

- 卡片点击 → `router.push({ name: 'translation' | 'summarization' })`
- 快捷输入 → `workspaceStore.setQuickText(text)` → 跳转对应页并预填

---

## 2. 翻译页 `/translation`

```
┌────────────────────────────────────────────────────────────┐
│ 源语言 [auto ▼]  ⇄  目标语言 [zh ▼]   语调 [Professional ▼] │
│ ┌──────────────────┐    ┌──────────────────┐               │
│ │ 输入文本          │    │ 翻译结果 ▌        │  ← SSE 流式   │
│ └──────────────────┘    └──────────────────┘               │
│ [开始翻译]  [停止生成]  [复制] [下载] [清空]                 │
└────────────────────────────────────────────────────────────┘
```

数据流：`useTask().submitTask('translate', { text, sourceLang, targetLang, tone })`

---

## 3. 总结页 `/summarization`

```
┌────────────────────────────────────────────────────────────┐
│ 要点数 [5]  字数上限 [250]  语调 [Professional]  [导入文件] │
│ ┌──────────────────┐    ┌──────────────────┐               │
│ │ 长文本输入        │    │ 概述 + 要点列表   │  ← 流式后解析 │
│ └──────────────────┘    └──────────────────┘               │
│ [生成总结]  [停止生成]                                       │
└────────────────────────────────────────────────────────────┘
```

数据流：`submitTask('summarize', { text, keyPointsCount, wordLimit, tone })`  
`task_done` 后解析 JSON `{ overview, keyPoints }` 渲染。

---

## 4. 运行日志 `/history`

列表展示：时间、类型（translation/summarization）、输入摘要、输出、耗时、状态。

数据来源：`GET /api/logs` + `workspaceStore.logs`。

---

## 5. 智能体对话 `/chat`

独立模块：会话列表 + 消息区 + ReAct 步骤块（Think / Action / Observation）。

通信：`POST /api/chat` + WebSocket `/ws/chat/{sessionId}`。

---

## 6. 全局状态

| Store / Composable   | 职责                                        |
| -------------------- | ------------------------------------------- |
| `workspace`          | logs、quickText、apiConnected、isDark       |
| `chat`               | Agent 会话与消息                            |
| `useTask` / `useSSE` | 翻译/总结流式任务（页面级 ref，不进 store） |
