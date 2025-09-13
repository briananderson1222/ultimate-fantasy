#!/usr/bin/env bash
set -e

export AUTH_MODE=dev
export AUTH_DEV_SECRET=test-e2e-secret
export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"

echo "🧹 Cleaning up..."
pkill -f "uvicorn.*800" || true
pkill -f "next.*300" || true
sleep 2

echo "🚀 Starting backend..."
cd backend/src
uv run uvicorn main:app --host 127.0.0.1 --port 8000 &
BACK_PID=$!
cd ../..

echo "🎨 Starting frontend..."
cd frontend
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --port 3000 &
FRONT_PID=$!
cd ..

echo "⏳ Waiting for services..."
sleep 20

echo "🧪 Running e2e tests..."
cd frontend
E2E_BASE_URL=http://127.0.0.1:3000 npx playwright test --project=chromium
cd ..

echo "🛑 Cleanup..."
kill $BACK_PID $FRONT_PID 2>/dev/null || true

echo "✅ E2E complete!"
