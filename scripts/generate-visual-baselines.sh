#!/bin/bash

# Generate baseline screenshots for visual regression tests
set -e

echo "🎨 Generating visual test baselines..."

cd "$(dirname "$0")/../frontend"

# Check if backend is running
if ! curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null 2>&1; then
  echo "❌ Backend not running. Please start backend first:"
  echo "   cd backend/src && uv run uvicorn main:app --host 127.0.0.1 --port 8000"
  exit 1
fi

# Check if frontend is running
if ! curl -fsS http://127.0.0.1:3000 >/dev/null 2>&1; then
  echo "❌ Frontend not running. Please start frontend first:"
  echo "   cd frontend && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev"
  exit 1
fi

echo "✅ Services are running, generating baselines..."

# Generate baseline screenshots
npm run test:visual:update

echo "✅ Visual baselines generated successfully!"
echo "📁 Screenshots saved to: tests/e2e/visual.spec.ts-snapshots/"
echo ""
echo "💡 To run visual tests: npm run test:visual"
echo "💡 To update baselines: npm run test:visual:update"
