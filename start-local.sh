#!/bin/bash

echo "🚀 Starting Ultimate Fantasy Platform Locally"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Kill any processes using our ports (more thorough cleanup)
echo "🧹 Cleaning up ports..."
pkill -f "next dev" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start database with Docker (if available)
if command -v docker &> /dev/null && (command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1); then
    echo "🐳 Starting PostgreSQL with Docker..."
    docker compose -f docker-compose.dev.yml up -d --remove-orphans
    echo "⏳ Waiting for database to be ready..."
    sleep 5
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ultimate_fantasy"
else
    echo "⚠️  Docker not available. Using SQLite fallback."
    export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"
fi

# Start backend
echo "🔧 Starting Backend..."
cd apps/api
export DATABASE_URL="${DATABASE_URL:-sqlite+pysqlite:///ultimate_fantasy.db}"

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing backend dependencies..."
    uv sync --all-extras
fi

# Check if we can connect to PostgreSQL, fallback to SQLite if not
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "🔍 Testing PostgreSQL connection..."
    if ! uv run python -c "
import sys
sys.path.insert(0, 'src')
try:
    from services.db import get_engine
    engine = get_engine()
    with engine.connect() as conn:
        pass
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'⚠️  PostgreSQL connection failed: {e}')
    print('🔄 Switching to SQLite fallback...')
    raise SystemExit(1)
" 2>/dev/null; then
        echo "🔄 Switching to SQLite fallback..."
        export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"
    fi
fi

echo "📊 Using database: $DATABASE_URL"

# Start backend in background
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID) - http://localhost:8000"

cd ..

# Start frontend
echo "🎨 Starting Frontend..."
cd apps/web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"

# Start frontend in background
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000" npm run dev -- --port 3000 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID) - http://localhost:3000"

cd ..

echo ""
echo "🎉 Ultimate Fantasy Platform is running!"
echo "========================================"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Keep script running
wait
