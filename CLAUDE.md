# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AdaAgent is a full-stack AI text processing platform with a Vue 3 frontend, Python FastAPI backend (called "Sidecar"), and a Click CLI. It provides translation, summarization (via SSE streaming), and agent chat (via WebSocket).

## Common Commands

### Development
```bash
npm run sidecar:setup    # First-time: create backend venv + install deps
npm run install           # Install frontend deps
npm run dev:all           # Start both frontend (port 1420) + backend (port 18765)
npm run dev               # Frontend only
npm run sidecar           # Backend only
```

### Testing
```bash
make test                 # All tests (backend + CLI + frontend)
make test-backend         # cd backend && .venv/bin/python -m pytest tests/ -q
make test-cli             # cd cli && ../backend/.venv/bin/python -m pytest tests/ -q
make test-frontend        # cd frontend && npm run test
```

Run a single backend test: `cd backend && .venv/bin/python -m pytest tests/test_foo.py::test_bar -q`
Run frontend tests in watch mode: `cd frontend && npm run test:watch`

### Build
```bash
make build                # cd frontend && npm run build (includes vue-tsc type check)
```

## Architecture

### Monorepo Layout
- **`frontend/`** — Vue 3 + TypeScript + Vite. Ant Design Vue + Tailwind CSS v4.
- **`backend/`** — Python FastAPI. SQLite via aiosqlite. LLM: Zhipu GLM / Google Gemini / mock mode.
- **`cli/`** — Python Click CLI (`ai-app` command). Calls backend SSE API via httpx.
- **`docs/spec/`** — API design specs, development standards, requirements.
- **`docs/`** — User manual, verification docs, AI-native specs, architecture.

### Frontend Layer Pattern (SRP)

| Layer | Location | Role |
|-------|----------|------|
| View | `views/*.vue` | Page shell, layout assembly |
| Panel | `*Panel.vue` | Combines children, calls store |
| Leaf | `MessageBubble.vue` etc. | Pure presentation |
| Composable | `composables/*.ts` | Single-scene reusable flow logic |
| Store | `stores/*.ts` | Single business domain state (Pinia) |
| Service | `services/*.ts` | HTTP/WS calls, no Vue logic |

Chat module strictly follows View → Panel → Leaf. Linguist pages (Translation/Summarization) use composable orchestration + single-page two-column layout.

### Backend Structure

- `api/` — Route handlers (thin, delegate to services)
- `services/` — Business logic: `llm.py` (LLM streaming), `task_manager.py` (in-memory task state machine), `prompt.py`
- `main.py` — FastAPI app entry point
- `db.py` — SQLite layer (sessions + messages tables)
- `ws_hub.py` — WebSocket hub for agent chat (multi-tab support)
- `config.py` — pydantic-settings, reads env vars

### SSE Task API (unified contract for translate/summarize)

All text processing goes through a single SSE endpoint:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/functions` | Capability discovery |
| POST | `/api/task` | Submit task (`type`: `translate` \| `summarize`), returns SSE stream |
| DELETE | `/api/task/{taskId}` | Cancel running task |
| GET | `/api/task/{taskId}` | Query task status |

**Do not create** separate REST endpoints like `POST /api/translate`. See `docs/spec/api-design.md`.

### Key Real-Time Patterns

- **SSE** (`composables/useSSE.ts` ↔ `api/task.py`): Custom SSE parser via fetch + ReadableStream. Event types: `task_start`, `token`, `task_done`, `task_error`.
- **WebSocket** (`composables/useChatStream.ts` ↔ `ws_hub.py`): Bidirectional streaming for agent chat. Events: `agent:delta`, `agent:final`, `agent:error`.
- **Task lifecycle**: pending → running → done/failed/cancelled. Cooperative cancellation via asyncio.Event. Heartbeat + zombie cleanup.

### Configuration

Backend config via environment variables (see `config.py`): `LLM_MODE` (mock/real), `TASK_TIMEOUT_SECONDS`, `MAX_CONCURRENT_TASKS`, `MAX_LOGS`. Frontend config via Vite env: `VITE_API_BASE`, `VITE_WS_BASE`.

## Development Standards (from docs/spec/development-standards.md)

1. **Comments required**: All modules and exported functions need docstrings/JSDoc explaining purpose, boundary conditions, collaborators.
2. **Error handling required**: All async/IO must use try/catch (frontend: `runSafe()` from `utils/safeAsync.ts`; backend: `http_safe.register_global_exception_handler`).
3. **No duplicated logic**: Extract shared logic to composables/services. Do not copy-paste across views.
4. **API contract compliance**: Only SSE Task API for translation/summarization. No standalone REST routes.
