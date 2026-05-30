# 手动验收记录

本目录存放 [`implementation-tasks.md`](../ai-native/implementation-tasks.md) 与 [`ai-requirement.md`](../ai-native/ai-requirement.md) 要求的人工验收截图与说明。

---

## 交付物核对

| 类别 | 要求来源 | 路径 / 动作 | 状态 |
|------|----------|-------------|------|
| 源码仓库 | ai-requirement §四 | GitHub/Gitee 地址 | 提交时填写 |
| README | ai-requirement §四 | [`README.md`](../../README.md) | ✅ |
| SKILL.md | ai-requirement §3.2 | [`.claude/skills/SKILL.md`](../../.claude/skills/SKILL.md) | ✅ |
| Agent 调用截图 | ai-requirement §3.2 / T4.3 | [`agent-skill-invoke.png`](agent-skill-invoke.png) | ✅ |
| agent.md | 加分 §1 | [`agent.md`](../../agent.md) | ✅ |
| spec/ 目录 | 加分 §1 | [`docs/spec/`](../spec/) | ✅ |
| 系统手册 | T7.4 | [`docs/manual.md`](../manual.md) | ✅ |
| Docker | 加分 §5 | `Dockerfile` + `docker-compose.yml` | ✅（Sidecar） |
| 手动验收截图 | T2.4–T6.2 | 下表 V1–V6 | ✅ |
| 异常清单（工程加分） | exception-checklist | [`exception-checklist.md`](../ai-native/exception-checklist.md) | ✅ |

---

## 验收清单

### 截图目录结构

```
docs/verification/
├── agent-skill-invoke.png          # Agent skill 调用截图
├── light/                          # 浅色主题截图
│   ├── ai_workspace_overview.png   # 工作台总览
│   ├── translation_comparison.png  # 翻译页（输入）
│   ├── translation_complete.png    # 翻译完成
│   ├── ai_summary_config.png      # 总结配置
│   ├── smart_summary.png           # 总结结果
│   ├── ai_chat_interface.png      # Agent 对话
│   ├── api_logs.png               # 运行日志
│   └── global_settings.png        # 设置页
├── dark/                           # 深色主题截图
│   ├── dark_workspace.png
│   ├── dark_translator.png
│   ├── dark_summary_result.png
│   ├── dark_chat_interface.png
│   ├── runtime_logs.png
│   └── system_settings.png
└── mobile/                         # 移动端截图
    ├── linguist_workspace_main.jpg
    ├── linguist_translation.jpg
    ├── linguist_summary.jpg
    └── linguist_api_logs.jpg
```

### 验收项与截图对照

| 编号 | 任务 | 内容 | 截图文件 | 状态 |
|------|------|------|----------|------|
| V1 | T2.4 | 翻译页 mock 流式 + 结果对照 | `light/translation_comparison.png` · `light/translation_complete.png` | ✅ |
| V2 | T2.5 | 总结页 mock 流式 + 结果 | `light/ai_summary_config.png` · `light/smart_summary.png` | ✅ |
| V3 | T2.6 | 工作台总览 + 快捷入口 | `light/ai_workspace_overview.png` | ✅ |
| V4 | T4.3 | Claude Code 发现并调用 `ai-app` | `agent-skill-invoke.png` | ✅ |
| V5 | T6.1 | 明暗主题切换前后对比 | `light/` · `dark/` 全套 | ✅ |
| V6 | T6.2 | 移动端响应式（375px） | `mobile/` 全套 | ✅ |

---

## 如何复现

```bash
npm run dev:all
# 浏览器打开 http://localhost:1420
# 确认 backend/.env 中 LLM_MODE=mock（或移除 GLM_API_KEY 以演示 mock）
```

1. **翻译流式（V1）**：`/translation` → 输入「你好」→ 开始翻译 → 观察打字机效果 → 点击停止
2. **总结流式（V2）**：`/summarization` → 粘贴长文本 → 生成总结 → 停止
3. **快捷路由（V3）**：`/dashboard` → 快捷输入框输入文本 → 回车 → 确认目标页预填
4. **主题（V5）**：Sidebar 底部切换太阳/月亮图标 → 确认 Ant 组件与页面背景同步变化 → 刷新确认持久化（`localStorage` 键 `adaagent-dark`）
5. **响应式（V6）**：DevTools 设备模式切换 375px / 768px 截图
6. **Agent skill（V4）**：Claude Code 加载 `.claude/skills/SKILL.md` → 执行 `ai-app list` → 截图终端输出

---

## 自动化测试覆盖

以下项已有自动化测试，不强制截图：

**后端（pytest）**

- SSE 契约：`backend/tests/test_task_sse.py`
- 任务取消：`backend/tests/test_task_cancel.py`
- 任务管理器：`backend/tests/test_task_manager.py`
- Mock LLM：`backend/tests/test_llm_mock.py`
- Real LLM MockTransport：`backend/tests/test_llm_real.py`
- 配置 / Prompt / 校验 / 日志：`test_config.py`、`test_prompt.py`、`test_log_service.py` 等

**CLI**

- `cli/tests/test_cli.py`

**前端（vitest）**

- `frontend/src/composables/useSSE.test.ts`
- `frontend/src/composables/useTask.test.ts`
- `frontend/src/composables/useStreamBuffer.test.ts`
- `frontend/src/composables/useThemeAttribute.test.ts`
- `frontend/src/composables/useQuickRoute.test.ts`
- `frontend/src/services/linguistApi.test.ts`
- `frontend/src/stores/workspace.test.ts`
- `frontend/src/components/SummarizationView.test.ts`

```bash
make test
```

> 若本机配置了 `GLM_API_KEY`，部分后端 mock 测试可能因自动切换 `real` 模式而失败；验收前可临时 `LLM_MODE=mock` 并 unset 密钥，或使用干净 `.env`。

---

## 已知缺口（非阻塞 mock 演示）

| 项 | 说明 |
|----|------|
| Agent WS 自动重连 | `useChatStream.ts` 无 reconnect（exception-checklist #50） |
| History 虚拟滚动 | 已有分页 + 截断，未引入 `@tanstack/vue-virtual`（#36） |
| CLI 超时对齐 | CLI 120s vs Server 60s（#56） |
| docker-compose | 仅 Sidecar，不含前端静态资源服务 |
