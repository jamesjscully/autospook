#!/bin/bash

# AutoSpook Build Test Script
# Tests Docker build process and uv setup

set -e  # Exit on any error

echo "🚀 AutoSpook Build Test"
echo "======================="

# Check prerequisites
echo "📋 Checking Prerequisites..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install Docker to test builds."
    echo "   For Ubuntu: sudo apt install docker.io"
    echo "   For macOS: Install Docker Desktop"
    DOCKER_AVAILABLE=false
else
    echo "✅ Docker is available"
    DOCKER_AVAILABLE=true
fi

# Check if UV is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv &> /dev/null; then
        echo "✅ UV installed successfully"
    else
        echo "❌ UV installation failed"
        exit 1
    fi
else
    echo "✅ UV is available"
fi

# Test backend dependencies
echo ""
echo "🔧 Testing Backend Dependencies..."
cd backend

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found"
    exit 1
fi
echo "✅ pyproject.toml found"

# Test UV sync
echo "🔄 Testing UV dependency resolution..."
if uv lock; then
    echo "✅ UV lock successful - dependencies can be resolved"
else
    echo "❌ UV lock failed - dependency issues detected"
    exit 1
fi

# Test UV sync (install)
echo "🔄 Testing UV sync (install)..."
if uv sync; then
    echo "✅ UV sync successful - all dependencies installed"
else
    echo "❌ UV sync failed - installation issues detected"
    exit 1
fi

# Test LLM integration
echo "🤖 Testing LLM Integration..."
if uv run python test_llm_integration.py; then
    echo "✅ LLM integration test passed"
else
    echo "❌ LLM integration test failed"
    exit 1
fi

# Test frontend dependencies
echo ""
echo "🎨 Testing Frontend Dependencies..."
cd ../frontend

if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi
echo "✅ package.json found"

# Test npm install
echo "🔄 Testing npm install..."
if npm install; then
    echo "✅ npm install successful"
else
    echo "❌ npm install failed"
    exit 1
fi

# Test frontend build
echo "🔄 Testing frontend build..."
if npm run build; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Test Docker build if available
cd ..
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    echo "🐳 Testing Docker Build..."
    
    echo "🔄 Building Docker image..."
    if docker build -t autospook-test -f Dockerfile .; then
        echo "✅ Docker build successful"
        
        # Clean up test image
        echo "🧹 Cleaning up test image..."
        docker rmi autospook-test
    else
        echo "❌ Docker build failed"
        exit 1
    fi
else
    echo ""
    echo "⏭️  Skipping Docker build test (Docker not available)"
fi

# Test docker-compose validation
echo ""
echo "🔧 Testing Docker Compose Configuration..."
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    if docker-compose config &> /dev/null; then
        echo "✅ docker-compose.yml is valid"
    else
        echo "❌ docker-compose.yml validation failed"
        exit 1
    fi
else
    echo "⏭️  Skipping docker-compose validation (not available)"
fi

echo ""
echo "🎉 All Build Tests Passed!"
echo "========================="
echo ""
echo "✅ UV package management working"
echo "✅ Backend dependencies resolved"
echo "✅ LLM integration framework ready"
echo "✅ Frontend build successful"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "✅ Docker build successful"
fi
echo ""
echo "🚀 Ready for development and deployment!"
echo ""
echo "Next steps:"
echo "1. Configure API keys: backend/SETUP_API_KEYS.md"
echo "2. Run development: python dev_launch.py"
echo "3. Run production: docker-compose up" 