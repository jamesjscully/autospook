#!/bin/bash

echo "🚀 Starting AutoSpook - Temporal + LangGraph"

# Check if Temporal is running
if ! curl -s http://localhost:7233 > /dev/null; then
    echo "⚠️  Temporal server not running. Please start Temporal first:"
    echo "   temporal server start-dev"
    exit 1
fi

echo "✅ Temporal server is running"

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Start worker in background
echo "👷 Starting Temporal worker..."
uv run python -m backend.worker &
WORKER_PID=$!

# Wait a moment for worker to start
sleep 2

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo ""
echo "🎉 AutoSpook is running!"
echo "   API: http://localhost:8000"
echo "   Temporal UI: http://localhost:8233"
echo ""
echo "Example usage:"
echo "curl -X POST http://localhost:8000/investigate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"target\": \"John Doe\", \"context\": \"Security investigation\"}'"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WORKER_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for processes
wait