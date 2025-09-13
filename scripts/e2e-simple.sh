#!/usr/bin/env bash
set -e

export AUTH_MODE=${AUTH_MODE:-dev}
export AUTH_DEV_SECRET=${AUTH_DEV_SECRET:-test-e2e-secret}
export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"

echo "🧹 Cleaning up any existing processes..."
pkill -f "uvicorn.*8000" || true
pkill -f "next.*3000" || true
sleep 2

echo "🚀 Starting backend on port 8000..."
cd backend/src
uv run uvicorn main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!
cd ../..

echo "🎨 Starting frontend on port 3000..."
cd frontend
npm run dev -- --port 3000 &
FRONT_PID=$!
cd ..

echo "⏳ Waiting for services to start..."
sleep 10

echo "🧪 Testing backend..."
if curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
    kill $BACK_PID $FRONT_PID 2>/dev/null || true
    exit 1
fi

echo "🧪 Testing frontend..."
if curl -fsS http://127.0.0.1:3000 >/dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend failed to start"
    kill $BACK_PID $FRONT_PID 2>/dev/null || true
    exit 1
fi

echo "🎭 Running Playwright e2e tests..."
cd frontend
E2E_BASE_URL=http://127.0.0.1:3000 npm run test:e2e
cd ..

echo "🛑 Stopping services..."
kill $BACK_PID $FRONT_PID 2>/dev/null || true

echo "✅ E2E tests completed!"
