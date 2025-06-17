# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoSpook is an opens source intelligence (OSINT) tool for reporting on an targeted individual.
## Development Commands

### Quick Start (Recommended)
```bash
make dev
```
This handles dependency installation and starts both backend and frontend services.

### Manual Development
```bash
# Install all dependencies
make install

# Start backend only
make dev-backend

# Start frontend only  
make dev-frontend

# Traditional approach
uv run uvicorn backend.main:app --reload --port 8001  # Backend on :8001
cd frontend && npm start                               # Frontend on :3000
```

### Code Quality
```bash
# Format and lint all code
make format
make lint

# Run all tests
make test

# Run security audits
make audit

# Traditional approach
uv run black backend/     # Python formatting
uv run ruff backend/      # Python linting  
uv run pytest            # Python testing
cd frontend && npm test   # Frontend testing
uv run pip-audit .        # Python security audit
cd frontend && npm audit  # NPM security audit
```

### Temporal Workflows
```bash
# Start Temporal infrastructure
make temporal-start

# Run development with Temporal workflows
make temporal-dev

# Run workflow demo
make temporal-demo

# Stop Temporal infrastructure
make temporal-stop
```

### Utility Commands
```bash
# Check service health
make health

# View service logs
make logs

# Clean up build artifacts
make clean

# Stop all services
make stop

# Show all available commands
make help
```

## Architecture

AutoSpook follows a **Temporal + LangGraph + LangSmith** architecture pattern for robust OSINT research workflows.

### Backend (`backend/`)
- **main.py**: FastAPI application with CORS, health endpoints, and OSINT research API
- **agent.py**: LangGraph agent implementation for OSINT research using OpenAI GPT-3.5-turbo
- **orchestrator.py**: Temporal workflow orchestration for deep research workflows
- Built with FastAPI, LangGraph, Temporal, and LangSmith integration

#### Key Design Principles
- **Single source of truth**: `ResearchState` lives in Temporal workflow
- **Activity boundary**: LangGraph executes inside Temporal activities for I/O operations
- **Comprehensive tracing**: All operations captured by LangSmith for debugging

### Frontend (`frontend/src/`)
- **App.js**: Main chat interface component with message history for OSINT research
- **App.css**: Chat UI styling (clean, modern chat interface)
- React 18 with Axios for API communication

### Key API Endpoints
- `POST /chat`: Main OSINT research endpoint accepting `{"message": "text", "max_steps": 3}`
- `POST /research`: Alias for chat endpoint
- `GET /health`: Service health status
- `GET /`: API info and health check

### Temporal Workflows (Optional)
- **DeepResearchWorkflow**: Multi-step OSINT research with state persistence
- **Worker Bootstrap**: Temporal worker for background research tasks

## Environment Setup

Requires `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=autospook
```

Copy from `env.example` template.

## Agent Architecture

The LangGraph agent follows a simple conversational flow:
1. Receives user message via FastAPI endpoint
2. Processes through LangGraph workflow
3. Uses OpenAI GPT-3.5-turbo for response generation
4. Returns response with LangSmith tracing

The agent is designed to be extensible - additional nodes can be added to the LangGraph workflow for more sophisticated capabilities.