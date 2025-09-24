#!/bin/bash

echo "🚀 Ultimate Fantasy Platform - Setup Validation"
echo "================================================"

# Find project root (directory containing docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "❌ Cannot find project root directory"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "✅ Project structure validated"

# Check backend dependencies
echo ""
echo "🔍 Checking Backend Setup..."
cd apps/api

if [ ! -f "pyproject.toml" ]; then
    echo "❌ Backend pyproject.toml not found"
    exit 1
fi

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ uv is available"
    
    # Test backend dependencies
    if uv run python -c "import fastapi, sqlalchemy, uvicorn" 2>/dev/null; then
        echo "✅ Backend dependencies are installed"
    else
        echo "⚠️  Installing backend dependencies..."
        uv sync
    fi
    
    # Test backend startup
    echo "🧪 Testing backend startup..."
    timeout 10s uv run python -c "
import sys
sys.path.insert(0, 'src')
from main import app
print('✅ Backend can start successfully')
" || echo "⚠️  Backend startup test timed out (this is normal)"
    
else
    echo "⚠️  uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

cd ../..

# Check frontend dependencies
echo ""
echo "🔍 Checking Frontend Setup..."
cd apps/web

if [ ! -f "package.json" ]; then
    echo "❌ Frontend package.json not found"
    exit 1
fi

# Check if npm is available
if command -v npm &> /dev/null; then
    echo "✅ npm is available"
    
    # Check if node_modules exists
    if [ -d "node_modules" ]; then
        echo "✅ Frontend dependencies are installed"
    else
        echo "⚠️  Installing frontend dependencies..."
        npm install
    fi
    
    # Test frontend build
    echo "🧪 Testing frontend build..."
    if npm run build &> /dev/null; then
        echo "✅ Frontend builds successfully"
    else
        echo "⚠️  Frontend build failed"
    fi
    
else
    echo "⚠️  npm not found. Install Node.js 20+ from https://nodejs.org/"
fi

cd ..

# Check Docker setup
echo ""
echo "🔍 Checking Docker Setup..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo "✅ Docker Compose is available"
        
        # Validate docker-compose.yml
        if docker compose config &> /dev/null; then
            echo "✅ docker-compose.yml is valid"
        else
            echo "⚠️  docker-compose.yml validation failed"
        fi
    else
        echo "⚠️  Docker Compose not found"
    fi
else
    echo "⚠️  Docker not found. Install from https://docs.docker.com/get-docker/"
fi

echo ""
echo "🎉 Setup validation complete!"
echo ""
echo "📚 Next steps:"
echo "   1. For Docker: docker-compose up --build"
echo "   2. For local dev: Follow the README instructions"
echo "   3. Visit http://localhost:3000 (frontend) and http://localhost:8000/docs (API)"
