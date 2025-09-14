# Ultimate Fantasy Platform

A modern fantasy sports platform built with FastAPI (backend) and Next.js (frontend).

## 🚀 Quick Start

Get the entire application running locally in under 5 minutes:

```bash
# Clone the repository
git clone <repository-url>
cd ultimate-fantasy

# Option 1: Docker (Recommended)
docker-compose up --build

# Option 2: Local Development
./start-local.sh

# Option 3: Manual Setup (see detailed instructions below)

# Wait for services to start, then visit:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## ✅ Validation

Run the setup validation script to ensure everything is working:

```bash
./validate-setup.sh
```

This will check:
- ✅ Backend dependencies and startup
- ✅ Frontend dependencies and build
- ✅ Docker setup (if available)
- ✅ API endpoints functionality

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for local development:
  - Python 3.11+ with [uv](https://docs.astral.sh/uv/)
  - Node.js 20+
  - PostgreSQL 15+ (optional - SQLite fallback available)

## 🏗️ Architecture

```
├── backend/          # FastAPI application
│   ├── src/         # Source code
│   ├── tests/       # Test suite (100% passing)
│   └── alembic/     # Database migrations
├── frontend/        # Next.js application
│   ├── src/         # Source code
│   └── tests/       # Test suite
└── specs/           # API specifications
```

## 🐳 Docker Setup (Recommended)

### Full Stack Development
```bash
# Start all services (frontend, backend, database)
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Database Only (for local development)
```bash
# Start only PostgreSQL for local development
docker-compose -f docker-compose.dev.yml up -d

# Stop database
docker-compose -f docker-compose.dev.yml down
```

## 💻 Local Development Setup

### Quick Start Script
```bash
# Automated local setup
./start-local.sh
```

### Manual Setup

#### Backend Setup

```bash
cd backend

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ultimate_fantasy"
# OR use SQLite fallback: export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"

# Run database migrations (if using PostgreSQL)
uv run alembic upgrade head

# Start development server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Start development server
export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## 🧪 Running Tests

### Backend Tests (100% Passing)
```bash
cd backend

# Run all tests
uv run pytest

# Run specific test types
uv run pytest tests/unit/        # Unit tests
uv run pytest tests/integration/ # Integration tests
uv run pytest tests/contract/    # Contract tests
uv run pytest tests/perf/        # Performance tests

# Run with coverage
uv run pytest --cov=src
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint

# Format code
npm run format

### End-to-End (Playwright)
```bash
# Start backend and frontend, then run e2e
./scripts/e2e.sh

# Or run manually (in separate terminals):
# Terminal 1: backend
cd backend/src && uv run uvicorn main:app --host 127.0.0.1 --port 8000
# Terminal 2: frontend
cd frontend && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
# Terminal 3: tests
cd frontend && E2E_BASE_URL=http://127.0.0.1:3000 npm run test:e2e
```

### Visual Regression Tests
```bash
# Run visual tests (requires backend + frontend running)
cd frontend && npm run test:visual

# Generate baseline screenshots
./scripts/generate-visual-baselines.sh

# Update baselines after design changes
cd frontend && npm run test:visual:update
```

### JWT Dev Mode
- Backend supports `AUTH_MODE=dev` (default) with HS256 tokens using `AUTH_DEV_SECRET`.
- You can mint a dev token in Node:
```bash
node -e "const c=(s)=>Buffer.from(JSON.stringify(s)).toString('base64').replace(/=+/g,'').replace(/\+/g,'-').replace(/\//g,'_');const h=c({alg:'HS256',typ:'JWT'});const p=c({sub: require('crypto').randomUUID(), email:'user@example.com', name:'User'});const si=h+'.'+p;const sig=require('crypto').createHmac('sha256',process.env.AUTH_DEV_SECRET||'dev-secret').update(si).digest('base64').replace(/=+/g,'').replace(/\+/g,'-').replace(/\//g,'_');console.log(si+'.'+sig)"
```
Set this token into the browser using `localStorage.setItem('uf_token', '<token>')` for the frontend to send `Authorization` headers.

### Dev Auth Token (UI Helper)
- Purpose: Generate a dev JWT (HS256) entirely in the browser and save it to `localStorage.uf_token` so the frontend automatically sends `Authorization: Bearer <token>`.
- Where: A "Dev Auth Token" panel appears on these pages: Leagues list (`/leagues`), Create League, League Public page, and Set Lineup.
- How it works:
  - Uses Web Crypto to compute a HS256 signature; no network calls are made.
  - Subject (`sub`) is the user ID. Defaults to a random UUID; you can paste your own.
  - Secret must match the backend `AUTH_DEV_SECRET` (default `dev-secret` when not set elsewhere).
  - Clicking "Generate & Save" writes the token to `localStorage.uf_token`; the frontend client reads it automatically.
- Steps:
  1) Ensure backend runs with `AUTH_MODE=dev` and set `AUTH_DEV_SECRET` (optional).
  2) Open a page with the panel; confirm or edit Subject and Secret.
  3) Click "Generate & Save". You can "Clear Token" to remove it.
- Troubleshooting:
  - 401 Unauthorized: The token is missing or signed with the wrong secret. Regenerate with the same `AUTH_DEV_SECRET` as the backend.
  - Switching users: regenerate with a different Subject UUID.
  - Production: Do NOT use this helper in production; it is for local/dev only.
```

## 🌐 API Documentation

Once the backend is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### API Quick Examples

List your leagues (requires a dev or real JWT):

```bash
export TOKEN="<jwt>"
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:8000/me/leagues | jq
```

List league members:

```bash
LEAGUE_ID=00000000-0000-0000-0000-000000000000
curl -sS http://localhost:8000/leagues/$LEAGUE_ID/members | jq
```

List waivers:

```bash
LEAGUE_ID=00000000-0000-0000-0000-000000000000
curl -sS "http://localhost:8000/waivers?league_id=$LEAGUE_ID&limit=50&offset=0" | jq
```

List lineups for a team:

```bash
TEAM_ID=00000000-0000-0000-0000-000000000000
curl -sS "http://localhost:8000/lineups?team_id=$TEAM_ID&game_day=2025-01-01" | jq
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ultimate_fantasy
DEBUG=true
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Database Setup

#### Using Docker (Recommended)
```bash
# Start PostgreSQL container
docker-compose -f docker-compose.dev.yml up -d postgres
```

#### Manual PostgreSQL Setup
```bash
# Install PostgreSQL
# Ubuntu/Debian: sudo apt install postgresql postgresql-contrib
# macOS: brew install postgresql

# Create database
createdb ultimate_fantasy

# Set connection string
export DATABASE_URL="postgresql://username:password@localhost:5432/ultimate_fantasy"
```

## 📊 Development Workflow

### 1. Start Database
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Backend Development
```bash
cd backend
uv run uvicorn main:app --reload
```

### 3. Frontend Development
```bash
cd frontend
npm run dev
```

### 4. Run Tests
```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm test
```

## 🚀 Production Deployment

### Build Production Images
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Environment Setup
Create production environment files:

```bash
# .env.production
DATABASE_URL=postgresql://user:pass@prod-db:5432/ultimate_fantasy
DEBUG=false
```

## 🛠️ Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Kill process or use different ports
```

#### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps

# Check connection
psql postgresql://postgres:postgres@localhost:5432/ultimate_fantasy
```

#### Permission Issues (Linux/WSL)
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Reset Everything
```bash
# Stop all containers and remove volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
docker-compose up --build
```

## 📝 API Usage Examples

### Create a League
```bash
curl -X POST "http://localhost:8000/leagues" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(node -e "const c=(s)=>Buffer.from(JSON.stringify(s)).toString('base64').replace(/=+/g,'').replace(/\+/g,'-').replace(/\//g,'_');const h=c({alg:'HS256',typ:'JWT'});const p=c({sub: require('crypto').randomUUID()});const si=h+'.'+p;const sig=require('crypto').createHmac('sha256',process.env.AUTH_DEV_SECRET||'dev-secret').update(si).digest('base64').replace(/=+/g,'').replace(/\+/g,'-').replace(/\//g,'_');console.log(si+'.'+sig)")" \
  -d '{
    "name": "My Fantasy League",
    "sport": "basketball",
    "league_type": "head_to_head",
    "season": "2025"
  }'
```

### Join a League
```bash
curl -X POST "http://localhost:8000/leagues/{league_id}/join" \
  -H "Authorization: Bearer $TOKEN"
```

### Set Lineup
```bash
curl -X PUT "http://localhost:8000/lineups" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "team_id": "team-uuid",
    "game_day": "2025-01-15",
    "players": [
      {"player_id": "player-uuid-1", "position": "G"},
      {"player_id": "player-uuid-2", "position": "F"}
    ]
  }'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `uv run pytest` (backend) and `npm test` (frontend)
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

- **Issues**: Create an issue in the repository
- **Documentation**: Check `/docs` folder for detailed documentation
- **API Reference**: http://localhost:8000/docs when running locally
