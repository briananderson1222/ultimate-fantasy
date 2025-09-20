# Tasks: Ultimate Fantasy Platform - Comprehensive Implementation

**Input**: Design documents from `/specs/005-ultimate-fantasy-platform/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, FastAPI, Next.js 15, React Native, PostgreSQL, Redis
   → Structure: Multi-app (apps/api, apps/web, apps/mobile) with shared packages/
2. Load design documents:
   → data-model.md: 12 entities → model tasks
   → contracts/: 2 files (fantasy-api.yaml, sports-data-api.yaml) → contract test tasks
   → quickstart.md: 5 scenarios → integration test tasks
3. Generate tasks by category: Setup → Tests → Core → Integration → Polish
4. Apply task rules: Different files = [P], Tests before implementation (TDD)
5. Number tasks sequentially (T001-T055)
6. Dependencies: Models before services, services before endpoints
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Paths use multi-app structure: apps/api/src/, apps/web/src/, apps/mobile/src/

## Phase 3.1: Setup and Environment

### T001 [X] Initialize ultimate fantasy platform monorepo structure
- Create apps/api/, apps/web/, apps/mobile/ directories
- Initialize packages/api-client/, packages/shared-logic/, packages/ui-components/
- Set up root-level package.json with workspace configuration

### T002 [X] [P] Configure Python backend environment in apps/api/
- Initialize Python 3.11+ project with pyproject.toml
- Install FastAPI, SQLAlchemy, Alembic, pytest dependencies
- Configure ruff, black, mypy for code quality

### T003 [X] [P] Configure Next.js frontend environment in apps/web/
- Initialize Next.js 15 project with TypeScript 5.9+
- Install React 19, TanStack Query, Tailwind CSS dependencies
- Configure ESLint, Prettier, Vitest for code quality

### T004 [X] [P] Configure React Native mobile environment in apps/mobile/
- Initialize Expo 54 project with TypeScript
- Install React Native, React Navigation, AsyncStorage dependencies
- Configure Jest, Detox for testing

### T005 [X] [P] Set up shared packages infrastructure
- Configure packages/api-client with TypeScript and HTTP client
- Configure packages/shared-logic with Zustand and business logic
- Configure packages/ui-components with cross-platform components

### T006 [X] Database and infrastructure setup
- Configure PostgreSQL connection and migrations in apps/api/alembic/
- Set up Redis connection for caching and real-time features
- Create Docker Compose for local development environment

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel)
### T007 [X] [P] Fantasy API contract tests in apps/api/tests/contract/test_fantasy_api.py
- Test draft endpoints: GET/POST /api/v1/draft/{leagueId}
- Test trade endpoints: GET/POST/PATCH /api/v1/trades
- Test league endpoints: GET/POST /api/v1/leagues
- Validate request/response schemas against fantasy-api.yaml

### T008 [X] [P] Sports Data API contract tests in apps/api/tests/contract/test_sports_data_api.py
- Test player search: GET /api/v1/sports/players
- Test player details: GET /api/v1/sports/players/{playerId}
- Test stats endpoints: GET /api/v1/sports/stats
- Validate request/response schemas against sports-data-api.yaml

### Integration Tests (Parallel)
### T009 [X] [P] League creation integration test in apps/api/tests/integration/test_league_creation.py
- Test complete league experience from quickstart scenario 1
- User registration → league creation → team joining → setup validation

### T010 [X] [P] Draft process integration test in apps/api/tests/integration/test_draft_process.py
- Test draft workflow from quickstart scenario 1
- Draft start → pick selection → snake order → completion

### T011 [X] [P] Trading system integration test in apps/api/tests/integration/test_trading_system.py
- Test trade workflow from quickstart scenario 2
- Trade proposal → evaluation → acceptance/rejection

### T012 [X] [P] Waiver system integration test in apps/api/tests/integration/test_waiver_system.py
- Test waiver workflow from quickstart scenario 2
- Bid placement → processing → player assignment

### T013 [X] [P] Real-time features integration test in apps/api/tests/integration/test_realtime_features.py
- Test WebSocket connections and real-time updates from quickstart scenario 3
- Connection establishment → message broadcasting → client updates

## Phase 3.3: Core Data Models (ONLY after tests are failing)

### Entity Models (Parallel)
### T014 [X] [P] Player model in apps/api/src/models/player.py
- Implement Player entity with fields: player_id, external_id, name, position, team_id, sport
- Add injury_status, season_stats, game_stats, projections JSON fields
- Include validation rules for position and injury status

### T015 [X] [P] League model in apps/api/src/models/league.py
- Implement League entity with configuration fields
- Add scoring_rules, roster_settings, draft_settings JSON configurations
- Include state transitions: setup → drafting → active → completed

### T016 [X] [P] Team model in apps/api/src/models/team.py
- Implement Team entity linking users to leagues
- Add wins, losses, points_for, waiver_priority tracking fields
- Include roster JSON array and budget management

### T017 [X] [P] Lineup model in apps/api/src/models/lineup.py
- Implement Lineup entity for daily/weekly player selections
- Add players JSON array with position validation
- Include optimistic locking with version field

### T018 [X] [P] Draft model in apps/api/src/models/draft.py
- Implement Draft entity for structured player selection
- Add current_pick tracking and picks JSON array
- Include timer and status management

### T019 [X] [P] Trade model in apps/api/src/models/trade.py
- Implement Trade entity for player exchanges
- Add proposed_players and requested_players JSON arrays
- Include evaluation_score and expiration logic

### T020 [X] [P] WaiverBid model in apps/api/src/models/waiver_bid.py
- Implement WaiverBid entity for free agent acquisition
- Add bid_amount, priority, and drop_player relationships
- Include processing status tracking

### T021 [X] [P] Score model in apps/api/src/models/score.py
- Implement Score entity for fantasy point calculations
- Add stats JSON and points breakdown
- Include final/projected status flag

### T022 [X] [P] Notification model in apps/api/src/models/notification.py
- Implement Notification entity for real-time alerts
- Add type, title, message, and expiration fields
- Include read status tracking

### T023 [X] [P] ChatMessage model in apps/api/src/models/chat_message.py
- Implement ChatMessage entity for league communication
- Add content, moderation status, and reply relationships
- Include edit timestamp tracking

### T024 [X] [P] Achievement model in apps/api/src/models/achievement.py
- Implement Achievement entity for gamification
- Add type, name, description, and earned date
- Include season and league context

### T025 [X] [P] User model in apps/api/src/models/user.py
- Implement User entity for authentication and profile
- Add email, password_hash, profile information
- Include authentication and authorization fields

## Phase 3.4: Service Layer

### Core Services (Sequential - dependency chain)
### T026 [X] User service in apps/api/src/services/user_service.py
- Implement UserService with CRUD operations
- Add authentication, registration, profile management
- Include JWT token generation and validation

### T027 [X] Sports data service in apps/api/src/services/sports_data_service.py
- Implement SportsDataService for external API integration
- Add ESPN API and The Athletic API clients
- Include data validation and normalization

### T028 [X] League service in apps/api/src/services/league_service.py
- Implement LeagueService with configuration management
- Add league creation, settings, and membership
- Include invite code generation and validation

### T029 [X] Player service in apps/api/src/services/player_service.py
- Implement PlayerService with stats and status management
- Add search, filtering, and projection calculations
- Include injury status updates and team affiliations

### T030 [X] Draft service in apps/api/src/services/draft_service.py
- Implement DraftService for player selection process
- Add draft management, pick validation, timer handling
- Include snake order calculation and auto-draft

### T031 [X] Trade service in apps/api/src/services/trade_service.py
- Implement TradeService for player exchanges
- Add trade evaluation, fairness analysis, processing
- Include deadline enforcement and veto handling

### T032 [X] Lineup service in apps/api/src/services/lineup_service.py
- Implement LineupService for roster management
- Add position validation, optimistic locking, constraints
- Include scoring period and lock time management

### T033 [X] Scoring service in apps/api/src/services/scoring_service.py
- Implement ScoringService for fantasy point calculations
- Add custom scoring rules, stat processing, projections
- Include real-time updates and historical tracking

## Phase 3.5: API Endpoints

### Fantasy API Endpoints (Sequential - shared route files)
### T034 Draft API endpoints in apps/api/src/api/routes/draft.py
- Implement GET/POST /api/v1/draft/{leagueId} endpoints
- Add draft pick creation: POST /api/v1/draft/{leagueId}/pick
- Include real-time WebSocket notifications

### T035 League API endpoints in apps/api/src/api/routes/leagues.py
- Implement league CRUD: GET/POST/PATCH /api/v1/leagues
- Add league joining: POST /api/v1/leagues/{leagueId}/join
- Include league settings and member management

### T036 Trade API endpoints in apps/api/src/api/routes/trades.py
- Implement trade management: GET/POST/PATCH /api/v1/trades
- Add trade evaluation and processing
- Include trade history and notifications

### T037 Lineup API endpoints in apps/api/src/api/routes/lineups.py
- Implement lineup management: GET/PUT /api/v1/lineups
- Add position validation and constraint checking
- Include optimistic locking and version control

### T038 Waiver API endpoints in apps/api/src/api/routes/waivers.py
- Implement waiver bid management: GET/POST /api/v1/waivers/bids
- Add waiver processing: POST /api/v1/admin/waivers/process
- Include priority ordering and budget validation

### Sports Data API Endpoints
### T039 Sports data API endpoints in apps/api/src/api/routes/sports.py
- Implement player search: GET /api/v1/sports/players
- Add player details: GET /api/v1/sports/players/{playerId}
- Include stats and injury status endpoints

### T040 Authentication API endpoints in apps/api/src/api/routes/auth.py
- Implement user registration: POST /api/v1/auth/register
- Add login/logout: POST /api/v1/auth/login
- Include JWT token refresh and validation

## Phase 3.6: Real-time and Integration

### Real-time Infrastructure
### T041 [X] WebSocket connection manager in apps/api/src/api/websockets/connection_manager.py
- Implement WebSocket connection management
- Add league-based rooms and message broadcasting
- Include connection state tracking and cleanup

### T042 [X] Real-time event publisher in apps/api/src/services/event_publisher.py
- Implement Redis pub/sub for cross-service communication
- Add event types: draft_pick, trade_update, score_update
- Include message serialization and delivery

### T043 [X] Sports data ingestion scheduler in apps/api/src/services/data_ingestion.py
- Implement scheduled jobs for player stats updates
- Add external API polling and data synchronization
- Include error handling and retry logic

### Database and Middleware
### T044 Database connection and session management in apps/api/src/infrastructure/database.py
- Configure SQLAlchemy engine and session factory
- Add connection pooling and transaction management
- Include migration and health check utilities

### T045 Authentication middleware in apps/api/src/api/middleware/auth.py
- Implement JWT token validation middleware
- Add role-based access control
- Include rate limiting and security headers

### T046 [X] Logging and monitoring middleware in apps/api/src/api/middleware/logging.py
- Implement structured logging with correlation IDs
- Add request/response logging and metrics
- Include error tracking and performance monitoring

## Phase 3.7: Frontend Implementation

### Web Application (Parallel - different route files)
### T047 [X] [P] League management pages in apps/web/src/app/leagues/
- Implement league creation, settings, and dashboard
- Add league joining and member management
- Include responsive design and accessibility

### T048 [X] [P] Draft interface in apps/web/src/app/draft/[leagueId]/page.tsx
- Implement real-time draft board and pick selection
- Add timer, player search, and auto-draft features
- Include WebSocket integration for live updates

### T049 [X] [P] Lineup management in apps/web/src/app/lineup/page.tsx
- Implement drag-and-drop lineup setting
- Add position constraints and validation
- Include player statistics and projections

### T050 [X] [P] Trading interface in apps/web/src/app/trades/page.tsx
- Implement trade proposal and evaluation
- Add trade history and notifications
- Include fairness analysis and deadline tracking

## Phase 3.8: Mobile Implementation

### Mobile Application (Parallel)
### T051 [X] [P] Mobile navigation and authentication in apps/mobile/src/navigation/
- Implement React Navigation stack and tab navigation
- Add authentication screens and token management
- Include biometric authentication and secure storage

### T052 [X] [P] Mobile league and draft screens in apps/mobile/src/screens/
- Implement touch-optimized league management
- Add mobile draft interface with haptic feedback
- Include offline capability and background sync

## Phase 3.9: Package Libraries

### Shared Packages (Parallel)
### T053 [X] [P] API client library in packages/api-client/src/
- Implement TypeScript HTTP client with interceptors
- Add automatic token refresh and error handling
- Include request/response type definitions

### T054 [X] [P] Shared business logic in packages/shared-logic/src/
- Implement Zustand stores for state management
- Add validation schemas and utility functions
- Include cross-platform business logic

### T055 [X] [P] UI component library in packages/ui-components/src/
- Implement cross-platform React components
- Add design tokens and theming system
- Include Storybook documentation and testing

## Dependencies

**Critical Dependencies**:
- Setup (T001-T006) before everything
- Tests (T007-T013) before implementation (T014+)
- Models (T014-T025) before services (T026-T033)
- Services before endpoints (T034-T040)
- Core features before real-time (T041-T043)
- Infrastructure (T044-T046) supports all endpoints

**Parallel Execution Groups**:
- Environment setup: T002, T003, T004, T005
- Contract tests: T007, T008
- Integration tests: T009, T010, T011, T012, T013
- Entity models: T014-T025 (all parallel)
- Frontend pages: T047, T048, T049, T050
- Mobile screens: T051, T052
- Package libraries: T053, T054, T055

## Parallel Execution Example

```bash
# Phase 3.2: Launch all contract and integration tests together
Task: "Fantasy API contract tests in apps/api/tests/contract/test_fantasy_api.py"
Task: "Sports Data API contract tests in apps/api/tests/contract/test_sports_data_api.py"
Task: "League creation integration test in apps/api/tests/integration/test_league_creation.py"
Task: "Draft process integration test in apps/api/tests/integration/test_draft_process.py"
Task: "Trading system integration test in apps/api/tests/integration/test_trading_system.py"

# Phase 3.3: Launch all entity models together
Task: "Player model in apps/api/src/models/player.py"
Task: "League model in apps/api/src/models/league.py"
Task: "Team model in apps/api/src/models/team.py"
Task: "Lineup model in apps/api/src/models/lineup.py"
Task: "Draft model in apps/api/src/models/draft.py"
```

## Validation Checklist

✅ **Contract Coverage**:
- [x] fantasy-api.yaml → T007 contract tests
- [x] sports-data-api.yaml → T008 contract tests

✅ **Entity Coverage**:
- [x] All 12 entities from data-model.md → T014-T025

✅ **Scenario Coverage**:
- [x] 5 quickstart scenarios → T009-T013 integration tests

✅ **TDD Compliance**:
- [x] All tests (T007-T013) before implementation (T014+)
- [x] Tests must fail before implementing features

✅ **Parallel Safety**:
- [x] [P] tasks target different files
- [x] No shared file conflicts in parallel groups

✅ **Path Specificity**:
- [x] All tasks specify exact file paths
- [x] Multi-app structure (apps/api, apps/web, apps/mobile)

This tasks.md provides 55 comprehensive, immediately executable tasks that follow constitutional TDD principles and support the complete Ultimate Fantasy Platform implementation across all 6 phases.

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Based on plan.md: Web + Mobile application structure (existing monorepo with apps/api, apps/web, apps/mobile, packages/shared)

## Phase 3.1: Setup & Dependencies

- [X] T001 [P] Update apps/api dependencies: Add scikit-learn, redis, websockets for AI/real-time features
- [X] T002 [P] Update apps/web dependencies: Add @dnd-kit/sortable, recharts for enhanced UI components
- [X] T003 [P] Update apps/mobile dependencies: Add react-native-sqlite-storage for offline capability
- [X] T004 [P] Configure ESLint/Prettier for fantasy sports coding standards in packages/shared-logic
- [X] T005 [P] Setup OpenTelemetry tracing configuration in apps/api/src/infrastructure/observability/
- [X] T006 [P] Initialize Redis connection pool in apps/api/src/infrastructure/cache/

## Phase 3.2: Sports Data Foundation Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

### Contract Tests - Sports Data API
- [X] T007 [P] Contract test GET /api/v1/sports/players in apps/api/tests/contract/test_sports_players_get.py
- [X] T008 [P] Contract test GET /api/v1/sports/players/{playerId} in apps/api/tests/contract/test_sports_players_detail.py
- [X] T009 [P] Contract test GET /api/v1/sports/teams in apps/api/tests/contract/test_sports_teams_get.py
- [X] T010 [P] Contract test GET /api/v1/sports/schedule in apps/api/tests/contract/test_sports_schedule_get.py
- [X] T011 [P] Contract test GET /api/v1/sports/scores in apps/api/tests/contract/test_sports_scores_get.py

### Contract Tests - Fantasy Management API
- [X] T012 [P] Contract test POST /api/v1/draft/{leagueId} in apps/api/tests/contract/test_draft_start.py
- [X] T013 [P] Contract test POST /api/v1/draft/{leagueId}/pick in apps/api/tests/contract/test_draft_pick.py
- [X] T014 [P] Contract test POST /api/v1/trades in apps/api/tests/contract/test_trades_post.py
- [X] T015 [P] Contract test PATCH /api/v1/trades/{tradeId} in apps/api/tests/contract/test_trades_patch.py
- [X] T016 [P] Contract test GET /api/v1/analytics/recommendations in apps/api/tests/contract/test_analytics_recommendations.py
- [X] T017 [P] Contract test GET /api/v1/analytics/insights in apps/api/tests/contract/test_analytics_insights.py

### Integration Tests - User Scenarios
- [X] T018 [P] Integration test complete league experience in apps/api/tests/integration/test_complete_league_flow.py
- [X] T019 [P] Integration test draft process end-to-end in apps/api/tests/integration/test_draft_flow.py
- [X] T020 [P] Integration test trading workflow in apps/api/tests/integration/test_trading_flow.py
- [X] T021 [P] Integration test waiver system in apps/api/tests/integration/test_waiver_flow.py
- [X] T022 [P] Integration test real-time features in apps/api/tests/integration/test_realtime_flow.py
- [X] T023 [P] Integration test AI recommendations in apps/api/tests/integration/test_ai_flow.py

## Phase 3.3: Core Models & Data Layer (ONLY after tests are failing)

### Database Models
- [X] T024 [P] Player model with sports data integration in apps/api/src/models/player.py
- [X] T025 [P] Enhanced League model with advanced settings in apps/api/src/models/league.py
- [X] T026 [P] Team model with roster management in apps/api/src/models/team.py
- [X] T027 [P] Lineup model with optimistic locking in apps/api/src/models/lineup.py
- [X] T028 [P] Draft model with real-time state in apps/api/src/models/draft.py
- [X] T029 [P] Trade model with evaluation scoring in apps/api/src/models/trade.py
- [X] T030 [P] WaiverBid model with priority system in apps/api/src/models/waiver_bid.py
- [X] T031 [P] Score model with breakdown tracking in apps/api/src/models/score.py
- [X] T032 [P] Notification model for real-time alerts in apps/api/src/models/notification.py
- [X] T033 [P] ChatMessage model with moderation in apps/api/src/models/chat_message.py
- [X] T034 [P] Achievement model for gamification in apps/api/src/models/achievement.py

### Enhanced Domain Services
- [ ] T035 [P] SportsDataService with multi-provider support in apps/api/src/domains/sports/services/sports_data_service.py
- [ ] T036 [P] DraftService with real-time coordination in apps/api/src/domains/drafts/services/draft_service.py
- [ ] T037 [P] Enhanced TradeService with AI evaluation in apps/api/src/domains/trading/services/enhanced_trade_service.py
- [ ] T038 [P] NotificationService with WebSocket integration in apps/api/src/domains/notifications/services/notification_service.py
- [ ] T039 [P] AnalyticsService with performance insights in apps/api/src/domains/analytics/services/analytics_service.py
- [ ] T040 [P] AIService with recommendation engine in apps/api/src/domains/ai/services/ai_service.py

## Phase 3.4: Sports Data Integration Implementation

- [ ] T041 [P] ESPN API provider implementation in apps/api/src/domains/sports/providers/espn_provider.py
- [ ] T042 [P] Sports data normalization layer in apps/api/src/domains/sports/services/data_normalizer.py
- [ ] T043 Sports data ingestion scheduler in apps/api/src/domains/sports/jobs/ingestion_scheduler.py
- [ ] T044 GET /api/v1/sports/players endpoint implementation in apps/api/src/domains/sports/api/players.py
- [ ] T045 GET /api/v1/sports/players/{playerId} endpoint in apps/api/src/domains/sports/api/players_detail.py
- [ ] T046 GET /api/v1/sports/teams endpoint in apps/api/src/domains/sports/api/teams.py
- [ ] T047 GET /api/v1/sports/schedule endpoint in apps/api/src/domains/sports/api/schedule.py
- [ ] T048 GET /api/v1/sports/scores endpoint in apps/api/src/domains/sports/api/scores.py

## Phase 3.5: Advanced Fantasy Features Implementation

- [ ] T049 Snake draft algorithm implementation in apps/api/src/domains/drafts/algorithms/snake_draft.py
- [ ] T050 Draft timer with WebSocket broadcasts in apps/api/src/domains/drafts/services/draft_timer.py
- [ ] T051 POST /api/v1/draft/{leagueId} endpoint in apps/api/src/domains/drafts/api/draft_start.py
- [ ] T052 POST /api/v1/draft/{leagueId}/pick endpoint in apps/api/src/domains/drafts/api/draft_pick.py
- [ ] T053 [P] Trade evaluation algorithm in apps/api/src/domains/trading/algorithms/trade_evaluator.py
- [ ] T054 POST /api/v1/trades endpoint in apps/api/src/domains/trading/api/trades_post.py
- [ ] T055 PATCH /api/v1/trades/{tradeId} endpoint in apps/api/src/domains/trading/api/trades_patch.py
- [ ] T056 [P] Enhanced waiver processing with FAAB in apps/api/src/domains/trading/services/waiver_processor.py

## Phase 3.6: Real-time Infrastructure

- [ ] T057 [P] WebSocket connection manager in apps/api/src/infrastructure/websockets/connection_manager.py
- [ ] T058 [P] Redis pub/sub event system in apps/api/src/infrastructure/events/redis_pubsub.py
- [ ] T059 Real-time draft updates handler in apps/api/src/domains/drafts/websockets/draft_handler.py
- [ ] T060 Real-time score updates handler in apps/api/src/domains/scoring/websockets/score_handler.py
- [ ] T061 GET /api/v1/real-time/connect WebSocket endpoint in apps/api/src/infrastructure/websockets/websocket_api.py

## Phase 3.7: AI & Analytics Implementation

- [ ] T062 [P] Player performance prediction model in apps/api/src/domains/ai/models/performance_predictor.py
- [ ] T063 [P] Lineup optimization algorithm in apps/api/src/domains/ai/algorithms/lineup_optimizer.py
- [ ] T064 [P] Waiver recommendation engine in apps/api/src/domains/ai/algorithms/waiver_recommender.py
- [ ] T065 GET /api/v1/analytics/recommendations endpoint in apps/api/src/domains/analytics/api/recommendations.py
- [ ] T066 GET /api/v1/analytics/insights endpoint in apps/api/src/domains/analytics/api/insights.py
- [ ] T067 [P] Performance metrics aggregator in apps/api/src/domains/analytics/services/metrics_aggregator.py

## Phase 3.8: Professional Theming & Web UI Enhancement

### Design System & Shared Components
- [ ] T068 [P] Fantasy sports design tokens in packages/ui-components/src/tokens/fantasy-theme.ts
- [ ] T069 [P] Enhanced PlayerCard component in packages/ui-components/src/components/PlayerCard.tsx
- [ ] T070 [P] DraftBoard component with real-time updates in packages/ui-components/src/components/DraftBoard.tsx
- [ ] T071 [P] TradeAnalyzer component with evaluation in packages/ui-components/src/components/TradeAnalyzer.tsx
- [ ] T072 [P] ScoreTicker component for live updates in packages/ui-components/src/components/ScoreTicker.tsx

### Web App Feature Implementation
- [ ] T073 [P] Enhanced league creation flow in apps/web/src/app/leagues/create/advanced/page.tsx
- [ ] T074 [P] Draft room interface in apps/web/src/app/draft/[leagueId]/room/page.tsx
- [ ] T075 [P] Trade center with AI evaluation in apps/web/src/app/leagues/[leagueId]/trades/page.tsx
- [ ] T076 [P] Analytics dashboard in apps/web/src/app/analytics/page.tsx
- [ ] T077 [P] Real-time chat interface in apps/web/src/components/chat/LeagueChat.tsx
- [ ] T078 Enhanced lineup builder with AI suggestions in apps/web/src/app/lineup/enhanced/page.tsx

## Phase 3.9: Mobile App Feature Parity

### Core Mobile Screens
- [ ] T079 [P] Enhanced mobile dashboard in apps/mobile/src/screens/EnhancedDashboardScreen.tsx
- [ ] T080 [P] Mobile draft interface in apps/mobile/src/screens/DraftScreen.tsx
- [ ] T081 [P] Mobile player search with filters in apps/mobile/src/screens/PlayerSearchScreen.tsx
- [ ] T082 [P] Touch-optimized lineup builder in apps/mobile/src/screens/LineupBuilderScreen.tsx
- [ ] T083 [P] Mobile trade interface in apps/mobile/src/screens/TradeScreen.tsx
- [ ] T084 [P] Mobile waiver management in apps/mobile/src/screens/WaiverScreen.tsx
- [ ] T085 [P] Mobile analytics view in apps/mobile/src/screens/AnalyticsScreen.tsx

### Mobile-Specific Features
- [ ] T086 [P] Offline data synchronization in apps/mobile/src/services/OfflineSync.ts
- [ ] T087 [P] Push notification handler in apps/mobile/src/services/PushNotifications.ts
- [ ] T088 [P] Touch gesture handlers in apps/mobile/src/components/GestureHandlers.tsx
- [ ] T089 [P] Mobile navigation optimization in apps/mobile/src/navigation/TabNavigator.tsx

## Phase 3.10: Integration & Middleware

- [ ] T090 Connect SportsDataService to external APIs in apps/api/src/domains/sports/integrations/
- [ ] T091 Enhanced auth middleware with rate limiting in apps/api/src/api/middleware/enhanced_auth.py
- [ ] T092 WebSocket authentication middleware in apps/api/src/infrastructure/websockets/auth_middleware.py
- [ ] T093 Request correlation ID tracking in apps/api/src/api/middleware/correlation.py
- [ ] T094 Database connection pooling optimization in apps/api/src/infrastructure/database/pool_manager.py
- [ ] T095 API response caching layer in apps/api/src/infrastructure/cache/response_cache.py

## Phase 3.11: Social Features

- [ ] T096 [P] League chat system in apps/api/src/domains/social/services/chat_service.py
- [ ] T097 [P] Content moderation service in apps/api/src/domains/social/services/moderation_service.py
- [ ] T098 [P] Achievement tracking system in apps/api/src/domains/social/services/achievement_service.py
- [ ] T099 [P] League message board in apps/web/src/app/leagues/[leagueId]/messages/page.tsx
- [ ] T100 [P] Mobile chat interface in apps/mobile/src/screens/ChatScreen.tsx

## Phase 3.12: Performance & Optimization

- [ ] T101 [P] Database query optimization and indexing in apps/api/src/infrastructure/database/optimizations/
- [ ] T102 [P] Web app code splitting configuration in apps/web/next.config.js
- [ ] T103 [P] Mobile bundle optimization in apps/mobile/metro.config.js
- [ ] T104 [P] CDN integration for static assets in apps/web/src/lib/cdn.ts
- [ ] T105 [P] API response compression in apps/api/src/api/middleware/compression.py

## Phase 3.13: Testing & Polish

### Unit Tests
- [ ] T106 [P] Unit tests for sports data validation in apps/api/tests/unit/test_sports_validation.py
- [ ] T107 [P] Unit tests for draft algorithms in apps/api/tests/unit/test_draft_algorithms.py
- [ ] T108 [P] Unit tests for trade evaluation in apps/api/tests/unit/test_trade_evaluation.py
- [ ] T109 [P] Unit tests for AI recommendations in apps/api/tests/unit/test_ai_recommendations.py
- [ ] T110 [P] Unit tests for UI components in packages/ui-components/src/components/__tests__/

### Performance & Load Testing
- [ ] T111 [P] API performance testing (300ms/600ms targets) in apps/api/tests/performance/test_api_performance.py
- [ ] T112 [P] WebSocket load testing (1000+ concurrent) in apps/api/tests/performance/test_websocket_load.py
- [ ] T113 [P] Mobile performance testing (60fps target) in apps/mobile/tests/performance/
- [ ] T114 [P] Database query performance validation in apps/api/tests/performance/test_db_performance.py

### Documentation & Validation
- [ ] T115 [P] Update API documentation with new endpoints in docs/api/
- [ ] T116 [P] Create mobile app user guide in docs/mobile/
- [ ] T117 [P] Update design system documentation in packages/ui-components/docs/
- [ ] T118 Execute quickstart validation scenarios per quickstart.md
- [ ] T119 [P] Update CLAUDE.md with new architecture patterns
- [ ] T120 Final integration testing and bug fixes

## Dependencies

### Critical Blocking Dependencies
- **Setup (T001-T006)** blocks **All other phases**
- **Contract Tests (T007-T017)** MUST FAIL before **Implementation (T024+)**
- **Integration Tests (T018-T023)** MUST FAIL before **Implementation (T024+)**
- **Models (T024-T034)** block **Services (T035-T040)**
- **Services (T035-T040)** block **API Endpoints (T044+)**
- **Sports Data (T041-T048)** blocks **Fantasy Features (T049+)**
- **Real-time Infrastructure (T057-T061)** blocks **Draft Implementation (T049-T052)**
- **AI Services (T062-T067)** blocks **Analytics Endpoints (T065-T066)**

### Parallel Execution Groups
```
# Group 1: Setup (can run simultaneously)
T001, T002, T003, T004, T005, T006

# Group 2: Contract Tests (after setup, before implementation)
T007, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017

# Group 3: Integration Tests (after setup, before implementation)
T018, T019, T020, T021, T022, T023

# Group 4: Core Models (after tests fail)
T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034

# Group 5: Domain Services (after models)
T035, T036, T037, T038, T039, T040

# Group 6: Sports Data Features (after services)
T041, T042, T053, T056, T062, T063, T064, T067

# Group 7: UI Components (independent of backend)
T068, T069, T070, T071, T072, T073, T074, T075, T076, T077

# Group 8: Mobile Screens (independent of each other)
T079, T080, T081, T082, T083, T084, T085, T086, T087, T088, T089

# Group 9: Polish & Testing (after implementation)
T106, T107, T108, T109, T110, T111, T112, T113, T114, T115, T116, T117, T119
```

## Parallel Example
```
# Launch Group 2 contract tests together:
Task: "Contract test GET /api/v1/sports/players in apps/api/tests/contract/test_sports_players_get.py"
Task: "Contract test GET /api/v1/sports/teams in apps/api/tests/contract/test_sports_teams_get.py"
Task: "Contract test POST /api/v1/draft/{leagueId} in apps/api/tests/contract/test_draft_start.py"
Task: "Contract test POST /api/v1/trades in apps/api/tests/contract/test_trades_post.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Follow TDD: Red → Green → Refactor
- Mobile and Web can be developed in parallel after API is stable
- Real-time features require WebSocket infrastructure completion first

## Task Generation Rules Applied

### From Sports Data API Contract (sports-data-api.yaml):
- 5 endpoints → 5 contract tests (T007-T011)
- Player search, detail, teams, schedule, scores → Implementation tasks (T044-T048)

### From Fantasy Management API Contract (fantasy-api.yaml):
- 6 major endpoints → 6 contract tests (T012-T017)
- Draft, trades, analytics → Implementation tasks (T049-T066)

### From Data Model (data-model.md):
- 12 core entities → 12 model tasks (T024-T034)
- 6 domain services → 6 service tasks (T035-T040)

### From User Stories (quickstart.md):
- 6 major scenarios → 6 integration tests (T018-T023)
- Complete league experience, draft, trading, waivers, real-time, AI

### From Research Decisions (research.md):
- Multi-provider sports data → ESPN provider (T041)
- WebSocket + Redis → Real-time infrastructure (T057-T061)
- Design tokens → Professional theming (T068-T072)
- Cross-platform consistency → Mobile feature parity (T079-T089)

## Validation Checklist ✅

- [x] All contracts have corresponding tests (T007-T017)
- [x] All entities have model tasks (T024-T034)
- [x] All tests come before implementation (Phase 3.2 before 3.3+)
- [x] Parallel tasks truly independent (different files, marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD workflow enforced (tests must fail first)
- [x] Constitutional compliance (library-first, observability, versioning)
- [x] Performance targets addressed (300ms/600ms API, 60fps mobile)
- [x] All 35 functional requirements from spec covered across tasks

**Total Tasks**: 120 comprehensive tasks covering complete Ultimate Fantasy Platform transformation from foundation to professional-grade fantasy sports platform with real-time features, AI analytics, mobile parity, and advanced fantasy functionality.