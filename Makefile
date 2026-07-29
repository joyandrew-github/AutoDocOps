.PHONY: help install-backend install-frontend install dev dev-backend dev-frontend build up down restart logs clean test-backend lint-backend format-backend migrate-db

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

install: install-backend install-frontend ## Install all dependencies

dev-backend: ## Run backend development server
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Run frontend development server
	cd frontend && npm run dev

dev: ## Run both backend and frontend development servers
	@echo "Starting backend and frontend development servers..."
	@make -j2 dev-backend dev-frontend

build: ## Build Docker containers
	docker-compose build

up: ## Start all services with Docker Compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-postgres: ## Show PostgreSQL logs
	docker-compose logs -f postgres

logs-neo4j: ## Show Neo4j logs
	docker-compose logs -f neo4j

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

clean: ## Remove all containers, volumes, and networks
	docker-compose down -v
	rm -rf backend/logs/*
	rm -rf frontend/.next
	rm -rf frontend/node_modules

test-backend: ## Run backend tests
	cd backend && pytest

lint-backend: ## Run backend linting
	cd backend && black --check app
	cd backend && isort --check-only app
	cd backend && mypy app

format-backend: ## Format backend code
	cd backend && black app
	cd backend && isort app

migrate-db: ## Run database migrations
	cd backend && alembic upgrade head

create-migration: ## Create a new database migration (usage: make create-migration MSG="migration message")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

rollback-db: ## Rollback database migration
	cd backend && alembic downgrade -1

psql: ## Connect to PostgreSQL database
	docker exec -it autodocops-postgres psql -U autodocops -d autodocops

redis-cli: ## Connect to Redis
	docker exec -it autodocops-redis redis-cli
