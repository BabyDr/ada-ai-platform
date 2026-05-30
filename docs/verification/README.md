# 手动验收记录

本目录存放 [`implementation-tasks.md`](../ai-native/implementation-tasks.md) 与 [`ai-requirement.md`](../ai-native/ai-requirement.md) 要求的人工验收截图与说明。

> **当前状态（2026-05-30）**：自动化测试与文档已就绪；本目录 **尚无 `.png` 截图文件**，笔试硬性交付项「Agent 调用截图」与下列 V1–V6 均待补拍。

---

## 交付物核对

| 类别 | 要求来源 | 路径 / 动作 | 状态 |
|------|----------|-------------|------|
| 源码仓库 | ai-requirement §四 | GitHub/Gitee 地址 | 提交时填写 |
| README | ai-requirement §四 | [`README.md`](../../README.md) | ✅ |
| skill.md | ai-requirement §3.2 | [`.claude/skills/skill.md`](../../.claude/skills/skill.md) | ✅ |
| **Agent 调用截图** | ai-requirement §3.2 / T4.3 | `agent-skill-invoke.png` | ❌ 待补 |
| agent.md | 加分 §1 | [`agent.md`](../../agent.md) | ✅ |
| spec/ 目录 | 加分 §1 | [`spec/`](../../spec/) | ✅ |
| 系统手册 | T7.4 | [`docs/manual.md`](../manual.md) | ✅ |
| Docker | 加分 §5 | `Dockerfile` + `docker-compose.yml` | ✅（Sidecar） |
| 手动验收截图 | T2.4–T6.2 | 下表 V1–V6 | ❌ 待补 |
| 异常清单（工程加分） | exception-checklist | [`exception-checklist.md`](../ai-native/exception-checklist.md) | ✅ |

---

## 验收清单

| 编号 | 任务 | 内容 | 截图文件（建议命名） | 状态 |
|------|------|------|---------------------|------|
| V1 | T2.4 | 翻译页 mock 流式 + 停止生成 | `translation-streaming.png` | ❌ |
| V2 | T2.5 | 总结页 mock 流式 + 停止生成 | `summarization-streaming.png` | ❌ |
| V3 | T2.6 | 工作台快捷输入预填翻译页 | `dashboard-quick-route.png` | ❌ |
| V4 | T4.3 | Claude Code 发现并调用 `ai-app` | `agent-skill-invoke.png` | ❌ |
| V5 | T6.1 | 明暗主题切换前后对比 | `theme-light.png` / `theme-dark.png` | ❌ |
| V6 | T6.2 | 375px / 768px 响应式无溢出 | `responsive-375.png` / `responsive-768.png` | ❌ |

可选加分验收（非笔试硬性，见 exception-checklist）：

| 编号 | 内容 | 截图建议 | 状态 |
|------|------|----------|------|
| V7 | 流式中切换路由 → 离开确认 Modal | `route-leave-guard.png` | ❌ |
| V8 | F5 刷新后任务恢复提示 | `task-recovery-hint.png` | ❌ |
| V9 | 运行日志分页「加载更多」 | `history-pagination.png` | ❌ |

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
6. **Agent skill（V4）**：Claude Code 加载 `.claude/skills/skill.md` → 执行 `ai-app list` → 截图终端输出
7. **路由守卫（V7）**：翻译流式进行中点击 Sidebar 其他菜单 → 确认弹出离开提示
8. **任务恢复（V8）**：流式进行中 F5 → 页面 mount 后显示恢复提示文案

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
