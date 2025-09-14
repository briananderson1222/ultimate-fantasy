# Claude Code Context

**Project**: Ultimate Fantasy Platform
**Last Updated**: 2025-09-15
**Version**: 1.0.0

## Project Overview

Ultimate Fantasy is a modern fantasy sports platform featuring web and mobile applications with real-time data, league management, and social features.

## Current Architecture

### Frontend Stack
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Custom component library with Storybook
- **Testing**: Jest, React Testing Library, Playwright (E2E)
- **State Management**: React Context + Custom hooks
- **Animation**: Framer Motion for complex animations

### Backend Stack
- **Framework**: FastAPI with Python 3.11
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: RESTful endpoints with OpenAPI documentation
- **Testing**: pytest with integration tests
- **Authentication**: JWT tokens with secure session management

### Project Structure
```
ultimate-fantasy/
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # Reusable components
│   │   ├── lib/          # Utilities and configurations
│   │   └── styles/       # Global styles and themes
│   ├── tests/            # Frontend test suites
│   └── .storybook/       # Component documentation
├── backend/               # FastAPI application
│   ├── src/
│   │   ├── api/          # API route handlers
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── lib/          # Backend utilities
│   └── tests/            # Backend test suites
├── landing/              # Marketing site
└── specs/                # Feature specifications and plans
```

## Current Features

### Implemented
- User authentication and registration
- League creation and management
- Team roster management
- Player database with real-time stats
- Scoring system with weekly calculations
- Waiver wire and trade systems
- League chat and communication
- Responsive web interface
- Visual regression testing

### In Development
- **Modern Design System** (Current Sprint)
  - Dark-first theming with light mode support
  - Card-based component library
  - Data visualization components
  - Enhanced drag-and-drop interactions
  - Integrated chat with transaction notifications

## Development Practices

### Testing Strategy (TDD Required)
1. **Contract Tests**: Component API validation
2. **Integration Tests**: Feature workflow testing
3. **E2E Tests**: User journey validation
4. **Visual Regression**: UI consistency checks

### Code Standards
- TypeScript strict mode enabled
- ESLint + Prettier for code formatting
- Semantic versioning for releases
- Conventional commits for change tracking

### Performance Targets
- **Frontend**: <1.5s FCP, <2.5s LCP, 60fps animations
- **Backend**: <200ms API response p95, 1000+ req/s throughput
- **Mobile**: Touch-optimized interactions, offline-capable

## Recent Changes (Last 3 Sprints)

### Sprint 002: Backend Modularization
- Refactored API endpoints into service layer architecture
- Implemented comprehensive logging middleware
- Added integration test coverage for all endpoints
- Established data validation patterns

### Sprint 003: Visual Testing Foundation
- Set up Playwright visual regression testing
- Created component snapshot baselines
- Implemented motion system for animations
- Added theme switching infrastructure

### Sprint 004: Design System (Completed)
- Comprehensive testing infrastructure added
- Component contract definitions established
- Design token system architecture implemented
- Drag-and-drop interaction patterns validated

## Key Technologies

### Design System Stack
- **@dnd-kit/core**: Accessible drag-and-drop functionality
- **Framer Motion**: Complex animations and page transitions
- **CSS Custom Properties**: Runtime theme switching
- **Storybook**: Component documentation and testing

### Data Management
- **SWR/TanStack Query**: Server state management
- **React Context**: Global application state
- **Local Storage**: User preferences and theme persistence

### Build & Deployment
- **Vercel**: Frontend hosting and deployment
- **Docker**: Backend containerization
- **GitHub Actions**: CI/CD pipeline
- **PostgreSQL**: Production database

## Development Workflow

### Feature Development
1. Create feature specification in `/specs/`
2. Generate implementation plan with task breakdown
3. Follow TDD cycle: Red → Green → Refactor
4. Update documentation and tests
5. Visual regression testing for UI changes

### Code Review Process
- All changes require PR review
- Automated testing must pass
- Visual changes require design approval
- Performance impact assessment for major changes

## Next Feature: Frontend Shared Logic Extraction (003-2-frontend-shared)
**Goal**: Extract and modularize frontend code for sharing between NextJS web app and future React Native mobile app.

### Architecture
- **Packages Structure**: 4 packages (shared-logic, ui-components, api-client, mobile-app)
- **Target Platforms**: NextJS web app + React Native mobile app
- **Shared Technologies**: TypeScript, React, React Query, Zod validation

### Package Structure
```
packages/
├── shared-logic/          # Business utilities, hooks, types, validation
├── ui-components/         # Cross-platform UI with platform adapters
├── api-client/           # HTTP services and shared API types
└── mobile-app/           # React Native app consuming shared packages
```

### Implementation Strategy
1. **Phase 1**: Extract API layer from components to services
2. **Phase 2**: Move business logic from lib/ to shared utilities
3. **Phase 3**: Extract UI components with platform styling adapters
4. **Phase 4**: Initialize React Native app with shared dependencies

## Constraints and Considerations

### Performance
- Mobile-first approach requires touch-optimized interactions
- Large datasets need virtualization and pagination
- Real-time features must handle 100+ concurrent users

### Accessibility
- Screen reader compatibility required
- Keyboard navigation for all interactive elements
- High contrast mode support
- Reduced motion preferences respected

### Security
- Input validation on all user data
- XSS prevention in chat features
- Secure session management
- Rate limiting on API endpoints

---

*This context file is automatically maintained. Manual edits between AUTO_UPDATE_START and AUTO_UPDATE_END markers will be preserved.*
