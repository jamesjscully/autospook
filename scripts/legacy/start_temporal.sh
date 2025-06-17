#!/bin/bash

echo "Starting Temporal-based AutoSpook..."

# Start Temporal server and dependencies
echo "Starting Temporal server..."
docker-compose -f docker-compose.temporal.yml up -d

# Wait for Temporal to be ready
echo "Waiting for Temporal server to be ready..."
sleep 10

# Check if Temporal is running
while ! curl -s http://localhost:7233 > /dev/null; do
    echo "Waiting for Temporal server..."
    sleep 5
done

echo "Temporal server is ready!"

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync

# Start the Temporal worker in background
echo "Starting Temporal worker..."
uv run python -m backend.worker &
WORKER_PID=$!

# Start the FastAPI application
echo "Starting FastAPI application..."
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "AutoSpook is running!"
echo "- FastAPI: http://localhost:8000"
echo "- Temporal UI: http://localhost:8080"
echo "- Frontend: Start with 'cd frontend && npm start'"

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $WORKER_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    docker-compose -f docker-compose.temporal.yml down
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait