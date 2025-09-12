# Tasks: Ultimate Fantasy Platform

**Input**: Design documents from `/mnt/e/dev/ultimate-fantasy/ultimate-fantasy/specs/001-ultimate-fantasy-platform/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Setup project scaffolding and tooling
2. Write failing contract and integration tests
3. Implement models, then services, then endpoints
4. Wire integrations (DB, middleware, logging)
5. Polish with unit tests, performance, and docs
```

## Tasks

- [x] T001 Create backend project structure per plan in `backend/` (folders: `backend/src/models/`, `backend/src/services/`, `backend/src/api/`, `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`). Include `backend/pyproject.toml` with pinned deps and `backend/README.md` with run instructions.
  - Python 3.11 runtime. Dependencies (exact pins): `fastapi==0.116.1`, `sqlalchemy==2.0.43`, `alembic==1.16.5`, `uvicorn[standard]==0.35.0`, `pydantic==2.11.7`, `psycopg[binary]==3.2.10`, `httpx==0.28.1`.
  - Test/dev tools: `pytest==8.4.2`, `pytest-asyncio==1.2.0`, `pytest-benchmark==5.1.0`, `ruff==0.13.0`, `black==25.1.0`, `isort==6.0.1`, `mypy==1.18.1`.
- [x] T002 Create frontend project structure per plan in `frontend/` using Next.js (App Router) with TypeScript and Tailwind (folders: `frontend/src/app/`, `frontend/src/components/`, `frontend/src/services/`, `frontend/tests/`). Include `frontend/package.json` with pinned deps, Tailwind config, and basic app bootstrap.
  - Node 20.x. Dependencies: `next@15.5.3`, `react@19.1.1`, `react-dom@19.1.1`, `@tanstack/react-query@5.87.4`, `tailwindcss@4.1.13`.
  - Dev dependencies: `typescript@5.9.2`, `eslint@9.35.0`, `eslint-config-next@15.5.3`, `prettier@3.6.2`, `postcss@8.5.6`, `autoprefixer@10.4.21`.
- [x] T003 [P] Configure linting/formatting: backend (ruff, black, isort, mypy via `backend/pyproject.toml` and `backend/mypy.ini`) and frontend (eslint, prettier via `frontend/package.json`). Add CI workflow at `/.github/workflows/ci.yml` using `actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5` to run both test suites.

## Tests First (TDD) — MUST FAIL FIRST

- [x] T004 [P] Contract test from `openapi.yml`: create `backend/tests/contract/test_contract_openapi.py` that loads `/mnt/e/dev/ultimate-fantasy/ultimate-fantasy/specs/001-ultimate-fantasy-platform/contracts/openapi.yml` and asserts the following endpoints exist with methods: POST `/leagues`, PATCH `/leagues/{leagueId}/settings`, POST `/leagues/{leagueId}/join`, PUT `/lineups`, GET `/leagues/{leagueId}/scoreboard`, POST `/waivers/bids`, GET `/leagues/{leagueId}/public`. Ensure tests fail until implemented.
- [x] T005 [P] Integration test: Create and join league flow in `backend/tests/integration/test_create_and_join_league.py` per quickstart Scenario 1, using live FastAPI TestClient and a temporary PostgreSQL URL (can use sqlite fallback for local but mark xfail if not postgres).
- [x] T006 [P] Integration test: Set a lineup in `backend/tests/integration/test_set_lineup.py` per quickstart Scenario 2.
- [x] T007 [P] Integration test: Scoreboard update in `backend/tests/integration/test_scoreboard.py` per quickstart Scenario 3. Seed or simulate stats via `ScoringService` or a test fixture, then assert GET `/leagues/{leagueId}/scoreboard` returns updated scores.
- [x] T008 [P] Integration test: Waiver claim bidding and resolution in `backend/tests/integration/test_waiver_claim.py` per quickstart Scenario 4.

## Core Implementation

- [x] T009 [P] Create `League` model in `backend/src/models/league.py` with fields from data-model.md and SQLAlchemy mappings.
- [x] T010 [P] Create `User` model in `backend/src/models/user.py` with fields from data-model.md and SQLAlchemy mappings.
- [x] T011 [P] Create `Team` model in `backend/src/models/team.py` with FKs to `League` and `User`.
- [x] T012 [P] Create `Player` model in `backend/src/models/player.py`.
- [x] T013 [P] Create `Roster` model in `backend/src/models/roster.py` linking `Team` and `Player` with acquisition fields.
- [x] T014 [P] Create `Lineup` model in `backend/src/models/lineup.py` with JSONB players and version.
- [x] T015 [P] Create `Schedule` model in `backend/src/models/schedule.py`.
- [x] T016 [P] Create `Score` model in `backend/src/models/score.py` with JSONB stats.
- [x] T017 [P] Create `Waiver` model in `backend/src/models/waiver.py`.
- [x] T018 [P] Create `Transaction` model in `backend/src/models/transaction.py`.
- [x] T019 [P] Create `Notification` model in `backend/src/models/notification.py`.
- [x] T020 [P] Create `Rule` model in `backend/src/models/rule.py`.
- [x] T021 [P] Create `Preset` model in `backend/src/models/preset.py`.
- [x] T022 Implement `DatabaseSession` and SQLAlchemy engine setup in `backend/src/services/db.py` using `DATABASE_URL` (PostgreSQL) and Alembic base in `backend/src/models/base.py`.
- [x] T023 Implement `LeagueService` in `backend/src/services/league_service.py` with create/join operations and rule preset application.
- [x] T024 Implement `LineupService` in `backend/src/services/lineup_service.py` with validation against rules and save.
- [x] T025 Implement `ScoringService` in `backend/src/services/scoring_service.py` to apply ingested stats to generate `Score` rows.
- [x] T026 Implement `WaiverService` in `backend/src/services/waiver_service.py` for bid lifecycle and resolution.

## Endpoints (from contracts/openapi.yml)

- [x] T027 Define FastAPI app and routers under `backend/src/api/` and wire dependency injection and DB sessions in `backend/src/api/deps.py` and `backend/src/main.py`. Include and mount routers for files below.
- [x] T028 [P] Implement POST `/leagues` in `backend/src/api/leagues_create.py` using `LeagueService.create` and return created league with commissioner and invite link.
- [x] T029 [P] Implement POST `/leagues/{leagueId}/join` in `backend/src/api/leagues_join.py` using `LeagueService.join` and return membership result.
- [x] T030 [P] Implement PUT `/lineups` in `backend/src/api/lineups.py` using `LineupService` to validate and save.
- [x] T031 [P] Implement GET `/leagues/{leagueId}/scoreboard` in `backend/src/api/scoreboard.py` using `ScoringService` to read computed scores.
- [x] T032 [P] Implement POST `/waivers/bids` in `backend/src/api/waivers.py` using `WaiverService` to place bids.
- [x] T033 [P] Implement PATCH `/leagues/{leagueId}/settings` in `backend/src/api/leagues_settings.py` to update rules.
- [x] T034 [P] Implement GET `/leagues/{leagueId}/public` in `backend/src/api/leagues_public.py` to return public league data.

## Integration

- [x] T035 Configure DB connection and migrations: add Alembic files in `backend/alembic/` and initial migration from models (files: `backend/alembic/env.py`, `backend/alembic/versions/<timestamp>_init.py`).
- [x] T036 Add auth middleware (placeholder) in `backend/src/api/middleware/auth.py` and wire to app; shape matches quickstart assumptions (authenticated user context).
- [x] T037 Add structured logging with request and correlation IDs in `backend/src/api/middleware/logging.py` and configure uvicorn loggers.
- [x] T038 Configure CORS and security headers in `backend/src/api/security.py` and app startup.

## Frontend (skeleton aligned with backend contracts)

- [x] T039 [P] Create basic pages with App Router and TanStack Query:
  - `frontend/src/app/leagues/page.tsx` (list leagues)
  - `frontend/src/app/leagues/create/page.tsx` (create league → POST `/leagues`)
  - `frontend/src/app/leagues/[leagueId]/page.tsx` (public league view → GET `/leagues/{leagueId}/public` and join UI → POST `/leagues/{leagueId}/join`)
  - `frontend/src/app/lineup/page.tsx` (set lineup → PUT `/lineups`)
- [x] T040 [P] Implement `frontend/src/services/api.ts` with typed wrappers for: POST `/leagues`, POST `/leagues/{leagueId}/join`, PATCH `/leagues/{leagueId}/settings`, PUT `/lineups`, GET `/leagues/{leagueId}/scoreboard`, POST `/waivers/bids`, GET `/leagues/{leagueId}/public`. Include basic error handling and TanStack Query helpers.

## Polish

- [x] T041 [P] Unit tests for services in `backend/tests/unit/test_league_service.py`, `backend/tests/unit/test_lineup_service.py`, `backend/tests/unit/test_waiver_service.py`.
- [x] T042 Performance tests for API p95 targets using `pytest-benchmark` in `backend/tests/perf/test_api_perf.py`.
- [x] T043 [P] Update docs: generate `backend/README.md` runbook and `specs/001-ultimate-fantasy-platform/docs/api.md` from `openapi.yml`.
- [x] T044 Remove duplication and ensure type hints; run linters/formatters; ensure CI green.

## Dependencies

- Setup (T001–T003) before tests and implementation.
- Tests (T004–T008) must be written and fail before Core (T009–T026) and Endpoints (T027–T034).
- Models (T009–T021) before Services (T023–T026) and Migrations (T035).
- Services before Endpoints that depend on them.
- Integration (T035–T038) after Core and Endpoints wiring.
- Frontend (T039–T040) after contracts exist; can proceed in parallel once API shapes are stable.
- Polish (T041–T044) after prior phases.

## Parallel Execution Examples

```
# Example: run all [P] tests in parallel
task run "T004" & task run "T005" & task run "T006" & task run "T007" & task run "T008" && wait

# Example: parallelize independent model files
task run "T009" & task run "T010" & task run "T011" & task run "T012" & task run "T013" & task run "T014" & task run "T015" & task run "T016" & task run "T017" & task run "T018" & task run "T019" & task run "T020" & task run "T021" && wait

# Example: frontend setup and linting can run with backend linting
task run "T003" & task run "T039" & task run "T040" && wait
```

## Notes

- Contract-driven: `/mnt/e/dev/ultimate-fantasy/ultimate-fantasy/specs/001-ultimate-fantasy-platform/contracts/openapi.yml` is the single source for endpoints and schemas.
- Use PostgreSQL in development; allow SQLite fallback in tests where possible to keep tests runnable locally, clearly marking xfail where behavior differs.
- Ensure each task commits independently and keeps changes scoped to the mentioned files.

---

# Next Tasks: Scoreboard Aggregation, Auth Upgrade, E2E

These tasks extend the platform beyond the initial MVP to provide real scoreboard aggregation, production-ready auth via JWTs, and end‑to‑end UI coverage. Follow the same TDD approach: write failing tests first, then implement.

## New Tests First (TDD) — MUST FAIL FIRST

- [ ] T045 [P] Unit test: Scoring aggregation — create `backend/tests/unit/test_scoring_service_aggregate.py` to seed teams, lineups, and player scores, then assert `ScoringService.compute_league_scoreboard(league_id, game_day=None)` returns per‑team totals (e.g., sum of `stats.points`) sorted descending.
- [ ] T046 [P] Integration test: Scoreboard endpoint aggregation — create `backend/tests/integration/test_scoreboard_aggregate.py` to create a league, set lineups, ingest scores, then `GET /leagues/{leagueId}/scoreboard` returns structured items with totals and team identifiers.
- [ ] T047 [P] Integration test: JWT auth — create `backend/tests/integration/test_auth_jwt.py` that issues a valid HS256 dev token (via `AUTH_MODE=dev` and `AUTH_DEV_SECRET`) and asserts protected endpoints reject requests without Authorization and accept with a valid token.

## Scoreboard Aggregation

- [ ] T048 Implement aggregation in `backend/src/services/scoring_service.py`: add `compute_league_scoreboard(league_id: UUID, game_day: date | None)` that
  - Joins `Lineup` and `Score` by `player_id` and `game_day` (all days if `game_day is None`).
  - Sums `stats.points` per team, returns a list of items `{ team_id, total_points, lineup_count }` sorted by `total_points` desc.
  - Handles missing/empty stats as 0; SQLite compatibility maintained.
- [ ] T049 Update API response in `backend/src/api/scoreboard.py` to call `ScoringService.compute_league_scoreboard` and return `ScoreboardResponse` with `items: [{ team_id, total_points }]` (may include `team_name` later when joining `Team`).
- [ ] T050 Performance: add DB indexes for aggregation — create Alembic migration `backend/alembic/versions/<timestamp>_scoreboard_indexes.py` adding indexes on `scores (player_id, game_day)` and `lineups (team_id, game_day)`.
- [ ] T051 [P] Docs: update `specs/001-ultimate-fantasy-platform/docs/api.md` to document the scoreboard item shape and example payloads.

## Auth Upgrade (JWT)

- [ ] T052 [P] Backend deps: add `PyJWT[crypto]==2.9.0` to `backend/pyproject.toml` and run `uv sync`. Document env in `backend/README.md`.
- [ ] T053 Implement JWT verification in `backend/src/api/middleware/auth.py`:
  - Support `Authorization: Bearer <token>`.
  - Modes via env: `AUTH_MODE=dev|jwks`.
    - `dev`: HS256 using `AUTH_DEV_SECRET`.
    - `jwks`: RS256 using `AUTH_JWKS_URL` (fetch with `httpx`), validate `aud` and `iss` via `AUTH_AUDIENCE`, `AUTH_ISSUER`.
  - Populate `request.state.user_id` (from `sub`) and `request.state.user_claims`.
- [ ] T054 [P] Add `get_current_user_id()` in `backend/src/api/deps.py` that raises 401 when absent/invalid. Update write endpoints to depend on it. Keep compatibility to accept `x-user-id` only when `AUTH_MODE=dev`.
- [ ] T055 Persist/update users: add `backend/src/services/user_service.py` with `ensure_user_from_claims(claims)` to upsert `User` on first seen `sub`/`email`. Wire it in the auth middleware for requests that have valid tokens.
- [ ] T056 [P] Tests for auth:
  - Unit: `backend/tests/unit/test_auth_middleware.py` (token decode branches, bad sig, wrong aud/iss).
  - Integration: extend existing endpoint tests to use `Authorization` header under `AUTH_MODE=dev`. Remove reliance on `x-user-id` except where explicitly xfail‑marked for backwards compatibility.
- [ ] T057 Frontend auth header: update `frontend/src/services/api.ts` to inject `Authorization: Bearer <token>` from `localStorage` (e.g., `uf_token`), fallback to none in dev. Update docs with a helper to set a dev token.

## E2E Tests (Playwright)

- [ ] T058 [P] Add Playwright to frontend: dev dependency `@playwright/test@1.48.2`. Create `frontend/playwright.config.ts` with baseURL from `process.env.E2E_BASE_URL` (default `http://localhost:3000`). Add npm scripts: `test:e2e`, `e2e:headed`.
- [ ] T059 [P] Author tests under `frontend/tests/e2e/`:
  - `leagues.spec.ts`: create league flow → asserts success banner and API 201.
  - `join.spec.ts`: join league from invite link → asserts membership.
  - `lineup.spec.ts`: set lineup → asserts 200 and UI echo.
  - `scoreboard.spec.ts`: view scoreboard → asserts aggregated items rendered.
  - `waivers.spec.ts`: place waiver bid → asserts 201.
  Each test sets a dev HS256 token into `localStorage` before navigation.
- [ ] T060 CI: extend `/.github/workflows/ci.yml` with job `frontend-e2e` that uses Node 20, installs deps, runs `npx playwright install --with-deps`, starts backend (uvicorn) and frontend (Next.js) concurrently, waits on healthchecks, then runs `npm run test:e2e`. Use env: `AUTH_MODE=dev`, `AUTH_DEV_SECRET`, `NEXT_PUBLIC_API_URL`.
- [ ] T061 [P] E2E compose: optional `docker-compose.e2e.yml` to run postgres, backend, frontend with seeded env for e2e. Add `scripts/e2e.sh` to orchestrate start/wait/test/teardown locally.
- [ ] T062 Docs: update `README.md` with JWT auth instructions, how to mint a dev HS256 token, and how to run E2E locally and in CI.

## Dependencies (New)

- Scoreboard aggregation (T048–T051) depends on tests (T045–T046).
- Auth upgrade (T053–T057) depends on deps (T052) and tests (T047, T056).
- E2E tests (T058–T062) depend on backend auth in dev mode and scoreboard aggregation being available for assertions.

## Parallel Execution Examples (New)

```
# New tests first (in parallel)
task run "T045" & task run "T046" & task run "T047" && wait

# Implement aggregation and auth side-by-side
task run "T048" & task run "T049" & task run "T050" & task run "T051" & task run "T052" && wait

# Frontend E2E setup and CI wiring
task run "T058" & task run "T060" & task run "T061" && wait
```
