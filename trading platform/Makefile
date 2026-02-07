.PHONY: help setup start stop test clean

help:
	@echo "Trading Analytics Platform - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial project setup"
	@echo "  make setup-backend  - Setup backend only"
	@echo "  make setup-frontend - Setup frontend only"
	@echo ""
	@echo "Database:"
	@echo "  make db-start       - Start TimescaleDB"
	@echo "  make db-stop        - Stop TimescaleDB"
	@echo "  make db-migrate     - Run database migrations"
	@echo "  make db-reset       - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Development:"
	@echo "  make start          - Start all services"
	@echo "  make start-backend  - Start backend only"
	@echo "  make start-frontend - Start frontend only"
	@echo "  make stop           - Stop all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean build artifacts"

setup: setup-backend setup-frontend db-start
	@echo "✅ Setup complete!"

setup-backend:
	@echo "Setting up backend..."
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd backend && cp .env.example .env || true
	@echo "✅ Backend setup complete"

setup-frontend:
	@echo "Setting up frontend..."
	cd frontend && npm install
	cd frontend && cp .env.example .env || true
	@echo "✅ Frontend setup complete"

db-start:
	@echo "Starting TimescaleDB..."
	docker-compose up -d timescaledb
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "✅ Database started"

db-stop:
	@echo "Stopping TimescaleDB..."
	docker-compose stop timescaledb
	@echo "✅ Database stopped"

db-migrate:
	@echo "Running database migrations..."
	cd backend && . venv/bin/activate && alembic upgrade head
	@echo "✅ Migrations complete"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d timescaledb; \
		sleep 5; \
		cd backend && . venv/bin/activate && alembic upgrade head; \
		echo "✅ Database reset complete"; \
	fi

start: db-start
	@echo "Starting all services..."
	@echo "Backend will be at http://localhost:8000"
	@echo "Frontend will be at http://localhost:3000"
	@echo ""
	@echo "Run 'make start-backend' and 'make start-frontend' in separate terminals"

start-backend:
	@echo "Starting backend..."
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend:
	@echo "Starting frontend..."
	cd frontend && npm run dev

stop:
	@echo "Stopping all services..."
	docker-compose stop
	@echo "✅ Services stopped"

test: test-backend test-frontend
	@echo "✅ All tests complete"

test-backend:
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest -v
	@echo "✅ Backend tests complete"

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --run
	@echo "✅ Frontend tests complete"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf backend/.coverage
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	@echo "✅ Cleanup complete"
