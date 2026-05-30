# API 设计规范

> 开发规范（注释、try/catch、SRP）见 `spec/development-standards.md`。

Base URL：`http://127.0.0.1:18765`  
前缀：所有 REST 路径以 `/api` 开头

---

## 1. 核心 Task 契约（笔试必做）

### GET /api/functions

返回可用功能列表，供 **CLI / Agent** 发现能力（前端工作台不依赖）。

**Response 200**

```json
{
  "functions": [
    {
      "id": "translate",
      "name": "文本翻译",
      "description": "多语言翻译，支持源/目标语言与语调",
      "params": {
        "text": "string",
        "sourceLang": "string",
        "targetLang": "string",
        "tone": "string"
      }
    },
    {
      "id": "summarize",
      "name": "智能要点总结",
      "description": "长文本总结，支持要点数/字数上限/语调",
      "params": {
        "text": "string",
        "keyPointsCount": "number",
        "wordLimit": "number",
        "tone": "string"
      }
    }
  ]
}
```

---

### POST /api/task

提交任务，响应 **SSE**（`Content-Type: text/event-stream`）。

**Request Body**

```typescript
{
  type: "translate" | "summarize"
  params: Record<string, unknown>
}
```

**translate params**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | ✅ | 待翻译文本 |
| sourceLang | string | | 源语言，默认 `auto` |
| targetLang | string | | 目标语言，默认 `zh` |
| tone | string | | `Professional` / `Conversational` / `Technical` / `Academic` / `Creative` |

**summarize params**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | ✅ | 待总结文本 |
| keyPointsCount | number | | 默认 5 |
| wordLimit | number | | 默认 250 |
| tone | string | | 同上 |

**SSE Events**

| event | data 字段 | 说明 |
|-------|-----------|------|
| `task_start` | `{ taskId }` | 任务开始 |
| `token` | `{ content }` | 流式 token |
| `task_done` | `{ taskId, status, duration, result }` | 完成；translate 的 result 为 `{ text }`；summarize 为 `{ overview, keyPoints[] }` |
| `task_error` | `{ taskId, message }` | 失败 |

**Errors**

- `400`：`params.text` 为空
- `422`：Pydantic 校验失败（如 type 非法）

---

### DELETE /api/task/{taskId}

取消进行中的任务。

**Response 200**

```json
{
  "message": "task cancelled",
  "taskId": "abc123"
}
```

**Errors**

- `404`：任务不存在或已结束

---

### GET /api/task/{taskId}（加分）

查询任务状态。

**Response 200**

```json
{
  "taskId": "abc123",
  "status": "pending|running|done|failed|cancelled"
}
```

---

## 2. 辅助接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | `{ status, llm, keyLoaded }` |
| GET | `/api/logs` | 翻译/总结内存日志 |
| POST | `/api/logs/add` | 追加日志 |
| POST | `/api/logs/update-status` | 更新日志状态 |

---

## 3. Agent Chat（加分，独立模块）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sessions` | 会话列表 |
| POST | `/api/sessions` | 创建会话 |
| DELETE | `/api/sessions/{id}` | 删除 |
| GET | `/api/sessions/{id}/messages` | 消息历史 |
| POST | `/api/chat` | 发送消息（异步，过程走 WS） |
| WS | `/ws/chat/{session_id}` | 流式 Agent 事件 |

---

## 5. 环境变量（LLM）

| 变量 | 默认 | 说明 |
|------|------|------|
| `LLM_MODE` | `mock` | `mock` 本地预设流；`real` 需 GLM 密钥 |
| `GLM_API_KEY` / `ZHIPU_API_KEY` | | 智谱 API Key（与 Agent Chat 共用） |
| `GLM_API_BASE` | 智谱 OpenAI 兼容地址 | |
| `GLM_MODEL` | `glm-4-flash` | |
| `TASK_TIMEOUT_SECONDS` | `60` | 单任务超时 |

实现位置：`backend/adaagent/config.py`、`services/llm.py`
