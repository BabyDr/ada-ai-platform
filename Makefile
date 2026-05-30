.PHONY: test test-backend test-cli test-frontend build check

test: test-backend test-cli test-frontend
	@echo "All tests passed."

test-backend:
	cd backend && .venv/bin/python -m pytest tests/ -q

test-cli:
	cd cli && ../backend/.venv/bin/python -m pytest tests/ -q

test-frontend:
	cd frontend && npm run test

build:
	cd frontend && npm run build

## 提交前全量检查：单元测试 + 类型检查 + 构建
check: test build
	@echo "All checks passed. Ready to commit."
