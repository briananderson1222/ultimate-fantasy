# Ultimate Fantasy Platform

A modern fantasy sports platform built with FastAPI (backend) and Next.js (frontend).

## 🚀 Quick Start

Get the entire application running locally in under 5 minutes:

```bash
# Clone the repository
git clone <repository-url>
cd ultimate-fantasy

# Start all services with Docker
docker-compose up --build

# Wait for services to start, then visit:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for local development:
  - Python 3.11+ with [uv](https://docs.astral.sh/uv/)
  - Node.js 20+
  - PostgreSQL 15+

## 🏗️ Architecture

```
├── backend/          # FastAPI application
│   ├── src/         # Source code
│   ├── tests/       # Test suite
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

### Backend Setup

```bash
cd backend

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ultimate_fantasy"

# Run database migrations (if using PostgreSQL)
uv run alembic upgrade head

# Start development server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Start development server
npm run dev
```

## 🧪 Running Tests

### Backend Tests
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
```

## 🌐 API Documentation

Once the backend is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ultimate_fantasy
DEBUG=true
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
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
  -H "x-user-id: $(uuidgen)" \
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
  -H "x-user-id: $(uuidgen)"
```

### Set Lineup
```bash
curl -X PUT "http://localhost:8000/lineups" \
  -H "Content-Type: application/json" \
  -H "x-user-id: $(uuidgen)" \
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
