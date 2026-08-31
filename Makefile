# Convenience targets. Backend targets assume a venv at backend/.venv (see `make setup`).
.PHONY: help setup backend frontend test test-core seed clean

help:
	@echo "Targets:"
	@echo "  setup      Create backend venv + install base deps; install frontend deps"
	@echo "  backend    Run the FastAPI dev server on http://localhost:8000"
	@echo "  frontend   Run the Vite dev server on http://localhost:5173"
	@echo "  test       Run backend tests with pytest (requires full install)"
	@echo "  test-core  Run core tests with stdlib unittest (no third-party deps needed)"
	@echo "  seed       Seed the exemplar knowledge base from control text"
	@echo "  clean      Remove caches and generated artifacts"

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && \
		pip install -U pip && pip install -r requirements.txt
	cd frontend && npm install
	@echo ">> Optional AI upgrade: cd backend && . .venv/bin/activate && pip install -r requirements-ml.txt"

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest -q

test-core:
	cd backend && python3 -m unittest discover -s tests -v

seed:
	cd backend && . .venv/bin/activate && python -m app.training.seed

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache frontend/dist frontend/.vite
