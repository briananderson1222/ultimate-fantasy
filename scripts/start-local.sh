#!/bin/bash

echo "🚀 Starting Ultimate Fantasy Platform Locally"
echo "=============================================="

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
import os
from sqlalchemy import create_engine, text

database_url = os.getenv('DATABASE_URL')
engine = create_engine(database_url, future=True)
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'⚠️  PostgreSQL connection failed: {e}')
    raise SystemExit(1)
" 2>/dev/null; then
        echo "🔄 Switching to SQLite fallback..."
        export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"
    fi
fi

echo "📊 Using database: $DATABASE_URL"

# Start backend in background
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID) - http://localhost:8000"

cd ../..

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

cd ../..

# Start mobile app (optional)
echo "📱 Starting Mobile App..."
cd apps/mobile

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing mobile dependencies..."
    npm install
fi

# Check if Expo CLI is available
if command -v expo &> /dev/null || command -v npx &> /dev/null; then
    echo "📱 Starting Expo development server..."
    npm start &
    MOBILE_PID=$!
    echo "✅ Mobile app started (PID: $MOBILE_PID) - Use Expo Go app to scan QR code"
else
    echo "⚠️  Expo CLI not available. Skipping mobile app startup."
    MOBILE_PID=""
fi

cd ../..

# Start landing page (static server)
echo "🌐 Starting Landing Page..."
cd apps/landing

# Simple static server for landing page
if command -v python3 &> /dev/null; then
    python3 -m http.server 3001 &
    LANDING_PID=$!
    echo "✅ Landing page started (PID: $LANDING_PID) - http://localhost:3001"
elif command -v python &> /dev/null; then
    python -m http.server 3001 &
    LANDING_PID=$!
    echo "✅ Landing page started (PID: $LANDING_PID) - http://localhost:3001"
else
    echo "⚠️  Python not available. Skipping landing page startup."
    LANDING_PID=""
fi

cd ../..

echo ""
echo "🎉 Ultimate Fantasy Platform is running!"
echo "========================================"
echo "Frontend:     http://localhost:3000"
echo "Backend:      http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Landing Page: http://localhost:3001"
echo "Mobile:       Use Expo Go app to scan QR code"
echo ""
echo "Press Ctrl+C to stop all services"

# Build PID list for cleanup
PIDS="$BACKEND_PID $FRONTEND_PID"
if [ ! -z "$MOBILE_PID" ]; then
    PIDS="$PIDS $MOBILE_PID"
fi
if [ ! -z "$LANDING_PID" ]; then
    PIDS="$PIDS $LANDING_PID"
fi

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $PIDS 2>/dev/null; exit 0' INT

# Keep script running
wait