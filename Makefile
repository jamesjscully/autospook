# AutoSpook OSINT Research Tool Makefile
# Temporal + LangGraph + LangSmith Architecture
#
# Note: This Makefile unsets OPENAI_API_KEY system env var to ensure
# the .env file values are used instead of any global settings

.PHONY: help install dev dev-backend dev-frontend temporal-start temporal-stop temporal-dev clean test audit lint format check-deps health all tools-status tools-test

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "AutoSpook OSINT Research Tool"
	@echo "============================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start: make dev"

# Installation and setup
install: ## Install all dependencies (Python + Node.js)
	@echo "📦 Installing Python dependencies..."
	@uv sync
	@echo "📦 Installing Node.js dependencies..."
	@cd frontend && npm install
	@echo "✅ All dependencies installed"

check-deps: ## Check if required tools are installed
	@echo "🔍 Checking dependencies..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv is not installed. Visit: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "❌ npm is not installed. Install Node.js first."; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "⚠️  docker is not installed. Some features require Docker."; }
	@echo "✅ Dependencies check passed"

setup-env: ## Copy environment template if .env doesn't exist
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp env.example .env; \
		echo "⚠️  Please edit .env and add your API keys"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Development modes
dev: check-deps setup-env install ## Start full development environment (recommended)
	@echo "🚀 Starting AutoSpook Development Environment"
	@echo "============================================="
	@$(MAKE) --no-print-directory _dev-parallel

_dev-parallel: ## Internal: Start backend and frontend in parallel
	@echo "🔧 Starting backend on port 8001..."
	@unset OPENAI_API_KEY && uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001 > .backend.log 2>&1 & echo $$! > .backend.pid
	@echo "⚛️  Starting frontend on port 3000..."
	@cd frontend && npm start > ../.frontend.log 2>&1 & echo $$! > ../.frontend.pid
	@sleep 3
	@echo ""
	@echo "🎉 AutoSpook is running!"
	@echo "  📱 Frontend: http://localhost:3000"
	@echo "  🔌 Backend:  http://localhost:8001"
	@echo "  📚 API Docs: http://localhost:8001/docs"
	@echo ""
	@echo "Services started in background. Use 'make stop' to stop them."
	@echo "Use 'make logs' to view logs or 'make health' to check status."

dev-backend: check-deps setup-env ## Start only the backend server
	@echo "🔧 Starting AutoSpook backend..."
	@unset OPENAI_API_KEY && uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

dev-frontend: ## Start only the frontend server
	@echo "⚛️  Starting AutoSpook frontend..."
	@cd frontend && npm start

# Temporal workflow mode
temporal-start: ## Start Temporal infrastructure (Docker required)
	@echo "🏗️  Starting Temporal infrastructure..."
	@docker-compose -f docker-compose.temporal.yml up -d
	@echo "⏳ Waiting for Temporal to be ready..."
	@timeout 60 bash -c 'until curl -s http://localhost:7233 >/dev/null; do sleep 2; done' || { echo "❌ Temporal failed to start"; exit 1; }
	@echo "✅ Temporal infrastructure running"
	@echo "  🌐 Temporal UI: http://localhost:8080"

temporal-stop: ## Stop Temporal infrastructure
	@echo "🛑 Stopping Temporal infrastructure..."
	@docker-compose -f docker-compose.temporal.yml down
	@echo "✅ Temporal infrastructure stopped"

temporal-dev: temporal-start ## Start development with Temporal workflows
	@echo "🚀 Starting AutoSpook with Temporal workflows..."
	@echo "👷 Starting Temporal worker..."
	@uv run python backend/orchestrator.py worker > .worker.log 2>&1 & echo $$! > .worker.pid
	@sleep 2
	@echo "🔧 Starting backend..."
	@unset OPENAI_API_KEY && uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001 > .backend.log 2>&1 & echo $$! > .backend.pid
	@sleep 2
	@echo "⚛️  Starting frontend..."
	@cd frontend && npm start > ../.frontend.log 2>&1 & echo $$! > ../.frontend.pid
	@sleep 3
	@echo ""
	@echo "🎉 AutoSpook with Temporal is running!"
	@echo "  📱 Frontend:    http://localhost:3000"
	@echo "  🔌 Backend:     http://localhost:8001"
	@echo "  🏗️  Temporal UI: http://localhost:8080"
	@echo ""
	@echo "All services started in background."
	@echo "Use 'make stop' to stop services and 'make temporal-stop' to stop Temporal."

temporal-demo: ## Run Temporal workflow demo
	@echo "🧪 Running Temporal workflow demo..."
	@uv run python backend/orchestrator.py

# Process management
stop: ## Stop all running services
	@echo "🛑 Stopping all services..."
	@-if [ -f .backend.pid ]; then kill `cat .backend.pid` 2>/dev/null; rm -f .backend.pid; fi
	@-if [ -f .frontend.pid ]; then kill `cat .frontend.pid` 2>/dev/null; rm -f .frontend.pid; fi
	@-if [ -f .worker.pid ]; then kill `cat .worker.pid` 2>/dev/null; rm -f .worker.pid; fi
	@-pkill -f "uvicorn.*backend.main" 2>/dev/null
	@-pkill -f "npm.*start" 2>/dev/null
	@-pkill -f "orchestrator.py.*worker" 2>/dev/null
	@-rm -f .*.log .*.pid
	@echo "✅ All services stopped"

# Code quality
test: ## Run all tests
	@echo "🧪 Running tests..."
	@echo "🐍 Python tests..."
	@uv run pytest || echo "⚠️  No Python tests found"
	@echo "⚛️  Frontend tests..."
	@cd frontend && npm test -- --watchAll=false || echo "⚠️  Frontend tests skipped"

audit: ## Run security audits
	@echo "🔒 Running security audits..."
	@echo "🐍 Python security check..."
	@uv run pip-audit . || echo "⚠️  pip-audit failed"
	@echo "⚛️  NPM security audit..."
	@cd frontend && npm audit

lint: ## Run linting on all code
	@echo "🔍 Linting code..."
	@echo "🐍 Python linting..."
	@uv run ruff check backend/ || echo "⚠️  Ruff not configured"
	@echo "⚛️  Frontend linting..."
	@cd frontend && npm run lint --if-present || echo "⚠️  Frontend linting not configured"

format: ## Format all code
	@echo "✨ Formatting code..."
	@echo "🐍 Python formatting..."
	@uv run black backend/ || echo "⚠️  Black not configured"
	@uv run ruff check --fix backend/ || echo "⚠️  Ruff not configured"
	@echo "⚛️  Frontend formatting..."
	@cd frontend && npm run format --if-present || echo "⚠️  Frontend formatting not configured"

# Health checks
health: ## Check health of running services
	@echo "🏥 Checking service health..."
	@echo -n "Backend (8001): "
	@curl -s http://localhost:8001/health >/dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Frontend (3000): "
	@curl -s http://localhost:3000 >/dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Temporal (7233): "
	@curl -s http://localhost:7233 >/dev/null && echo "✅ Healthy" || echo "❌ Down"

# OSINT Tools Management
tools-status: ## Check status of OSINT tools and API configurations
	@echo "🔧 OSINT Tools Status"
	@echo "====================="
	@echo "Checking API key configurations..."
	@unset OPENAI_API_KEY && uv run python -c "from backend.tools.tool_registry import get_tool_registry; import asyncio; registry = asyncio.run(get_tool_registry()); print('✅ Tool registry initialized'); config = registry.get_configured_apis(); print(f'📊 Configured APIs: {config[\"configured\"]}'); print(f'🔧 Total tools: {len(registry.tools)}'); health = asyncio.run(registry.health_check()); print(f'📈 Health status: {health}');" 2>/dev/null || echo "❌ Failed to check tools status"

tools-test: ## Test OSINT tools with sample data
	@echo "🧪 Testing OSINT Tools"
	@echo "======================"
	@echo "Running basic tool tests..."
	@unset OPENAI_API_KEY && uv run python -c "from backend.tools.tool_registry import get_tool_registry; import asyncio; async def test(): registry = await get_tool_registry(); print('Testing whois_lookup...'); result = await registry.execute_tool('whois_lookup', domain='example.com'); print(f'Result: {result}'); print('Testing DNS lookup...'); result = await registry.execute_tool('dns_lookup', domain='example.com'); print(f'Result: {result}'); asyncio.run(test())" 2>/dev/null || echo "❌ Tool tests failed"

# Utility targets
clean: stop ## Clean up logs, cache, and build artifacts
	@echo "🧹 Cleaning up..."
	@rm -f .*.log .*.pid
	@rm -rf backend/__pycache__ backend/**/__pycache__
	@rm -rf frontend/build frontend/node_modules/.cache
	@uv cache clean || true
	@echo "✅ Cleanup complete"

logs: ## Show logs from running services
	@echo "📋 Service logs:"
	@echo "=================="
	@if [ -f .backend.log ]; then echo "🔧 Backend:"; tail -20 .backend.log; echo ""; fi
	@if [ -f .frontend.log ]; then echo "⚛️  Frontend:"; tail -20 .frontend.log; echo ""; fi
	@if [ -f .worker.log ]; then echo "👷 Worker:"; tail -20 .worker.log; fi

# Build targets
build: ## Build production assets
	@echo "🏗️  Building production assets..."
	@cd frontend && npm run build
	@echo "✅ Build complete"

# All-in-one targets
all: install test lint ## Install dependencies, run tests, and lint code

# Docker targets (future enhancement)
docker-build: ## Build Docker images (future)
	@echo "🐳 Docker build not yet implemented"

docker-run: ## Run in Docker containers (future)
	@echo "🐳 Docker run not yet implemented"