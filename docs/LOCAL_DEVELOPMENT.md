# Local Development Guide

This guide covers how to run the Ultimate Fantasy Platform locally, including all components: database, API, web frontend, mobile app, and landing page.

## Quick Start

### Prerequisites

- **Node.js** (v20+) for web and mobile apps
- **Python** (3.11+) for the backend API
- **uv** for Python package management
- **Expo CLI** for mobile development (optional)
- **Docker** for PostgreSQL (optional, falls back to SQLite)

### One-Command Startup

From the project root directory, you have two options:

#### Option 1: Simple Script

```bash
./scripts/start-local.sh
```

This script will automatically:

1. Clean up any existing processes on ports 3000, 8000, 3001
2. Start PostgreSQL with Docker (or use SQLite fallback)
3. Start the FastAPI backend on port 8000
4. Start the Next.js frontend on port 3000
5. Start the Expo mobile development server
6. Start a static server for the landing page on port 3001

#### Option 2: Tmux Development Environment (Recommended)

```bash
./scripts/start-with-tmux.sh
```

This creates a tmux session with dedicated windows for each service:

- **Window 1**: Live status dashboard with auto-refresh
- **Window 2**: Database monitoring and management
- **Window 3**: FastAPI backend (port 8000)
- **Window 4**: Next.js frontend (port 3000)
- **Window 5**: Expo mobile app
- **Window 6**: Static landing page (port 3001)

**Benefits:**

- Real-time monitoring of all services
- Dedicated database management window
- Easy switching between service logs
- Persistent session (detach with Ctrl+B, D)

**📖 See [Tmux Development Guide](../TMUX_README.md) for detailed usage**

## Components Overview

### 🗄️ Database

- **PostgreSQL** (preferred): Runs in Docker container on port 5432
- **SQLite** (fallback): Local file `ultimate_fantasy.db` in API directory
- **Auto-detection**: Script tests PostgreSQL connection and falls back to SQLite if needed

### 🔧 API Backend (`apps/api`)

- **Framework**: FastAPI with SQLAlchemy
- **Port**: 8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Database**: Auto-configured based on availability

### 🎨 Web Frontend (`apps/web`)

- **Framework**: Next.js 15 with React 19
- **Port**: 3000
- **URL**: http://localhost:3000
- **API Integration**: Connects to backend at `http://localhost:8000`

### 📱 Mobile App (`apps/mobile`)

- **Framework**: Expo with React Native
- **Development**: Use Expo Go app to scan QR code
- **Platform Support**: iOS, Android, Web
- **API Integration**: Connects to backend at `http://localhost:8000`

### 🌐 Landing Page (`apps/landing`)

- **Type**: Static HTML/CSS/JS
- **Port**: 3001
- **URL**: http://localhost:3001
- **Server**: Python's built-in HTTP server

## Manual Setup (Component by Component)

### 1. Database Setup

#### Option A: PostgreSQL with Docker (Recommended)

```bash
docker compose -f docker-compose.dev.yml up -d
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/ultimate_fantasy"
```

#### Option B: SQLite (Fallback)

```bash
export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"
```

### 2. Backend API

```bash
cd apps/api
uv sync --all-extras
export DATABASE_URL="${DATABASE_URL:-sqlite+pysqlite:///ultimate_fantasy.db}"
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Web Frontend

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev -- --port 3000
```

### 4. Mobile App

```bash
cd apps/mobile
npm install
npm start
```

### 5. Landing Page

```bash
cd apps/landing
python3 -m http.server 3001
```

## Environment Variables

### Backend API

- `DATABASE_URL`: Database connection string
- `DATABASE_ASYNC`: Enable async mode (`true`/`false`)

### Web Frontend

- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL (default: `http://localhost:8000`)

### Mobile App

- Uses the same backend API at `http://localhost:8000`
- Additional configuration in `app.json` for Expo settings

## Port Configuration

| Service      | Port    | URL                   | Purpose            |
| ------------ | ------- | --------------------- | ------------------ |
| Backend API  | 8000    | http://localhost:8000 | FastAPI server     |
| Web Frontend | 3000    | http://localhost:3000 | Next.js app        |
| Landing Page | 3001    | http://localhost:3001 | Static site        |
| PostgreSQL   | 5432    | localhost:5432        | Database           |
| Mobile       | Dynamic | Expo Dev Tools        | Development server |

## Development Differences from Production

### Database

- **Local**: Uses SQLite by default, PostgreSQL optional
- **Production**: Uses managed PostgreSQL

### API Configuration

- **Local**: Debug mode enabled, auto-reload on changes
- **Production**: Production optimizations, no auto-reload

### Frontend Build

- **Local**: Development build with hot reloading
- **Production**: Optimized build with minification

### Mobile Development

- **Local**: Expo development server with hot reloading
- **Production**: Standalone app builds for app stores

### CORS Settings

- **Local**: Allows localhost origins
- **Production**: Restricted to production domains

## Troubleshooting

### Port Already in Use

```bash
# Kill processes on specific ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

### Database Connection Issues

1. Check if PostgreSQL is running: `docker ps`
2. Check connection: `pg_isready -h localhost -p 5432`
3. Fallback to SQLite: `export DATABASE_URL="sqlite+pysqlite:///ultimate_fantasy.db"`

### Dependencies Issues

```bash
# Backend
cd apps/api && uv sync --all-extras

# Frontend
cd apps/web && npm install

# Mobile
cd apps/mobile && npm install
```

### Expo/Mobile Issues

```bash
# Clear Expo cache
cd apps/mobile && npx expo start --clear

# Install Expo CLI globally
npm install -g @expo/cli
```

## Testing Locally

### Backend API Tests

```bash
cd apps/api
uv run pytest
```

### Frontend Tests

```bash
cd apps/web
npm run test
npm run test:e2e
```

### Mobile Tests

```bash
cd apps/mobile
npm test
```

## Development Tools

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Checks

- **API Health**: http://localhost:8000/health
- **Services Health**: http://localhost:8000/health/services
- **System Info**: http://localhost:8000/system/info

### Frontend Development

- **Component Library**: `npm run play:ui` (port 8080)
- **Storybook**: Available in web app

## Stopping Services

The `scripts/start-local.sh` script handles cleanup automatically with Ctrl+C, but you can also manually stop services:

```bash
# Kill all Ultimate Fantasy processes
pkill -f "uvicorn.*8000"
pkill -f "next dev"
pkill -f "expo start"
pkill -f "python.*http.server.*3001"

# Stop Docker containers
docker compose -f docker-compose.dev.yml down
```

## Performance Considerations

### Local Development Optimizations

- Backend uses SQLite for faster startup
- Frontend runs in development mode with hot reloading
- Mobile uses Expo Go for instant updates
- Database migrations run automatically for SQLite

### Resource Usage

- **Memory**: ~2-3GB total for all services
- **CPU**: Moderate during startup, low during idle
- **Disk**: ~500MB for dependencies + database storage

## Next Steps

After getting the local environment running:

1. Visit the frontend at http://localhost:3000
2. Check the API docs at http://localhost:8000/docs
3. Download Expo Go app and scan the QR code for mobile testing
4. View the landing page at http://localhost:3001
5. Start developing! Changes will hot-reload automatically.
