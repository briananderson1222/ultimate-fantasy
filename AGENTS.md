# Ultimate Fantasy Platform - Agent Development Guide

This document provides essential information for AI agents working on the Ultimate Fantasy platform, covering development patterns, tools, and best practices.

## Table of Contents

- [Development Patterns](#development-patterns)
- [Tools & Technologies](#tools--technologies)
- [Project Structure](#project-structure)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Git Workflow](#git-workflow)
- [Task Management](#task-management)
- [Cross-Platform Development](#cross-platform-development)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)

## Development Patterns

### Spec-Driven Development (Spec Kit)

The project uses a comprehensive specification system located in the `.specify/` directory:

- **Specification Templates**: Located in `.specify/templates/` for consistent spec creation
- **Task Prerequisites**: Use `.specify/scripts/check-task-prerequisites.sh --json` to resolve feature directories and available documentation
- **Feature Structure**: Each feature has a dedicated directory under `specs/001-*/` with:
  - `spec.md` - Feature specification
  - `plan.md` - Implementation plan
  - `tasks.md` - Detailed task breakdown
  - `contracts/` - API contracts and schemas
  - `docs/` - Feature-specific documentation

### Test-Driven Development (TDD)

**Strict TDD Flow**: All development follows this pattern:

1. **Setup** - Project scaffolding and tooling
2. **Tests (RED)** - Write failing contract and integration tests first
3. **Implementation (GREEN)** - Make smallest change to pass tests
4. **Refactor** - Run formatters, linters, and broaden tests

**Task Numbering**: All tasks are numbered (T001, T002, etc.) and must be completed in order:

- Contract tests must fail before implementation
- Integration tests must fail before services
- Unit tests must fail before components

### Feature-Driven Development

**Numbered Features**: Features are organized as `specs/001-*/`, `specs/002-*/`, etc.:

- Each feature has a dedicated branch and task tracking
- Features build upon each other incrementally
- Clear dependencies and parallelization guidance

**Task Dependencies**: Tasks include dependency information:

```markdown
## Dependencies

- Setup (T001–T003) before tests and implementation
- Tests (T004–T008) must fail before Core (T009–T026)
- Models (T009–T021) before Services (T023–T026)
```

## Tools & Technologies

### Python Package Management

**uv Package Manager**: The project uses `uv` for Python dependency management:

- **Lock File**: `apps/api/uv.lock` contains exact dependency versions
- **Installation**: `cd apps/api && uv sync` for dependency installation
- **Virtual Environment**: `uv` manages virtual environments automatically
- **Performance**: Significantly faster than pip for dependency resolution

**Python Tooling**:

- **ruff**: Fast Python linter and formatter
- **black**: Code formatter
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework with async support

### JavaScript/TypeScript Tooling

**Package Management**: npm workspaces for monorepo management

- **Root Scripts**: Use `npm run <script>` from project root
- **Workspace Scripts**: Each package has consistent script names
- **Build System**: Rollup for shared packages

**Frontend Tools**:

- **Next.js**: React framework with App Router
- **React Native**: Mobile application framework
- **TypeScript**: Strict type checking across all packages
- **Tailwind CSS**: Utility-first CSS framework
- **ESLint**: Code linting with custom rules
- **Prettier**: Code formatting

### Development Tools

**Code Quality**:

- **Husky**: Pre-commit hooks for automated checks
- **Commitlint**: Conventional commit validation
- **Lint-staged**: Run linters on staged files

**Testing Tools**:

- **Jest**: Unit testing for JavaScript/TypeScript
- **Vitest**: Fast unit testing with native ESM support
- **Playwright**: End-to-end testing
- **React Testing Library**: Component testing utilities

## Project Structure

### Monorepo Organization

```
ultimate-fantasy/
├── apps/                          # Applications
│   ├── api/                       # FastAPI backend (Python)
│   ├── web/                       # Next.js web app (TypeScript)
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

### Backend Structure (Domain-Driven Design)

```
apps/api/src/
├── domains/                       # Domain-driven modules
│   ├── leagues/                   # League management domain
│   ├── users/                     # User management domain
│   ├── lineups/                   # Lineup management domain
│   ├── scoring/                   # Scoring domain
│   ├── trading/                   # Trading domain
│   └── waitlist/                  # Waitlist domain
├── api/                           # API routes & middleware
├── models/                        # Database models
├── services/                      # Business logic services
└── infrastructure/                # Infrastructure concerns
```

### Shared Package Architecture

```
packages/
├── shared-logic/                  # Business logic & state management
│   ├── store/                     # Zustand stores
│   ├── hooks/                     # React hooks
│   ├── utils/                     # Utility functions
│   ├── validation/                # Zod schemas
│   └── models/                    # Data models
├── api-client/                    # HTTP client & API services
│   ├── client/                    # HTTP client implementation
│   ├── services/                  # API service classes
│   └── models/                    # API models
└── ui-components/                 # Cross-platform UI components
    ├── primitives/                # Base components
    ├── adapters/                  # Platform adapters
    ├── tokens/                    # Design tokens
    └── themes/                    # Theme definitions
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

### Test Categories

**Contract Tests**: Validate API specifications

- Location: `**/tests/contract/`
- Purpose: Ensure API contracts are met
- Must fail before implementation begins

**Integration Tests**: Test component interactions

- Location: `**/tests/integration/`
- Purpose: Test business logic flows
- Use real dependencies (database, services)

**Unit Tests**: Test individual functions

- Location: `**/tests/unit/`
- Purpose: Test isolated functionality
- Fast execution, no external dependencies

**E2E Tests**: Test user journeys

- Location: `**/tests/e2e/`
- Purpose: Full user workflow testing
- Use Playwright for browser automation

### Test Execution Commands

**Backend Testing**:

```bash
cd apps/api
uv run pytest -q                    # Run all tests
uv run pytest tests/unit/           # Run unit tests only
uv run pytest tests/integration/    # Run integration tests
uv run pytest tests/contract/       # Run contract tests
```

**Frontend Testing**:

```bash
npm run test                        # Run all tests
npm run test:unit                   # Run unit tests
npm run test:e2e                    # Run E2E tests
npm run test:watch                  # Run tests in watch mode
```

## Code Quality

### Python Code Quality

```bash
cd apps/api
uv run ruff check .                 # Lint code
uv run black .                      # Format code
uv run isort .                      # Sort imports
uv run mypy .                       # Type checking
```

### JavaScript/TypeScript Code Quality

```bash
npm run lint                        # Lint all projects
npm run typecheck                   # TypeScript checking
npm run format                      # Format code
npm run format:check                # Check formatting
```

### Pre-commit Hooks

The project uses Husky for automated code quality checks:

- Linting and formatting
- Type checking
- Test execution
- Conventional commit validation

## Git Workflow

### Branch Naming Convention

```
feature/001-user-authentication
bugfix/fix-draft-timer
hotfix/critical-scoring-bug
release/v1.2.0
```

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples**:

```
feat(api): add JWT token refresh mechanism
fix(draft): resolve timer reset issue
docs(api): update endpoint documentation
test(contract): add OpenAPI coverage (T004)
```

### Task References

Always include task IDs in commit messages:

```
test(contract): add OpenAPI coverage (T004)
feat(api): implement JWT auth middleware (T053)
```

## Task Management

### Task Execution Loop

1. **Read Task**: Get next unchecked task from `tasks.md`
2. **Write Tests**: For test tasks, write failing tests first (RED)
3. **Implement**: For implementation tasks, make minimal changes to pass tests (GREEN)
4. **Quality Checks**: Run formatters and linters
5. **Test Execution**: Run relevant tests (narrow to broad)
6. **Update Tasks**: Check off task and add clarifying notes
7. **Commit**: Use conventional message with task ID

### Parallel Execution

Only run `[P]` tasks concurrently when they:

- Touch different files
- Have no dependency edges
- Are marked as parallel-safe in task descriptions

**Example**:

```bash
# Safe parallel execution
task run "T004" & task run "T005" & task run "T006" && wait
```

### Task Dependencies

Tasks include clear dependency information:

```markdown
## Dependencies

- Contract tests (T004–T008) before implementation
- Models (T009–T021) before Services (T023–T026)
- Services before Endpoints that depend on them
```

## Cross-Platform Development

### Platform Detection

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

### Storage Abstraction

```typescript
// Platform-specific storage adapters
interface StorageAdapter {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}
```

### Component Adaptation

```typescript
// Cross-platform component rendering
export const Button = ({ children, onPress, ...props }) => {
  if (platformUtils.isNative()) {
    return <TouchableOpacity onPress={onPress} {...props}>{children}</TouchableOpacity>;
  }
  return <button onClick={onPress} {...props}>{children}</button>;
};
```

## Backend Development

### Domain-Driven Design

Each domain is self-contained with:

- `api/` - API endpoints
- `models/` - Domain models
- `services/` - Business logic
- `config.py` - Domain configuration
- `health.py` - Health checks

### FastAPI Patterns

```python
# Dependency injection
from fastapi import Depends
from ...deps import get_current_user

@router.get("/leagues")
async def get_leagues(
    current_user: User = Depends(get_current_user),
    league_service: LeagueService = Depends(get_league_service)
):
    leagues = await league_service.get_user_leagues(current_user)
    return {"data": leagues, "status": "success"}
```

### Database Patterns

```python
# SQLAlchemy models
from sqlalchemy import Column, String, DateTime, func
from ...models.base import Base

class League(Base):
    __tablename__ = "leagues"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sport = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Frontend Development

### Next.js App Router

```
apps/web/src/app/
├── page.tsx                       # Home page
├── leagues/
│   ├── page.tsx                   # Leagues list
│   ├── [leagueId]/
│   │   ├── page.tsx               # League dashboard
│   │   └── settings/
│       └── page.tsx               # League settings
└── api/
    └── [...slug]/route.ts         # API routes
```

### React Native Structure

```
apps/mobile/src/
├── screens/                       # Application screens
├── navigation/                    # Navigation configuration
├── contexts/                      # React contexts
└── utils/                         # Platform utilities
```

### Shared Package Usage

```typescript
// Web application
import { useLeagueData } from "@ultimate-fantasy/shared-logic";
import { LeaguesService } from "@ultimate-fantasy/api-client";
import { Card, Button } from "@ultimate-fantasy/ui-components";

// Mobile application (same imports)
import { useLeagueData } from "@ultimate-fantasy/shared-logic";
import { LeaguesService } from "@ultimate-fantasy/api-client";
import { Card, Button } from "@ultimate-fantasy/ui-components";
```

## Conclusion

This guide provides the essential information needed to work effectively with the Ultimate Fantasy platform. Key principles:

- **Spec-Driven Development**: All work starts with specifications and contracts
- **Test-Driven Development**: Tests must fail before implementation begins
- **Cross-Platform First**: All shared code works on web and mobile
- **Domain-Driven Design**: Clean architecture with bounded contexts
- **Quality First**: Automated linting, formatting, and testing
- **Conventional Practices**: Standard commit messages and branch naming

For additional information, refer to:

- Feature specifications in `specs/001-*/`
- API documentation in `docs/BACKEND_API.md`
- Development guide in `docs/DEVELOPMENT_GUIDE.md`
- Architecture documentation in `docs/ARCHITECTURE.md`
