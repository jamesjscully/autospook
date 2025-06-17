#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[DEV_LAUNCH]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DEV_LAUNCH]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DEV_LAUNCH]${NC} $1"
}

print_error() {
    echo -e "${RED}[DEV_LAUNCH]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    print_warning "Shutting down services..."
    
    # Stop the main services
    if [[ ! -z "$BACKEND_PID" ]]; then
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
        print_status "Backend stopped (PID: $BACKEND_PID)"
    fi
    if [[ ! -z "$FRONTEND_PID" ]]; then
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
        print_status "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    
    # Stop the display processes
    if [[ ! -z "$BACKEND_DISPLAY_PID" ]]; then
        kill $BACKEND_DISPLAY_PID 2>/dev/null
    fi
    if [[ ! -z "$FRONTEND_DISPLAY_PID" ]]; then
        kill $FRONTEND_DISPLAY_PID 2>/dev/null
    fi
    
    # Clean up named pipes
    if [[ -p "$BACKEND_PIPE" ]]; then
        rm -f "$BACKEND_PIPE"
    fi
    if [[ -p "$FRONTEND_PIPE" ]]; then
        rm -f "$FRONTEND_PIPE"
    fi
    
    # Kill any remaining background jobs
    jobs -p | xargs -r kill 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_success "🚀 Starting AutoSpook Agent Development Environment"

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_warning "⚠️  .env file not found. Please copy env.example to .env and configure your API keys."
    print_status "Run: cp env.example .env"
    exit 1
fi

# Export environment variables from .env file
print_status "🔧 Loading environment variables from .env..."
set -a  # automatically export all variables
source .env
set +a  # stop automatically exporting

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "❌ uv is not installed. Please install it first."
    print_status "Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if node/npm is installed
if ! command -v npm &> /dev/null; then
    print_error "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

# Install backend dependencies if needed
print_status "📦 Checking backend dependencies..."
uv sync

# Install frontend dependencies if needed
print_status "📦 Checking frontend dependencies..."
cd frontend
if [[ ! -d "node_modules" ]]; then
    print_status "Installing frontend dependencies..."
    npm install
fi
cd ..

print_success "✅ Dependencies ready"

# Create named pipes for capturing output
BACKEND_PIPE=$(mktemp -u)
FRONTEND_PIPE=$(mktemp -u)
mkfifo "$BACKEND_PIPE"
mkfifo "$FRONTEND_PIPE"

# Function to prefix and display output
display_backend_output() {
    while IFS= read -r line; do
        echo -e "${BLUE}[BACKEND]${NC} $line"
    done < "$BACKEND_PIPE"
}

display_frontend_output() {
    while IFS= read -r line; do
        echo -e "${GREEN}[FRONTEND]${NC} $line"
    done < "$FRONTEND_PIPE"
}

# Start output display functions in background
display_backend_output &
BACKEND_DISPLAY_PID=$!

display_frontend_output &
FRONTEND_DISPLAY_PID=$!

# Start backend server
print_status "🔧 Starting backend server (FastAPI)..."
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001 > "$BACKEND_PIPE" 2>&1 &
BACKEND_PID=$!
print_success "✅ Backend started (PID: $BACKEND_PID) - http://localhost:8001"

# Wait a moment for backend to start
sleep 2

# Start frontend server
print_status "⚛️  Starting frontend server (React)..."
cd frontend
npm start > "$FRONTEND_PIPE" 2>&1 &
FRONTEND_PID=$!
cd ..
print_success "✅ Frontend started (PID: $FRONTEND_PID) - http://localhost:3000"

print_success "🎉 Both services are running!"
print_status "📱 Frontend: http://localhost:3000"
print_status "🔌 Backend API: http://localhost:8001"
print_status "📚 API Docs: http://localhost:8001/docs"
print_warning "Press Ctrl+C to stop all services"

# Wait for user to stop services
wait $BACKEND_PID $FRONTEND_PID 