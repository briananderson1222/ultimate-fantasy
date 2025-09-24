# Ultimate Fantasy Platform - Development Guide

This comprehensive guide covers all aspects of developing with the Ultimate Fantasy platform, from setup to deployment.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Shared Package Development](#shared-package-development)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

#### System Requirements

- **Node.js**: 20.0.0 or higher
- **Python**: 3.11 or higher
- **PostgreSQL**: 15.0 or higher
- **Redis**: 7.0 or higher
- **Docker**: 20.0 or higher
- **Git**: 2.30 or higher

#### Development Tools

- **Package Manager**: npm or yarn
- **Python Package Manager**: uv or pip
- **Code Editor**: VS Code recommended
- **Git Client**: Command line or GUI

### Quick Start

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ultimate-fantasy

# Start all services
docker-compose up --build

# Access applications
# Web App: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Mobile App: Follow mobile setup instructions
```

#### Option 2: Local Development

```bash
# Install dependencies
npm install

# Setup environment variables
cp .env.example .env.local

# Start backend
npm run dev:api

# Start web app (new terminal)
npm run dev:web

# Start mobile app (new terminal)
npm run dev:mobile
```

### Environment Configuration

#### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ultimate_fantasy

# Authentication
JWT_SECRET=your_jwt_secret_here
COGNITO_USER_POOL_ID=your_cognito_pool_id
COGNITO_CLIENT_ID=your_cognito_client_id

# External Services
SPORTS_DATA_API_KEY=your_sports_data_api_key
AI_SERVICE_API_KEY=your_ai_service_api_key

# Redis
REDIS_URL=redis://localhost:6379

# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
```

## Project Structure

### Monorepo Organization

```
ultimate-fantasy/
├── apps/                          # Applications
│   ├── api/                       # FastAPI backend
│   ├── web/                       # Next.js web app
│   ├── mobile/                    # React Native mobile app
│   └── landing/                   # Static landing page
├── packages/                      # Shared packages
│   ├── shared-logic/              # Business logic & state management
│   ├── api-client/                # HTTP client & API services
│   └── ui-components/             # Cross-platform UI components
├── specs/                         # Feature specifications
├── docs/                          # Documentation
└── scripts/                       # Utility scripts
```

### Application Structure

#### Backend (apps/api/)

```
apps/api/src/
├── api/                           # API routes & middleware
├── domains/                       # Domain-driven modules
├── infrastructure/                # Infrastructure concerns
├── models/                        # Database models
├── services/                      # Business logic services
└── main.py                        # Application entry point
```

#### Web Application (apps/web/)

```
apps/web/src/
├── app/                           # Next.js app router pages
├── components/                    # React components
├── lib/                           # Utility libraries
├── services/                      # API integration services
└── styles/                        # Global styles & themes
```

#### Mobile Application (apps/mobile/)

```
apps/mobile/src/
├── contexts/                      # React contexts
├── navigation/                    # Navigation configuration
├── screens/                       # Application screens
└── utils/                         # Platform utilities
```

## Development Workflow

### Git Workflow

#### Branch Naming Convention

```
feature/001-user-authentication
bugfix/fix-draft-timer
hotfix/critical-scoring-bug
release/v1.2.0
```

#### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**

```
feat(auth): add JWT token refresh mechanism
fix(draft): resolve timer reset issue
docs(api): update endpoint documentation
```

### Development Scripts

#### Root Level Scripts

```bash
# Development
npm run dev:web          # Start web development server
npm run dev:mobile       # Start mobile development server
npm run dev:api          # Start API development server
npm run dev:landing      # Start landing page server

# Building
npm run build:packages   # Build all shared packages
npm run build            # Build all applications
npm run build:web        # Build web application
npm run build:mobile     # Build mobile application
npm run build:api        # Build API application

# Testing
npm run test             # Run all tests
npm run test:packages    # Test shared packages
npm run test:web         # Test web application
npm run test:mobile      # Test mobile application
npm run test:api         # Test API application

# Code Quality
npm run lint             # Lint all projects
npm run typecheck        # TypeScript type checking
npm run format           # Format code with Prettier
```

#### Package-Level Scripts

```bash
# In any package directory
npm run build            # Build the package
npm run dev              # Development mode with watch
npm run test             # Run tests
npm run test:watch       # Run tests in watch mode
npm run typecheck        # TypeScript type checking
npm run lint             # Run ESLint
npm run lint:fix         # Fix ESLint issues
npm run format           # Format code
npm run clean            # Clean build artifacts
```

## Shared Package Development

### Package Overview

#### @ultimate-fantasy/shared-logic

**Purpose**: Business logic, state management, and utilities
**Size**: ~50KB
**Exports**: Hooks, stores, utilities, validation schemas

**Key Features:**

- Zustand stores for state management
- React Query integration for server state
- Form validation with Zod schemas
- Cross-platform utilities

#### @ultimate-fantasy/api-client

**Purpose**: HTTP client and API services
**Size**: ~30KB
**Exports**: HTTP client, API service classes, type definitions

**Key Features:**

- Universal HTTP client with platform-specific adapters
- Request/response interceptors
- Automatic token refresh
- Error handling and retry logic

#### @ultimate-fantasy/ui-components

**Purpose**: Cross-platform UI component library
**Size**: ~80KB
**Exports**: React components, design tokens, theme providers

**Key Features:**

- Platform-specific component rendering
- Design token system
- Theme support
- Accessibility features

### Creating New Shared Components

#### 1. Component Structure

```typescript
// packages/ui-components/src/components/NewComponent.tsx
import React from 'react';
import { useDesignTokens } from '../tokens/design-tokens';
import { platformUtils } from '../adapters/platform';

interface NewComponentProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onPress?: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onPress,
  ...props
}) => {
  const tokens = useDesignTokens();

  if (platformUtils.isNative()) {
    // React Native implementation
    const TouchableOpacity = require('react-native').TouchableOpacity;
    const Text = require('react-native').Text;

    return (
      <TouchableOpacity
        onPress={onPress}
        style={getNativeStyles(variant, size, tokens)}
        {...props}
      >
        <Text style={getNativeTextStyles(variant, size, tokens)}>
          {children}
        </Text>
      </TouchableOpacity>
    );
  }

  // Web implementation
  return (
    <button
      onClick={onPress}
      className={getWebClasses(variant, size)}
      {...props}
    >
      {children}
    </button>
  );
};
```

#### 2. Platform Adapters

```typescript
// packages/ui-components/src/adapters/platform.ts
export const platformUtils = {
  isWeb: () =>
    typeof window !== "undefined" && typeof navigator === "undefined",
  isNative: () =>
    typeof navigator !== "undefined" && navigator.product === "ReactNative",
  isMobile: () =>
    platformUtils.isNative() ||
    (platformUtils.isWeb() && window.innerWidth < 768),
  hasTouch: () => "ontouchstart" in window || navigator.maxTouchPoints > 0,
};
```

#### 3. Design Tokens

```typescript
// packages/ui-components/src/tokens/design-tokens.ts
export const designTokens = {
  colors: {
    primary: {
      50: "#eff6ff",
      500: "#3b82f6",
      900: "#1e3a8a",
    },
    semantic: {
      success: "#10b981",
      warning: "#f59e0b",
      error: "#ef4444",
    },
  },
  spacing: {
    1: "0.25rem",
    2: "0.5rem",
    4: "1rem",
    8: "2rem",
  },
  typography: {
    fontSizes: {
      sm: "0.875rem",
      base: "1rem",
      lg: "1.125rem",
    },
  },
};
```

### Testing Shared Packages

#### Unit Tests

```typescript
// packages/shared-logic/src/__tests__/utils/fantasy.test.ts
import { calculateLineupScore } from "../../utils/fantasy";

describe("calculateLineupScore", () => {
  it("should calculate score for valid lineup", () => {
    const lineup = {
      slots: [
        { position: "QB", player: { projected_points: 20 } },
        { position: "RB", player: { projected_points: 15 } },
        { position: "BENCH", player: { projected_points: 10 } },
      ],
    };

    const score = calculateLineupScore(lineup);
    expect(score).toBe(35); // Only QB and RB count
  });

  it("should handle empty lineup", () => {
    const score = calculateLineupScore(null);
    expect(score).toBe(0);
  });
});
```

#### Cross-Platform Tests

```typescript
// packages/ui-components/src/__tests__/components/Button.test.tsx
import { render, fireEvent } from '@testing-library/react';
import { Button } from '../../components/Button';

describe('Button Component', () => {
  it('should render on web', () => {
    const { getByRole } = render(
      <Button onPress={() => {}}>Click me</Button>
    );

    const button = getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('should handle press events', () => {
    const onPress = jest.fn();
    const { getByRole } = render(
      <Button onPress={onPress}>Click me</Button>
    );

    const button = getByRole('button');
    fireEvent.click(button);

    expect(onPress).toHaveBeenCalled();
  });
});
```

## Backend Development

### Domain-Driven Design

#### Domain Structure

```
apps/api/src/domains/
├── leagues/                       # League management domain
│   ├── api/                       # API endpoints
│   ├── models/                    # Domain models
│   ├── services/                  # Business logic
│   └── config.py                  # Domain configuration
├── users/                         # User management domain
├── lineups/                       # Lineup management domain
├── scoring/                       # Scoring domain
├── trading/                       # Trading domain
└── waitlist/                      # Waitlist domain
```

#### Domain Service Example

```python
# apps/api/src/domains/leagues/services/league_service.py
from typing import List, Optional
from ...models.league import League
from ...models.user import User

class LeagueService:
    def __init__(self, db_session):
        self.db_session = db_session

    async def create_league(
        self,
        name: str,
        commissioner: User,
        settings: LeagueSettings
    ) -> League:
        league = League(
            name=name,
            commissioner_id=commissioner.id,
            settings=settings
        )

        self.db_session.add(league)
        await self.db_session.commit()
        await self.db_session.refresh(league)

        return league

    async def get_user_leagues(self, user: User) -> List[League]:
        return await self.db_session.query(League).filter(
            League.members.any(user_id=user.id)
        ).all()
```

### API Development

#### FastAPI Route Structure

```python
# apps/api/src/api/routes/leagues.py
from fastapi import APIRouter, Depends, HTTPException
from ...domains.leagues.services.league_service import LeagueService
from ...models.user import User
from ...deps import get_current_user

router = APIRouter()

@router.get("/leagues")
async def get_leagues(
    current_user: User = Depends(get_current_user),
    league_service: LeagueService = Depends(get_league_service)
):
    leagues = await league_service.get_user_leagues(current_user)
    return {"data": leagues, "status": "success"}

@router.post("/leagues")
async def create_league(
    league_data: CreateLeagueRequest,
    current_user: User = Depends(get_current_user),
    league_service: LeagueService = Depends(get_league_service)
):
    league = await league_service.create_league(
        name=league_data.name,
        commissioner=current_user,
        settings=league_data.settings
    )
    return {"data": league, "status": "success"}
```

#### Pydantic Models

```python
# apps/api/src/models/league.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LeagueSettings(BaseModel):
    max_teams: int = Field(..., ge=4, le=20)
    scoring_type: str = Field(..., regex="^(standard|ppr|half_ppr)$")
    roster_size: int = Field(..., ge=10, le=30)
    playoff_teams: Optional[int] = None
    waiver_type: str = Field(..., regex="^(rolling|faab)$")

class League(BaseModel):
    id: str
    name: str
    sport: str
    league_type: str
    settings: LeagueSettings
    status: str
    commissioner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Database Development

#### SQLAlchemy Models

```python
# apps/api/src/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### Migration Management

```bash
# Create new migration
cd apps/api
alembic revision --autogenerate -m "add_user_preferences"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Frontend Development

### Next.js Web Application

#### Page Structure

```
apps/web/src/app/
├── page.tsx                       # Home page
├── leagues/
│   ├── page.tsx                   # Leagues list
│   ├── [leagueId]/
│   │   ├── page.tsx               # League dashboard
│   │   ├── settings/
│   │   │   └── page.tsx           # League settings
│   │   └── matchups/
│   │       └── page.tsx           # Matchups page
├── draft/
│   └── [leagueId]/
│       └── page.tsx               # Draft room
└── players/
    └── page.tsx                   # Player search
```

#### Component Architecture

```typescript
// apps/web/src/components/leagues/LeagueCard.tsx
import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLeagueData } from '@ultimate-fantasy/shared-logic';

interface LeagueCardProps {
  leagueId: string;
}

export const LeagueCard: React.FC<LeagueCardProps> = ({ leagueId }) => {
  const { league, isLoading, error } = useLeagueData(leagueId);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <Card className="p-6">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold">{league.name}</h3>
          <p className="text-sm text-gray-600">
            {league.sport.toUpperCase()} • {league.league_type}
          </p>
        </div>
        <Badge variant={league.status === 'active' ? 'success' : 'secondary'}>
          {league.status}
        </Badge>
      </div>
    </Card>
  );
};
```

### React Native Mobile Application

#### Screen Structure

```
apps/mobile/src/screens/
├── AuthScreen.tsx                 # Authentication
├── HomeScreen.tsx                 # Main dashboard
├── LeaguesScreen.tsx              # Leagues list
├── DraftScreen.tsx                # Draft interface
├── LineupScreen.tsx               # Lineup management
└── TradesScreen.tsx               # Trade management
```

#### Navigation Setup

```typescript
// apps/mobile/src/navigation/AppNavigator.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { HomeScreen } from '../screens/HomeScreen';
import { LeaguesScreen } from '../screens/LeaguesScreen';

const Stack = createStackNavigator();

export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'Ultimate Fantasy' }}
        />
        <Stack.Screen
          name="Leagues"
          component={LeaguesScreen}
          options={{ title: 'My Leagues' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};
```

## Testing Strategy

### Testing Pyramid

```
┌─────────────────┐
│   E2E Tests     │  ← User journeys, critical paths
├─────────────────┤
│ Integration     │  ← Component interactions, API calls
├─────────────────┤
│   Unit Tests    │  ← Individual functions, components
└─────────────────┘
```

### Unit Testing

#### Backend Unit Tests

```python
# apps/api/tests/test_league_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from domains.leagues.services.league_service import LeagueService

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def league_service(mock_db_session):
    return LeagueService(mock_db_session)

@pytest.mark.asyncio
async def test_create_league(league_service, mock_db_session):
    # Arrange
    user = MagicMock()
    user.id = "user_id"
    settings = MagicMock()

    # Act
    league = await league_service.create_league(
        name="Test League",
        commissioner=user,
        settings=settings
    )

    # Assert
    assert league.name == "Test League"
    assert league.commissioner_id == "user_id"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
```

#### Frontend Unit Tests

```typescript
// apps/web/src/__tests__/components/LeagueCard.test.tsx
import { render, screen } from '@testing-library/react';
import { LeagueCard } from '@/components/leagues/LeagueCard';

describe('LeagueCard', () => {
  it('renders league information', () => {
    render(<LeagueCard leagueId="test-league" />);

    expect(screen.getByText('Test League')).toBeInTheDocument();
    expect(screen.getByText('MLB')).toBeInTheDocument();
    expect(screen.getByText('traditional')).toBeInTheDocument();
  });

  it('shows active status badge', () => {
    render(<LeagueCard leagueId="test-league" />);

    const badge = screen.getByText('active');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge-success');
  });
});
```

### Integration Testing

#### API Integration Tests

```python
# apps/api/tests/integration/test_league_api.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_league_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/leagues",
            json={
                "name": "Test League",
                "sport": "mlb",
                "league_type": "traditional",
                "settings": {
                    "max_teams": 10,
                    "scoring_type": "points"
                }
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Test League"
```

### End-to-End Testing

#### Playwright E2E Tests

```typescript
// apps/web/e2e/league-creation.spec.ts
import { test, expect } from "@playwright/test";

test("user can create a new league", async ({ page }) => {
  await page.goto("/");

  // Navigate to league creation
  await page.click('[data-testid="create-league-button"]');
  await page.fill('[data-testid="league-name"]', "My Test League");
  await page.selectOption('[data-testid="sport-select"]', "mlb");
  await page.click('[data-testid="submit-button"]');

  // Verify league was created
  await expect(page.locator('[data-testid="league-name"]')).toHaveText(
    "My Test League",
  );
  await expect(page.locator('[data-testid="league-sport"]')).toHaveText("MLB");
});
```

## Code Quality

### TypeScript Configuration

#### Strict TypeScript Setup

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### ESLint Configuration

#### Frontend ESLint Rules

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "react/recommended",
    "react-hooks/recommended",
  ],
  rules: {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "error",
    "prefer-const": "error",
  },
};
```

#### Backend Python Linting

```python
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "I", "N", "B", "C4", "UP"]
ignore = ["E501"]  # Line too long

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports
"tests/*" = ["B011"]     # Asserts on tests
```

### Pre-commit Hooks

#### Husky Configuration

```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint
npm run typecheck
npm run test:quick
```

## Deployment

### Docker Deployment

#### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_BASE_URL=${API_BASE_URL}
    depends_on:
      - api

  mobile:
    build:
      context: ./apps/mobile
      dockerfile: Dockerfile
    environment:
      - API_BASE_URL=${API_BASE_URL}
```

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build:packages
      - run: npm run build

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

#### 1. TypeScript Errors

```bash
# Clear TypeScript cache
rm -rf node_modules/.cache
npm run typecheck

# Check specific package
cd packages/shared-logic
npm run typecheck
```

#### 2. Database Issues

```bash
# Reset database
docker-compose down
docker-compose up -d postgres
npm run db:reset

# Check database connection
docker-compose exec postgres psql -U ultimate_fantasy -d ultimate_fantasy
```

#### 3. Build Issues

```bash
# Clear all caches
npm run clean
rm -rf node_modules package-lock.json
npm install

# Rebuild packages
npm run build:packages
```

#### 4. Test Issues

```bash
# Run tests in debug mode
npm run test -- --verbose

# Run specific test file
npm test -- packages/shared-logic/src/__tests__/utils/fantasy.test.ts

# Update test snapshots
npm run test -- -u
```

### Debug Commands

#### Development Debugging

```bash
# Check package versions
npm list --workspaces

# Verify builds
npm run build --workspaces

# Check for circular dependencies
npx madge --circular packages/*/src
```

#### Performance Debugging

```bash
# Bundle analyzer
npm run analyze:web

# Performance monitoring
npm run dev:web -- --turbo

# Memory usage
node --inspect apps/web/.next/server/pages/api/leagues.js
```

### Getting Help

#### Development Support

- **Documentation**: Check the docs/ directory for detailed guides
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Team Chat**: Join the development Slack/Discord

#### Common Resources

- [API Documentation](./BACKEND_API.md)
- [Feature Documentation](./FEATURES.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)

## Conclusion

This development guide provides comprehensive information for working with the Ultimate Fantasy platform. The platform's architecture supports efficient development across multiple platforms while maintaining high code quality and testing standards.

Key development principles:

- **Cross-platform compatibility** with shared packages
- **Type safety** with strict TypeScript configuration
- **Domain-driven design** for maintainable backend architecture
- **Comprehensive testing** with unit, integration, and E2E tests
- **Modern tooling** with automated code quality checks

For additional support or questions, please refer to the project documentation or contact the development team.
