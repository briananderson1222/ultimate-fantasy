# Domain Consolidation Task List

## Goal & Scope
- Replace legacy `apps/api/src/models` and `apps/api/src/services` with the domain-oriented packages under `apps/api/src/domains`.
- Ensure each domain (users, leagues, drafts, lineups, scoring, trading, sports) has a single model/service implementation that encapsulates all current functionality.
- Align FastAPI routes, infra helpers, and tests with the consolidated domain services while preserving behaviour and test coverage.

## Workstream A — Foundations & Architecture
- [ ] Confirm canonical architecture decision: `domains/<domain>` holds models, services, schemas, events, and APIs.
- [ ] Inventory legacy vs. domain classes; document destination module for each duplicated model/service.
- [ ] Update architecture notes (docs/readme) to reflect modular domain layout once implemented.

## Workstream B — Database & Dependency Layer
- [X] Promote `infrastructure/database/session_factory` as the sole sync/async session provider.
- [X] Refactor FastAPI dependencies (`api/deps.py`, route modules) to use the session factory; remove `services/db.py` usage.
- [X] Provide DI helpers that construct domain services per-request with injected Session, redis, event dispatcher, etc.

## Workstream C — Model Consolidation (per Domain)
1. Users
   - [X] Merge authentication/profile fields & helpers from `models/user.py` into `domains/users/models/user.py`.
   - [X] Preserve JSON preference/settings defaults and validation constraints.
2. Leagues & Teams
   - [X] Extend `domains/leagues/models` with configuration JSON, status enums, invite codes, and roster/budget stats from legacy models.
   - [X] Ensure relationships/constraints (unique team per league/user) are ported.
3. Drafts
   - [X] Create `domains/drafts/models` reflecting legacy draft schema (statuses, picks, timers).
4. Lineups
   - [X] Enrich `domains/lineups/models/lineup.py` with weekly/game_day fields, locking/versioning, indexes.
5. Scoring
   - [X] Port `models/score.py` and related enums into `domains/scoring/models`.
6. Trading/Waivers
   - [X] Add trade model alongside existing waiver/transaction domain models with full workflow fields.
7. Sports/Shared
   - [X] Move shared models (notification, achievement, presets) into `domains/shared/models` as needed; delete legacy duplicates.

## Workstream D — Service Consolidation (per Domain)
1. Users
   - [X] Fold registration, authentication, JWT helpers from `services/user_service.py` into `domains/users/services/user_service.py` while keeping event publishing.
2. Leagues
   - [X] Merge configuration, invite code logic, commissioner checks, auto team creation, achievements, and errors into domain service.
3. Drafts
   - [X] Combine real-time coordination (redis, websocket callbacks) with validation/autopick/draft board features from legacy service.
4. Lineups
   - [X] Integrate validation, locking, optimistic concurrency, roster manipulation from legacy service into domain implementation.
   - [ ] Update integration fixtures/tests to provision domain teams so lineup endpoints can enforce ownership.
   - [ ] Reinstate lineup route/service ownership validation once tests expect real team data.
5. Scoring
   - [X] Unify stat ingestion, scoring rules, projections, and aggregate APIs into `domains/scoring/services`.
6. Trading/Waivers
   - [X] Merge trade proposal/evaluation/deadline logic with existing waiver processing and event publishing.
7. Sports Data
   - [X] Adopt domain `SportsDataService` as canonical; import provider configs & fallbacks from legacy version.
   - [X] Replace sports API route singletons with DI wiring and update tests/fixtures accordingly.
8. Shared Utilities
   - [ ] Centralize logging, events, cache helpers, and enums referenced across services.

## Workstream E — API Layer Integration
- [ ] Replace global service singletons in `api/routes/**` with FastAPI dependencies that construct domain services.
- [ ] Update route schemas to reference domain models (Pydantic `from_attributes=True` adjustments).
- [ ] Ensure websocket/background flows (draft timers, scoring updates) use consolidated services.

## Workstream F — Testing & Validation
- [ ] Update pytest fixtures to source sessions and services from the new dependency layer.
- [ ] Adjust unit/integration tests to import domain models/services; add coverage for migrated behaviours (lineup locking, trade vetoes, scoring rules, etc.).
- [ ] Run full test suite after each major domain migration; capture regressions.

## Workstream G — Data Migration & Schema Updates
- [ ] Draft Alembic migrations aligning DB schema with consolidated domain models (new columns, indexes, constraints).
- [ ] Provide data backfill scripts or guidance for existing deployments (e.g., migrating password hashes, roster data).
- [ ] Document rollback strategy for each migration.

## Workstream H — Cleanup & Verification
- [ ] Remove legacy `apps/api/src/models` and `apps/api/src/services` packages once all references are updated.
- [ ] Update documentation/README to describe the new domain service architecture and dependency setup.
- [ ] Final verification: lint, type checks, full test run, and optional local smoke test (auth → league creation → draft → scoring → trading).
