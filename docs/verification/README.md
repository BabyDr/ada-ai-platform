# 手动验收记录

本目录存放 `implementation-tasks.md` 要求的人工验收截图与说明。

## 验收清单

| 编号 | 任务 | 内容 | 截图文件（建议命名） |
|------|------|------|---------------------|
| V1 | T2.4 | 翻译页 mock 流式 + 停止生成 | `translation-streaming.png` |
| V2 | T2.5 | 总结页 mock 流式 + 停止生成 | `summarization-streaming.png` |
| V3 | T2.6 | 工作台快捷输入预填翻译页 | `dashboard-quick-route.png` |
| V4 | T4.3 | Claude Code 发现并调用 `ai-app` | `agent-skill-invoke.png` |
| V5 | T6.1 | 明暗主题切换前后对比 | `theme-light.png` / `theme-dark.png` |
| V6 | T6.2 | 375px / 768px 响应式无溢出 | `responsive-375.png` / `responsive-768.png` |

## 如何复现

```bash
npm run dev:all
# 浏览器打开 http://localhost:1420
```

1. **翻译流式**：`/translation` → 输入「你好」→ 开始翻译 → 观察打字机效果 → 点击停止
2. **总结流式**：`/summarization` → 粘贴长文本 → 生成总结
3. **快捷路由**：`/dashboard` → 快捷输入框输入文本 → 回车 → 确认目标页预填
4. **主题**：Sidebar 底部切换太阳/月亮图标 → 刷新确认持久化
5. **响应式**：DevTools 设备模式切换 375px / 768px 截图
6. **Agent skill**：Claude Code 加载 `.claude/skills/skill.md` → 执行 `ai-app list`

## 自动化测试覆盖

以下项已有自动化测试，不强制截图：

- 后端 SSE 契约：`backend/tests/test_task_sse.py`
- 任务取消：`backend/tests/test_task_cancel.py`
- real LLM MockTransport：`backend/tests/test_llm_real.py`
- 前端 composable：`frontend/src/composables/useSSE.test.ts`、`useTask.test.ts`
- 总结页 submitTask 参数：`frontend/src/components/SummarizationView.test.ts`

```bash
make test
```
