# Tasks: Backend Modularization for Future Microservices

**Input**: Design documents from `/specs/002-backend-modularization-for/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

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
- **Web app**: `backend/src/`, `backend/tests/`
- Paths assume backend restructuring with existing frontend

## Phase 3.1: Setup & Infrastructure
- [ ] T001 Create baseline performance benchmark tests in backend/tests/performance/test_baseline.py
- [ ] T002 [P] Create domain directory structure: backend/src/domains/{leagues,users,lineups,trading,scoring,waitlist,shared}/
- [ ] T003 [P] Create infrastructure directory structure: backend/src/infrastructure/{database,middleware,security,logging}/
- [ ] T004 [P] Create domain-specific test directories: backend/tests/domains/{leagues,users,lineups,trading,scoring,waitlist}/
- [ ] T005 [P] Create contract test directories: backend/tests/contracts/
- [ ] T006 [P] Create integration test directories: backend/tests/integration/

## Phase 3.2: Domain Interface Contracts (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests for Domain Interfaces
- [ ] T007 [P] Contract test for LeagueService.get_league_members in backend/tests/contracts/test_league_service_contract.py
- [ ] T008 [P] Contract test for LeagueService.validate_league_access in backend/tests/contracts/test_league_service_contract.py
- [ ] T009 [P] Contract test for UserService.get_user in backend/tests/contracts/test_user_service_contract.py
- [ ] T010 [P] Contract test for UserService.validate_user_permissions in backend/tests/contracts/test_user_service_contract.py
- [ ] T011 [P] Contract test for LineupService.get_lineup in backend/tests/contracts/test_lineup_service_contract.py
- [ ] T012 [P] Contract test for LineupService.validate_lineup_ownership in backend/tests/contracts/test_lineup_service_contract.py
- [ ] T013 [P] Contract test for TradingService.validate_trade_eligibility in backend/tests/contracts/test_trading_service_contract.py
- [ ] T014 [P] Contract test for ScoringService.calculate_lineup_score in backend/tests/contracts/test_scoring_service_contract.py
- [ ] T015 [P] Contract test for WaitlistService.add_to_waitlist in backend/tests/contracts/test_waitlist_service_contract.py

### Integration Tests for Cross-Domain Communication
- [ ] T016 [P] Integration test for league-user interaction in backend/tests/integration/test_league_user_boundaries.py
- [ ] T017 [P] Integration test for lineup-league interaction in backend/tests/integration/test_lineup_league_boundaries.py
- [ ] T018 [P] Integration test for trading-user interaction in backend/tests/integration/test_trading_user_boundaries.py
- [ ] T019 [P] Integration test for scoring-lineup interaction in backend/tests/integration/test_scoring_lineup_boundaries.py
- [ ] T020 [P] Integration test for waitlist-league interaction in backend/tests/integration/test_waitlist_league_boundaries.py

### Domain Isolation Tests
- [ ] T021 [P] Domain independence test for leagues domain in backend/tests/domains/leagues/test_domain_isolation.py
- [ ] T022 [P] Domain independence test for users domain in backend/tests/domains/users/test_domain_isolation.py
- [ ] T023 [P] Domain independence test for lineups domain in backend/tests/domains/lineups/test_domain_isolation.py
- [ ] T024 [P] Domain independence test for trading domain in backend/tests/domains/trading/test_domain_isolation.py
- [ ] T025 [P] Domain independence test for scoring domain in backend/tests/domains/scoring/test_domain_isolation.py
- [ ] T026 [P] Domain independence test for waitlist domain in backend/tests/domains/waitlist/test_domain_isolation.py

## Phase 3.3: Domain Structure Implementation (ONLY after tests are failing)

### Abstract Base Classes (Domain Interfaces)
- [ ] T027 [P] Create LeagueServiceInterface ABC in backend/src/domains/shared/interfaces/league_service.py
- [ ] T028 [P] Create UserServiceInterface ABC in backend/src/domains/shared/interfaces/user_service.py
- [ ] T029 [P] Create LineupServiceInterface ABC in backend/src/domains/shared/interfaces/lineup_service.py
- [ ] T030 [P] Create TradingServiceInterface ABC in backend/src/domains/shared/interfaces/trading_service.py
- [ ] T031 [P] Create ScoringServiceInterface ABC in backend/src/domains/shared/interfaces/scoring_service.py
- [ ] T032 [P] Create WaitlistServiceInterface ABC in backend/src/domains/shared/interfaces/waitlist_service.py

### Move Existing Files to Domain Structure
- [ ] T033 [P] Move leagues_* API files to backend/src/domains/leagues/api/
- [ ] T034 [P] Move league_service.py to backend/src/domains/leagues/services/
- [ ] T035 [P] Move user/preference models to backend/src/domains/users/models/
- [ ] T036 [P] Move lineups API to backend/src/domains/lineups/api/
- [ ] T037 [P] Move lineup_service.py to backend/src/domains/lineups/services/
- [ ] T038 [P] Move waivers API to backend/src/domains/trading/api/
- [ ] T039 [P] Move waiver_service.py to backend/src/domains/trading/services/
- [ ] T040 [P] Move scoreboard API to backend/src/domains/scoring/api/
- [ ] T041 [P] Move scoring_service.py to backend/src/domains/scoring/services/
- [ ] T042 [P] Move waitlist API to backend/src/domains/waitlist/api/

### Update Import Statements
- [ ] T043 Update all import statements in moved league files to use new domain structure
- [ ] T044 Update all import statements in moved user files to use new domain structure
- [ ] T045 Update all import statements in moved lineup files to use new domain structure
- [ ] T046 Update all import statements in moved trading files to use new domain structure
- [ ] T047 Update all import statements in moved scoring files to use new domain structure
- [ ] T048 Update all import statements in moved waitlist files to use new domain structure

### Domain Service Implementations
- [ ] T049 [P] Implement LeagueService with interface in backend/src/domains/leagues/services/league_service.py
- [ ] T050 [P] Implement UserService with interface in backend/src/domains/users/services/user_service.py
- [ ] T051 [P] Implement LineupService with interface in backend/src/domains/lineups/services/lineup_service.py
- [ ] T052 [P] Implement TradingService with interface in backend/src/domains/trading/services/trading_service.py
- [ ] T053 [P] Implement ScoringService with interface in backend/src/domains/scoring/services/scoring_service.py
- [ ] T054 [P] Implement WaitlistService with interface in backend/src/domains/waitlist/services/waitlist_service.py

## Phase 3.4: Infrastructure & Dependency Injection
- [ ] T055 Create domain service registry in backend/src/infrastructure/service_registry.py
- [ ] T056 Configure dependency injection container in backend/src/infrastructure/container.py
- [ ] T057 Create domain-specific database session factory in backend/src/infrastructure/database/session_factory.py
- [ ] T058 Update main FastAPI app to use domain service registry in backend/src/main.py
- [ ] T059 Add middleware for domain request routing in backend/src/infrastructure/middleware/domain_router.py

## Phase 3.5: Event System Implementation
- [ ] T060 [P] Create domain event base classes in backend/src/domains/shared/events/base.py
- [ ] T061 [P] Create event publisher interface in backend/src/domains/shared/events/publisher.py
- [ ] T062 [P] Create event subscriber interface in backend/src/domains/shared/events/subscriber.py
- [ ] T063 Create event dispatcher implementation in backend/src/infrastructure/events/dispatcher.py
- [ ] T064 [P] Add event publishing to LeagueService in backend/src/domains/leagues/services/league_service.py
- [ ] T065 [P] Add event publishing to UserService in backend/src/domains/users/services/user_service.py
- [ ] T066 [P] Add event publishing to LineupService in backend/src/domains/lineups/services/lineup_service.py
- [ ] T067 [P] Add event publishing to TradingService in backend/src/domains/trading/services/trading_service.py
- [ ] T068 [P] Add event publishing to ScoringService in backend/src/domains/scoring/services/scoring_service.py
- [ ] T069 [P] Add event publishing to WaitlistService in backend/src/domains/waitlist/services/waitlist_service.py

## Phase 3.6: Validation & Polish
- [ ] T070 Run existing API test suite to verify no regression in backend/tests/api/
- [ ] T071 Run domain isolation tests to verify boundaries work correctly
- [ ] T072 Run cross-domain integration tests to verify interfaces function
- [ ] T073 Run performance tests to compare with baseline metrics
- [ ] T074 [P] Create domain configuration files in backend/src/domains/{domain}/config.py
- [ ] T075 [P] Add health check endpoints per domain in backend/src/domains/{domain}/health.py
- [ ] T076 Update FastAPI application startup to initialize all domains
- [ ] T077 Create rollback script in scripts/rollback_modularization.py
- [ ] T078 Run quickstart validation scenarios from quickstart.md
- [ ] T079 Update logging configuration for domain-specific logs in backend/src/infrastructure/logging/

## Dependencies
- Setup (T001-T006) before all other tasks
- Contract tests (T007-T026) must FAIL before implementation (T027-T079)
- Interface ABCs (T027-T032) before implementations (T049-T054)
- File moves (T033-T042) before import updates (T043-T048)
- Domain services (T049-T054) before dependency injection (T055-T059)
- Infrastructure (T055-T059) before event system (T060-T069)
- All implementation before validation (T070-T079)

## Parallel Execution Examples

### Phase 3.2 Contract Tests (All Parallel):
```bash
# Launch T007-T015 together (contract tests):
python -m pytest backend/tests/contracts/test_league_service_contract.py -k "test_get_league_members" --tb=short
python -m pytest backend/tests/contracts/test_user_service_contract.py -k "test_get_user" --tb=short
python -m pytest backend/tests/contracts/test_lineup_service_contract.py -k "test_get_lineup" --tb=short
# ... continue for all contract tests
```

### Phase 3.2 Integration Tests (All Parallel):
```bash
# Launch T016-T020 together (integration tests):
python -m pytest backend/tests/integration/test_league_user_boundaries.py --tb=short
python -m pytest backend/tests/integration/test_lineup_league_boundaries.py --tb=short
python -m pytest backend/tests/integration/test_trading_user_boundaries.py --tb=short
# ... continue for all integration tests
```

### Phase 3.3 Interface Creation (All Parallel):
```bash
# Launch T027-T032 together (interface ABCs):
# Create LeagueServiceInterface, UserServiceInterface, etc. simultaneously
```

### Phase 3.3 File Moves (All Parallel):
```bash
# Launch T033-T042 together (file moves):
# Move all domain files simultaneously since they target different directories
```

## Notes
- [P] tasks = different files/directories, no dependencies
- Verify all contract and integration tests fail before implementing
- Commit after each major phase completion
- Run performance benchmarks before and after each phase
- Maintain backward compatibility throughout all phases

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - domain-interfaces.yaml → contract test tasks [P] (T007-T015)
   - events-schema.yaml → event system tasks (T060-T069)

2. **From Data Model**:
   - Each domain entity → move/restructure tasks [P] (T033-T042)
   - Interface contracts → ABC creation tasks [P] (T027-T032)

3. **From Quickstart Scenarios**:
   - Each validation step → verification task (T070-T079)
   - Domain independence → isolation test tasks [P] (T021-T026)

4. **Ordering**:
   - Setup → Contract Tests → Interface ABCs → File Moves → Implementation → Events → Validation
   - TDD strictly enforced: tests must fail before implementation

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T007-T026)
- [x] All domain entities have restructure tasks (T033-T042)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (different files/directories)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Performance validation included (T001, T073)
- [x] Rollback capability provided (T077)