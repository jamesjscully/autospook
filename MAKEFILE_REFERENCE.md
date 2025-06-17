# AutoSpook Makefile Reference

## Quick Start Commands

```bash
make           # Show help
make dev       # Start full development environment
make install   # Install all dependencies
make health    # Check service status
make stop      # Stop all services
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start full development environment (backend + frontend) |
| `make dev-backend` | Start only backend server |
| `make dev-frontend` | Start only frontend server |
| `make install` | Install Python and Node.js dependencies |
| `make check-deps` | Verify required tools are installed |
| `make setup-env` | Create .env file from template |

## Temporal Workflow Commands

| Command | Description |
|---------|-------------|
| `make temporal-start` | Start Temporal infrastructure (Docker) |
| `make temporal-stop` | Stop Temporal infrastructure |
| `make temporal-dev` | Development with Temporal workflows |
| `make temporal-demo` | Run workflow demonstration |

## Code Quality Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (Python + Frontend) |
| `make audit` | Run security audits (Python + NPM) |
| `make lint` | Run linting on all code |
| `make format` | Format all code (Black + Ruff) |

## Utility Commands

| Command | Description |
|---------|-------------|
| `make health` | Check health of running services |
| `make logs` | Show logs from running services |
| `make clean` | Clean up logs, cache, build artifacts |
| `make stop` | Stop all running services |
| `make build` | Build production assets |

## Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Temporal UI**: http://localhost:8080 (when running)

## Migration from Shell Scripts

| Old Script | New Command |
|------------|-------------|
| `./dev_launch.sh` | `make dev` |
| `./start_temporal.sh` | `make temporal-dev` |
| `./start.sh` | `make temporal-demo` |

## Development Workflow

```bash
# 1. Initial setup
make install
make setup-env  # Edit .env with your API keys

# 2. Start development
make dev        # Starts both frontend and backend

# 3. In separate terminal, check status
make health

# 4. View logs if needed
make logs

# 5. Stop when done
make stop
```

## Temporal Workflow Development

```bash
# 1. Start Temporal infrastructure
make temporal-start

# 2. Start development with workflows
make temporal-dev

# 3. Access Temporal UI at http://localhost:8080

# 4. Run demo workflow (separate terminal)
make temporal-demo

# 5. Stop everything
make temporal-stop
```