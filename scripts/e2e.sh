#!/usr/bin/env bash
set -eo pipefail

export AUTH_MODE=${AUTH_MODE:-dev}
export AUTH_DEV_SECRET=${AUTH_DEV_SECRET:-test-e2e-secret}
export NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}

echo "Starting backend (uvicorn) and frontend (Next.js) for E2E..."

# Start backend
(
  cd backend/src
  uv run uvicorn main:app --host 127.0.0.1 --port 8000 &
)
BACK_PID=$!

# Start frontend
(
  cd frontend
  npm run dev -- --port 3000 &
)
FRONT_PID=$!

echo "Waiting for servers..."
ATTEMPTS=60
until curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null 2>&1; do
  ((ATTEMPTS--)) || { echo "Backend failed to start"; kill $BACK_PID $FRONT_PID 2>/dev/null || true; exit 1; }
  sleep 1
done

ATTEMPTS=60
until curl -fsS http://127.0.0.1:3000 >/dev/null 2>&1; do
  ((ATTEMPTS--)) || { echo "Frontend failed to start"; kill $BACK_PID $FRONT_PID 2>/dev/null || true; exit 1; }
  sleep 1
done

echo "Running Playwright tests..."
(
  cd frontend
  npx playwright install --with-deps || true
  E2E_BASE_URL=http://127.0.0.1:3000 npm run test:e2e
)

echo "Stopping servers..."
kill $BACK_PID $FRONT_PID 2>/dev/null || true

echo "E2E completed."

