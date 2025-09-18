# Ultimate Fantasy - Deployment Guide

This document outlines the deployment process for the Ultimate Fantasy Sports Platform, which consists of multiple applications in a monorepo structure.

## Architecture Overview

The platform uses a monorepo structure with the following applications:

- **Web** (`apps/web/`) - NextJS web application
- **API** (`apps/api/`) - Python FastAPI server
- **Mobile** (`apps/mobile/`) - React Native (Expo) mobile application
- **Landing** (`apps/landing/`) - Marketing website
- **Shared Packages** (`packages/`) - Cross-platform shared logic

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (for containerized deployments)
- Expo CLI (for mobile app builds)

## Shared Packages

The shared packages must be built before deploying any applications:

```bash
# Build all shared packages
npm run build:packages

# Or build individually
npm run build --workspace=packages/shared-logic
npm run build --workspace=packages/ui-components
npm run build --workspace=packages/api-client
```

## Web App Deployment (NextJS)

### Development
```bash
npm run dev:web
```

### Production Build
```bash
cd apps/web
npm run build
npm start
```

### Environment Variables
Create `.env.local` in the apps/web directory:
```
NEXT_PUBLIC_API_URL=https://api.ultimatefantasy.app
NEXT_PUBLIC_WS_URL=wss://api.ultimatefantasy.app/ws
```

### Deployment Platforms
- **Vercel** (Recommended): Connect repository and deploy automatically
- **Netlify**: Static site generation with API routes
- **Docker**: Use the provided Dockerfile

## API Deployment (FastAPI)

### Development
```bash
npm run dev:api
```

### Production Setup
```bash
cd apps/api
uv sync --all-extras
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir src
```

### Environment Variables
Create `.env` in the apps/api directory:
```
DATABASE_URL=postgresql://user:password@localhost/ultimatefantasy
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
API_ENVIRONMENT=production
```

### Deployment Platforms
- **Railway**: Python app deployment
- **Heroku**: Using Procfile
- **AWS ECS**: Containerized deployment
- **DigitalOcean App Platform**: Direct from repository

## Mobile App Deployment (React Native/Expo)

### Development
```bash
npm run dev:mobile
```

### Building for App Stores

#### Using EAS Build (Recommended)
```bash
cd apps/mobile

# Install EAS CLI
npm install -g @expo/eas-cli

# Configure EAS
eas build:configure

# Build for both platforms
eas build --platform all

# Submit to app stores
eas submit --platform ios
eas submit --platform android
```

#### Environment Variables
Create `app.config.js` in the mobile directory:
```javascript
export default {
  expo: {
    name: "Ultimate Fantasy",
    extra: {
      apiUrl: process.env.API_URL || "https://api.ultimatefantasy.app",
    },
  },
};
```

### Over-the-Air Updates
```bash
# Publish update
eas update --branch production --message "Bug fixes and improvements"
```

## Database Setup

### PostgreSQL
```sql
CREATE DATABASE ultimatefantasy;
CREATE USER uf_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ultimatefantasy TO uf_user;
```

### Redis
For caching and real-time features:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu
```

## Docker Deployment

### Full Stack with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Individual Services
```bash
# Web App
docker build -t uf-web ./apps/web
docker run -p 3000:3000 uf-web

# API
docker build -t uf-api ./apps/api
docker run -p 8000:8000 uf-api
```

## CI/CD Pipeline

### GitHub Actions
The repository includes GitHub Actions workflows for:

- **Shared Packages**: Build and test on every push
- **Frontend**: Deploy to Vercel on main branch
- **Backend**: Deploy to production server
- **Mobile**: Build and publish with EAS

### Key Workflows

1. **Package Build** (`.github/workflows/packages.yml`)
   - Runs on: Push to `packages/*`
   - Steps: Install, build, test shared packages

2. **Web Deploy** (`.github/workflows/web.yml`)
   - Runs on: Push to `main` branch
   - Steps: Build packages, build web app, deploy to Vercel

3. **API Deploy** (`.github/workflows/api.yml`)
   - Runs on: Push to `main` branch
   - Steps: Test, build Docker image, deploy to production

4. **Mobile Build** (`.github/workflows/mobile.yml`)
   - Runs on: Tag creation
   - Steps: Build packages, EAS build, submit to stores

## Monitoring and Logging

### Frontend
- **Vercel Analytics**: Built-in monitoring
- **Sentry**: Error tracking and performance monitoring

### Backend
- **FastAPI Metrics**: Built-in /metrics endpoint
- **Sentry**: Error tracking
- **Grafana**: Custom dashboards
- **Health Checks**: /health endpoint

### Mobile
- **Expo Analytics**: Built-in crash reporting
- **Sentry**: Cross-platform error tracking

## Security Considerations

1. **Environment Variables**: Never commit secrets
2. **API Authentication**: JWT tokens with refresh mechanism
3. **CORS**: Properly configured for production domains
4. **Rate Limiting**: Implemented in API gateway
5. **SSL/HTTPS**: Required for all production deployments

## Scaling Considerations

### Horizontal Scaling
- **Frontend**: CDN distribution (Vercel Edge Network)
- **Backend**: Load balancer with multiple instances
- **Database**: Read replicas for scaling reads
- **Redis**: Cluster mode for high availability

### Performance Optimization
- **Frontend**: Code splitting, image optimization, SSR
- **Backend**: Database indexing, caching layers
- **Mobile**: Bundle size optimization, lazy loading

## Rollback Procedures

### Frontend
```bash
# Vercel rollback
vercel rollback [deployment-url]
```

### Backend
```bash
# Docker rollback
docker tag uf-backend:previous uf-backend:latest
docker-compose up -d backend
```

### Mobile
```bash
# Expo rollback
eas update --branch production --message "Rollback to previous version"
```

## Maintenance

### Database Migrations
```bash
cd apps/api
uv run alembic upgrade head  # Apply latest migrations
uv run alembic downgrade -1  # Rollback one migration
```

### Package Updates
```bash
# Update all dependencies
npm update --workspaces

# Security audits
npm audit --audit-level moderate
```

### Monitoring Health
- Check application health endpoints
- Monitor error rates and response times
- Review user feedback and crash reports
- Regular security scans and dependency updates

## Troubleshooting

### Common Issues

1. **Shared Package Build Failures**
   - Ensure TypeScript types are correct
   - Check for circular dependencies
   - Verify export/import statements

2. **Mobile App Build Issues**
   - Clear Expo cache: `expo r -c`
   - Check for native module compatibility
   - Verify EAS configuration

3. **Database Connection Issues**
   - Check connection strings and credentials
   - Verify network connectivity
   - Review database logs

### Debug Commands
```bash
# Check package versions
npm list --workspaces

# Verify builds
npm run build --workspaces

# Run tests
npm test --workspaces

# Check TypeScript
npm run typecheck --workspaces
```