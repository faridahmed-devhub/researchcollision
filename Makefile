APP_ENV ?= development

.PHONY: install dev backend frontend worker test test-backend test-frontend lint format typecheck migrate seed e2e clean docker-up docker-down

install:
	cd backend && python -m pip install -r requirements.txt && python -m pip install -r requirements-dev.txt
	cd frontend && npm install

dev:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

worker:
	cd backend && python -m app.workers.worker

frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -q

test-frontend:
	cd frontend && npm run test -- --run

lint:
	cd backend && python -m ruff check app tests scripts evaluation
	cd frontend && npm run lint

format:
	cd backend && python -m ruff check --fix app tests scripts evaluation && python -m ruff format app tests scripts evaluation
	cd frontend && npm run format

typecheck:
	cd backend && python -m mypy app
	cd frontend && npm run typecheck

migrate:
	cd backend && python -m alembic upgrade head

seed:
	cd backend && python ../scripts/seed.py

e2e:
	cd frontend && npm run test:e2e

clean:
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache frontend/dist frontend/test-results frontend/playwright-report
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

docker-up:
	docker compose up --build

docker-down:
	docker compose down
