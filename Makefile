.PHONY: test test-backend test-cli test-frontend build

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
