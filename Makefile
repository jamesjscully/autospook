.PHONY: install run dev stop restart kill-port clean baml-generate help docker-build docker-run docker-test deploy security-check

SHELL := /bin/bash

# Configuration
PROJECT_ID ?= we-relate-1
REGION ?= us-central1
SERVICE_NAME = autospook
IMAGE_NAME = gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)

# Default target
help:
	@echo "AutoSpook - OSINT Intelligence Gathering Service"
	@echo ""
	@echo "Development Commands:"
	@echo "  install       - Install Python dependencies"
	@echo "  run           - Run Flask application (loads .env)"
	@echo "  dev           - Run in development mode (loads .env)"
	@echo "  stop          - Stop the Flask server"
	@echo "  restart       - Restart the Flask application"
	@echo "  kill-port     - Kill any process running on port 5000"
	@echo "  test-env      - Test loading environment variables"
	@echo "  baml-generate - Regenerate BAML client code"
	@echo "  clean         - Clean up Python cache files"
	@echo "  setup         - Full setup: install dependencies and run"
	@echo ""
	@echo "Security & Testing:"
	@echo "  security-check - Run security vulnerability scans"
	@echo "  test          - Run application tests"
	@echo "  test-deployment - Test deployment readiness"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build  - Build Docker container"
	@echo "  docker-run    - Run container locally"
	@echo "  docker-test   - Test container locally"
	@echo "  docker-push   - Push container to registry"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy        - Deploy to Google Cloud Run"
	@echo "  deploy-test   - Deploy to test environment"
	@echo "  logs          - View Cloud Run logs"
	@echo ""
	@echo "Token Management:"
	@echo "  generate-token NAME - Generate new auth token"
	@echo "  list-tokens   - List all active tokens"
	@echo "  revoke-token TOKEN - Revoke a specific token"
	@echo "  validate-token TOKEN - Validate a token"
	@echo "  help          - Show this help message"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@if [ -d "venv313" ]; then \
		echo "Using virtual environment venv313..."; \
		source venv313/bin/activate && pip install -r requirements.txt; \
	else \
		pip install -r requirements.txt; \
	fi
	@echo "Dependencies installed successfully!"
	@echo "Note: Set OPENAI_API_KEY environment variable to use OSINT analysis"

# Kill any existing server on port 5000
kill-port:
	@echo "Checking for processes on port 5000..."
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || echo "No processes found on port 5000"

# Run the application (kill existing first)
run: kill-port
	@echo "Starting AutoSpook..."
	@if [ -d "venv313" ]; then \
		echo "Using virtual environment venv313..."; \
		if [ -f .env ]; then \
			echo "Loading environment variables from .env..."; \
			export $$(grep -v '^#' .env | xargs) && source venv313/bin/activate && python app.py; \
		else \
			echo "No .env file found, running without environment variables..."; \
			source venv313/bin/activate && python app.py; \
		fi; \
	else \
		if [ -f .env ]; then \
			echo "Loading environment variables from .env..."; \
			export $$(grep -v '^#' .env | xargs) && python app.py; \
		else \
			echo "No .env file found, running without environment variables..."; \
			python app.py; \
		fi; \
	fi

# Run in development mode (kill existing first)
dev: kill-port
	@echo "Starting AutoSpook in development mode..."
	@if [ -d "venv313" ]; then \
		echo "Using virtual environment venv313..."; \
		if [ -f .env ]; then \
			echo "Loading environment variables from .env..."; \
			export $$(grep -v '^#' .env | xargs) && source venv313/bin/activate && FLASK_ENV=development FLASK_DEBUG=1 python app.py; \
		else \
			echo "No .env file found, running without environment variables..."; \
			source venv313/bin/activate && FLASK_ENV=development FLASK_DEBUG=1 python app.py; \
		fi; \
	else \
		if [ -f .env ]; then \
			echo "Loading environment variables from .env..."; \
			export $$(grep -v '^#' .env | xargs) && FLASK_ENV=development FLASK_DEBUG=1 python app.py; \
		else \
			echo "No .env file found, running without environment variables..."; \
			FLASK_ENV=development FLASK_DEBUG=1 python app.py; \
		fi; \
	fi

# Stop the server
stop:
	@echo "Stopping AutoSpook server..."
	@-lsof -ti:5000 | xargs kill -9 2>/dev/null || echo "No server running on port 5000"
	@echo "Server stopped!"

# Restart the application
restart: stop run

# Test environment variables loading
test-env:
	@echo "Testing environment variables from .env file..."
	@if [ -f .env ]; then \
		echo "Found .env file, loading variables:"; \
		export $$(grep -v '^#' .env | xargs) && env | grep -E "(OPENAI_API_KEY|LANGCHAIN|GEMENI)" || echo "No matching environment variables found"; \
	else \
		echo "No .env file found"; \
	fi

# Regenerate BAML client code
baml-generate:
	@echo "Regenerating BAML client..."
	@if [ -d "venv313" ]; then \
		echo "Using virtual environment venv313..."; \
		source venv313/bin/activate && baml-cli generate; \
	else \
		baml-cli generate; \
	fi
	@echo "BAML client regenerated!"

# Clean up cache files
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleanup complete!"

# Full setup and run
setup: install baml-generate run

# Quick development workflow
quick: baml-generate dev

# Security and Testing
security-check:
	@echo "Running security checks..."
	@if [ -d "venv313" ]; then \
		source venv313/bin/activate && pip install bandit safety; \
		echo "Running bandit security scan..."; \
		bandit -r . -f json -o security-report.json || true; \
		echo "Running safety check..."; \
		safety check; \
	else \
		echo "Virtual environment not found. Please run 'make install' first."; \
	fi

test:
	@echo "Running application tests..."
	@if [ -d "venv313" ]; then \
		source venv313/bin/activate && python -m pytest tests/ -v || echo "No tests found"; \
	else \
		echo "Virtual environment not found. Please run 'make install' first."; \
	fi

test-deployment:
	@echo "Running deployment tests..."
	@if [ -d "venv313" ]; then \
		source venv313/bin/activate && python test_deployment.py; \
	else \
		python test_deployment.py; \
	fi

# Docker Commands
docker-build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):latest .

docker-run:
	@echo "Running Docker container locally..."
	@if [ ! -f .env ]; then \
		echo "Warning: .env file not found. Using environment variables."; \
	fi
	docker run --rm -p 8080:8080 --env-file .env $(IMAGE_NAME):latest

docker-test:
	@echo "Testing Docker container..."
	docker run --rm $(IMAGE_NAME):latest python -c "import app; print('✅ Container test passed')"

docker-push:
	@echo "Pushing Docker image to registry..."
	@if [ "$(PROJECT_ID)" = "your-project-id" ]; then \
		echo "❌ Error: Set PROJECT_ID environment variable"; \
		echo "   export PROJECT_ID=your-google-cloud-project-id"; \
		exit 1; \
	fi
	docker tag $(IMAGE_NAME):latest $(IMAGE_NAME):latest
	docker push $(IMAGE_NAME):latest

# Cloud Deployment
deploy:
	@echo "Deploying to Google Cloud Run..."
	@if [ ! -f .env.production ]; then \
		echo "❌ Error: .env.production file required for deployment"; \
		echo "   Copy .env.example to .env.production and configure"; \
		exit 1; \
	fi
	@./deploy.sh

deploy-test:
	@echo "Deploying to test environment..."
	@if [ "$(PROJECT_ID)" = "your-project-id" ]; then \
		echo "❌ Error: Set PROJECT_ID environment variable"; \
		exit 1; \
	fi
	PROJECT_ID=$(PROJECT_ID)-test ./deploy.sh

logs:
	@echo "Fetching Cloud Run logs..."
	gcloud logs tail "projects/$(PROJECT_ID)/logs/run.googleapis.com%2Frequests" --limit=50

# Token Management Commands
generate-token:
	@if [ -z "$(NAME)" ]; then \
		echo "Usage: make generate-token NAME=username"; \
		exit 1; \
	fi
	@./generate_key.sh --generate $(NAME)

list-tokens:
	@./generate_key.sh --list

revoke-token:
	@if [ -z "$(TOKEN)" ]; then \
		echo "Usage: make revoke-token TOKEN=your_token_here"; \
		exit 1; \
	fi
	@./generate_key.sh --revoke $(TOKEN)

validate-token:
	@if [ -z "$(TOKEN)" ]; then \
		echo "Usage: make validate-token TOKEN=your_token_here"; \
		exit 1; \
	fi
	@./generate_key.sh --validate $(TOKEN)

cleanup-tokens:
	@./generate_key.sh --cleanup

# Environment setup for deployment
setup-gcp:
	@echo "Setting up Google Cloud Platform..."
	@echo "1. Install Google Cloud SDK if not already installed"
	@echo "2. Run: gcloud auth login"
	@echo "3. Run: gcloud config set project $(PROJECT_ID)"
	@echo "4. Run: gcloud services enable run.googleapis.com containerregistry.googleapis.com"
	@echo "5. Create .env.production with your API keys"
	@echo "6. Generate an auth token: make generate-token NAME=admin"
	@echo "7. Run: make deploy"