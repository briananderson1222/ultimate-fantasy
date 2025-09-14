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

# Next Tasks: Frontend Real UI

Build a production-ready frontend UX: app shell, navigation, validated forms, polished pages for leagues, lineup, scoreboard, and waivers with proper loading/error states and tests.

## New Tests First (TDD) — MUST FAIL FIRST

- [x] T063 [P] UI tests scaffold: add unit test setup with Vitest + React Testing Library. Create `frontend/tests/unit/` with failing tests for Button, Input, and Layout rendering. Update CI to run unit tests.
- [x] T064 [P] E2E flows expansion: add Playwright specs for create → join → set lineup → view scoreboard end-to-end with assertions on UI states (skeletons, toasts). Place under `frontend/tests/e2e/*.spec.ts` (extend existing files), initially failing due to missing UI polish.

## Design System & App Shell

- [x] T065 [P] Add UI tooling deps (pinned): `zod@3.23.8`, `react-hook-form@7.53.0`, `@radix-ui/react-toast@1.1.5`, `@radix-ui/react-dialog@1.1.5`, `class-variance-authority@0.7.0`, `tailwind-merge@2.5.4`, `lucide-react@0.475.0`. Dev deps: `vitest@2.0.6`, `@testing-library/react@16.0.1`, `@testing-library/jest-dom@6.6.3`, `jsdom@25.0.1`.
- [x] T066 [P] App providers and shell: add `frontend/src/app/layout.tsx` with React Query provider, Toast provider, and global styles. Add top nav, footer, route-level loading/error boundaries (app router conventions).
- [x] T067 [P] Design tokens and primitives: create `frontend/src/components/ui/` with Button, Input, Select, Card, Modal, Toast, Skeleton, EmptyState. Add stories or playground page to preview components.
- [x] T068 Accessibility and focus styles: ensure components have labels/roles, focus-visible outlines, keyboard support. Add `eslint-plugin-jsx-a11y@6.9.0` and fix lint violations.

## Pages & Flows

- [x] T069 Create League (polish): refactor to use `react-hook-form + zod` schema, inline validation, success toast, and redirect to league page. File: `frontend/src/app/leagues/create/page.tsx`.
- [x] T070 League Public: enrich page with tabs (Overview, Scoreboard, Managers). Use GET `/leagues/{leagueId}/public` and `/leagues/{leagueId}/scoreboard` with `refetchInterval` for live updates. File: `frontend/src/app/leagues/[leagueId]/page.tsx`.
- [x] T071 My Leagues page: new route `frontend/src/app/leagues/page.tsx` lists a user's leagues. Requires contract support (see Backend Contracts). For now, render placeholder when API missing.
- [x] T072 Join flow: move join CTA into a Dialog with confirmation and success toast; refetch league data on success.
- [x] T073 Lineup Builder: enhance `frontend/src/app/lineup/page.tsx` with position badges, client-side validation, saved state indicator, and optimistic update. Add "copy yesterday" helper. Requires GET endpoint in the future (see Backend Contracts).
- [x] T074 Waivers UI: add page `frontend/src/app/waivers/page.tsx` to place bids and list recent bids. Initially, POST only; list view pending new API.
- [x] T075 Loading & error UX: add skeletons for each page, empty states, and error fallbacks (retry buttons). Ensure consistent toast patterns on success/failure.

## Backend Contracts (to unblock richer UI)

- [x] T076 [P] Extend OpenAPI: add GET `/me/leagues` (list leagues for current user), GET `/leagues/{leagueId}/members`, GET `/waivers?league_id=...`, and optionally GET `/lineups?team_id=...&game_day=...`. Update `specs/001-ultimate-fantasy-platform/contracts/openapi.yml` and docs.
- [x] T077 Implement endpoints and wire services: add routes + simple queries to support the above reads. Add basic pagination and sorting parameters.
- [x] T078 [P] Frontend API client: extend `frontend/src/services/api.ts` with typed functions for new endpoints and integrate into pages.

## Frontend Unit Tests & Coverage

- [x] T079 [P] Configure Vitest: add `frontend/vitest.config.ts`, JSDOM env, and scripts `test:unit`, `test:unit:watch`. Update CI to run unit tests.
- [x] T080 Component tests: write tests for Button/Input (disabled, loading), Form (validation errors), Toast (auto-dismiss), Layout (nav links), and pages (render + basic behavior).

## Docs & Polish

- [x] T081 [P] Usage docs: add `frontend/README.md` with UI architecture, component library guidance, form patterns, and example token setup.
- [x] T082 Lint rules & formatting: add `eslint-plugin-jsx-a11y` config, ensure Prettier/ESLint integrations are clean across new files.
- [x] T083 Perf & a11y pass: run Lighthouse locally; fix contrast, label, and tap target warnings. Ensure images/icons have accessible names.

## Dependencies (New UI)

- UI/Forms (T065) before page refactors (T069–T075).
- Contract updates (T076–T077) before building list/detail views that depend on them (T070–T074, T078).
- Unit test setup (T079) before component tests (T080).

## Parallel Execution Examples (New UI)

```
# Spin up UI foundations while writing tests
task run "T063" & task run "T065" & task run "T066" & task run "T067" && wait

# Build league pages in parallel once components exist
task run "T069" & task run "T070" & task run "T072" && wait

# Contracts + client + page wiring
task run "T076" & task run "T077" & task run "T078" && wait

# Unit test setup and component tests
task run "T079" & task run "T080" && wait
```

# Next Tasks: Backend Read APIs for UI

Provide the read endpoints needed for a fully functional UI: list a user's leagues, league members, waivers, and lineups. Follow tests-first.

- [x] T084 [P] Contract test (extended): add `backend/tests/contract/test_contract_openapi_extended.py` asserting new paths exist with methods and basic response shapes:
  - GET `/me/leagues`
  - GET `/leagues/{leagueId}/members`
  - GET `/waivers` (query: `league_id`, optional `team_id`, `limit`, `offset`)
  - GET `/lineups` (query: `team_id`, optional `game_day`, `limit`, `offset`)
- [x] T085 [P] Integration tests for new reads:
  - `test_me_leagues_lists_memberships`: create league + join as second user; GET `/me/leagues` returns memberships for the calling user (uses Authorization).
  - `test_league_members_lists_commissioner_and_joined_users`: after create+join, GET `/leagues/{leagueId}/members` returns both teams with user/team info.
  - `test_waivers_list_filters_by_league_and_team`: place multiple bids then GET `/waivers?league_id=...&team_id=...` returns only matching rows.
  - `test_lineups_list_by_team_and_day`: create two lineups; GET `/lineups?team_id=...&game_day=...` returns expected subset.

## OpenAPI & Schemas

- [x] T086 Extend `specs/001-ultimate-fantasy-platform/contracts/openapi.yml` with the new endpoints and minimal response schemas:
  - GET `/me/leagues` → `{ items: [{ league_id, name, season, team_id }] }`
  - GET `/leagues/{leagueId}/members` → `{ items: [{ team_id, user_id, team_name }] }`
  - GET `/waivers` → `{ items: [{ waiver_id, league_id, team_id, player_id, bid, status }] }`
  - GET `/lineups` → `{ items: [{ lineup_id, team_id, game_day, players, version }] }`

## Implementation

- [x] T087 [P] Services: add listing methods
  - `LeagueService.list_by_user(user_id)` → memberships across leagues (join Team/League)
  - `LeagueService.list_members(league_id)` or new `TeamService` → teams in a league
  - `WaiverService.list(league_id, team_id=None, limit=50, offset=0)`
  - `LineupService.list(team_id, game_day=None, limit=50, offset=0)`
- [x] T088 [P] Endpoints: implement and wire routers
  - `backend/src/api/leagues_me.py` → GET `/me/leagues`
  - `backend/src/api/leagues_members.py` → GET `/leagues/{leagueId}/members`
  - `backend/src/api/waivers.py` → add GET `/waivers`
  - `backend/src/api/lineups.py` → add GET `/lineups`
  - Include routers in `backend/src/main.py`
- [x] T089 [P] Pagination & validation: common query params `limit` (1–100), `offset` (>=0); validate with Pydantic and apply to queries. Default order by `created_at` desc where applicable.

## Frontend Wiring

- [x] T090 [P] API client: add wrappers in `frontend/src/services/api.ts` for GET `/me/leagues`, `/leagues/{leagueId}/members`, `/waivers`, `/lineups` with typings and React Query helpers.

## Fantasy Football Themed UI (Roadmap)

Deliver a professional, brandable Fantasy Football experience with rich theming, polished visuals, and production UX.

- [x] T200 Brand identity & art direction: define name, logo directions, mascot/illustration style, tone. Outcome: brief + moodboard (docs). See docs at `specs/001-ultimate-fantasy-platform/docs/brand-identity.md` and asset placeholders under `frontend/public/brand/`.
- [x] T201 Color system: primary/secondary, semantic (success/warning/error), surfaces, overlays, accents; light/dark tokens with contrast AA/AAA. Outcome: tokens + examples. Implemented in `frontend/src/styles/theme.css` with updated variables and examples; docs updated in `frontend/docs/theming.md`.
- [x] T202 Typography: heading scale, body, monospace, optional display font; load via CSS `@font-face` with fallbacks. Outcome: tokens + CSS. Implemented tokens in `frontend/src/styles/theme.css`, base styles and `@font-face` in `frontend/src/styles/typography.css`, and added font placeholders under `frontend/public/fonts/`.
- [x] T203 Iconography: adopt `lucide-react` (or similar) + custom football icons (ball, field, goal posts, helmet). Outcome: icon map + usage rules. Implemented custom icons in `frontend/src/components/icons/` with an `ICONS` map and usage docs in `frontend/docs/iconography.md`. lucide-react remains the primary UI icon set.
- [x] T204 Theme Pack (Fantasy Football): default theme with turf greens, honey gold accents, dark graphite backgrounds; gradients and subtle textures (noise overlay). Outcome: JSON theme + CSS variables. Added preset at `frontend/public/themes/fantasy-football.json`, gradient/texture tokens and sample classes in `frontend/src/styles/theme.css`, and a “Load Fantasy Pack” action in `/settings/theme`.
- [x] T205 Component styling sweep: buttons, inputs, tabs, modals, cards, tables — unify radii, shadows, focus rings, density (comfortable/compact). Outcome: updated primitives + docs. Updated UI primitives to use CSS tokens and unified focus rings/radii; implemented density via `[data-density]`. Files: `frontend/src/components/ui/{button.tsx,input.tsx,card.tsx,modal.tsx,tabs.tsx,data-table.tsx}`, `frontend/src/styles/theme.css`, `frontend/src/lib/preferences.ts`, and docs in `frontend/docs/customization.md`.
- [x] T206 Navigation & layout: header with logo, league switcher, quick actions; footer with links; responsive breakpoints and page containers. Outcome: layout components. Implemented `LeagueSwitcher` with `/me/leagues` data, integrated into `app/layout.tsx` header, added logo fallback, responsive containers, and footer links.
- [x] T207 Landing/Home page: hero section, feature highlights, CTA to create/join league; themed illustrations. Outcome: `/` redesign. Implemented hero with gradient/texture, create/join CTAs, and feature highlights in `frontend/src/app/page.tsx` using theme tokens and accessible markup.
- [x] T208 League detail visual polish: scoreboard tiles with team avatars, win/loss badges, trend arrows; members grid with avatars; tabs and sticky subnav. Outcome: updated `/leagues/[leagueId]`. Implemented scoreboard tiles with avatar gradients, leader badge, and trend arrows; members rendered as an avatar grid; tabs are now in a sticky subnav. See `frontend/src/app/leagues/[leagueId]/page.tsx`.
- [x] T209 Draft Room UI (MVP): live picks, queue, filters, timers, chat panel; keyboard shortcuts. Outcome: `/draft/[leagueId]` scaffold. Implemented scaffold at `frontend/src/app/draft/[leagueId]/page.tsx` with player search/filters, queue management, live picks, countdown timer, chat, and keyboard shortcuts (`/`, q, Enter, c, t). State persists per‑league in localStorage.
- [x] T210 Team & Matchups: team page with roster cards, upcoming matchup card, projections; weekly matchups view with responsive grid. Outcome: pages + components.
- [x] T211 Waivers & Trades polish: activity feed styling, bid cards with status badges; trade builder UX with validation and review. Outcome: updated pages.
- [x] T212 Player search & stats: searchable list with sticky filters, stat columns, favoriting; mobile-friendly. Outcome: new page + components.
- [x] T213 Motion & microinteractions: subtle transitions, toasts, loading states, skeletons, and empty states themed; reduced-motion support. Outcome: animation tokens + classes.
- [x] T214 Visual tests: add basic visual regression (Playwright screenshots) for themed pages; guard against style regressions in CI.
- [ ] T215 Theming docs & storybook: add `frontend/docs/theming.md` and component stories/playground; document override recipes and Theme Studio workflows.

Notes
- Builds on T098–T101 for tokens, provider, and Theme Studio.
- Add `class-variance-authority`, `tailwind-merge`, and `lucide-react` (see T065) before T205.
- Consider `frontend/public/brand/` for assets (logos, textures) and a `BrandKit.zip` export script.
- [x] T091 Integrate UI pages:
  - My Leagues page lists items from `/me/leagues` (replace placeholder).
  - League Public shows Members tab (GET `/leagues/{leagueId}/members`).
  - Waivers page lists recent bids (GET `/waivers?league_id=...`).
  - Lineup page optionally fetches existing lineup(s) for the selected team/day.

## Docs & Perf

- [x] T092 [P] Update docs: `specs/001-ultimate-fantasy-platform/docs/api.md` with new endpoints and examples; README examples for listing endpoints.
- [x] T093 [P] Perf tests: add p95 checks for GET `/me/leagues` and GET `/leagues/{leagueId}/members` to `backend/tests/perf/test_api_perf.py`.
- [x] T094 Indexes: optional Alembic migration adding indexes (`teams (user_id)`, `teams (league_id)`, `waivers (league_id, team_id)`, `lineups (team_id, game_day)`) if missing.

## Dependencies (Read APIs)

- Contract (T086) before endpoints/services (T087–T088) and client wiring (T090–T091).
- Tests (T084–T085) must fail before implementing T087–T091.
- Docs and perf (T092–T093) after implementation.

## Parallel Execution Examples (Read APIs)

```
# Write failing tests and contract
task run "T084" & task run "T085" & task run "T086" && wait

# Implement services and endpoints
task run "T087" & task run "T088" & task run "T089" && wait

# Wire frontend and docs
task run "T090" & task run "T091" & task run "T092" && wait
```

# Next Tasks: Frontend Ease-of-Use & Ultra-Customizability

Deliver a polished, highly customizable UI with theming, layout personalization, data views, and onboarding. Favor progressive enhancement: sensible defaults + deep controls. Tests first where applicable.

## New Tests First (TDD) — MUST FAIL FIRST

- [x] T095 [P] E2E theming tests: add Playwright spec `frontend/tests/e2e/theme.spec.ts` that switches light/dark/custom themes and asserts CSS variables and persistence across reload.
- [x] T096 [P] E2E layout tests: add `frontend/tests/e2e/dashboard_layout.spec.ts` that drags widgets, saves layout, reloads, and verifies persistence and responsive behavior.
- [x] T097 [P] Unit tests for preferences store: add Vitest tests for a new `usePreferences` hook (themes, density, locale) with localStorage and server sync (xfail until API added).

## Theming & Branding

- [x] T098 [P] Tokenized theme system: define CSS variables for color, spacing, radius, shadow, typography under `frontend/src/styles/theme.css`. Wire Tailwind to CSS variables.
- [x] T099 [P] Theme manager: add `ThemeProvider` with support for light/dark/system and custom theme objects (JSON). Persist per-user in localStorage.
- [x] T100 Theme Studio UI: add `/settings/theme` page to edit tokens live with previews; export/import theme JSON.
- [x] T101 League branding: allow per-league theme override (load from `/leagues/{leagueId}/public` branding fields when available); fallback to user/global theme.

## Layout & Widgets

- [x] T102 Dashboard widgets: create `frontend/src/app/(dashboard)/page.tsx` with modular widgets (My Leagues, Upcoming, Scoreboard, Waivers, Tips).
- [x] T103 [P] Drag-and-drop and grid: implement customizable layout (drag to reorder, resize) with lightweight grid + CSS; store layout in localStorage.
- [x] T104 Saved layouts: add save/reset buttons; persist per-user (and per-league scope) with server sync (blocked by Preferences API; see T112–T114).
- [x] T105 Widget config: per-widget settings (e.g., default league, filters). Provide a modal for configuration.

## Data Views & Filters

 - [x] T106 Table components: build reusable `DataTable` with column show/hide, sorting, pagination, and saved views. Use accessible markup.
 - [x] T107 Filters UI: add filter chips + advanced drawer; persist recent filters per-view.
 - [x] T108 Save & share views: allow naming a view and sharing via URL (query params) and server-side saved views when API exists.

## Forms & Rule Customization

 - [x] T109 Rule editor UI: dynamic form for league rules using zod schemas; supports custom fields, JSON editor (monaco or textarea) with validation.
 - [x] T110 Presets: import/export presets as JSON; apply preview before save; show diff vs active rules.

## Accessibility, i18n, and Help

 - [x] T111 [P] Global a11y pass: keyboard navigation, focus management, aria-labels, skip links, color contrast, reduced motion.
- [x] T112 i18n plumbing: set up i18n (e.g., `next-intl`) with locale switcher and message catalogs; default en-US; lazy-load locales.
- [x] T113 [P] Command palette: add cmd-k menu for quick actions (create league, join, set lineup) with keyboard shortcuts.
- [x] T114 Onboarding tours: add guided tours using `react-joyride` for create/join/lineup flows; dismissible and remember state.

## Preferences & Server Sync

- [x] T115 Preferences store: implement `usePreferences` hook (theme, density, layout, locale) with localStorage + optimistic server sync.
- [x] T116 Server preferences API (backend): add GET/PUT `/me/preferences` and `/leagues/{leagueId}/branding` to persist user/league settings (see tasks below).
- [x] T117 Frontend wiring: sync preferences at app start; debounce writes; handle merge conflicts and provide reset.

## Docs & Developer Experience

- [x] T118 [P] Storybook or Ladle: add a component playground with stories for all primitives; CI to build and preview.
- [x] T119 Theming docs: add `frontend/docs/theming.md` with tokens, override recipes, and Theme Studio usage.
- [x] T120 Customization guide: `frontend/docs/customization.md` covering layout, widgets, saved views, and sharing.

## Maintenance & Dependency Upgrades

- [ ] T134 [P] Upgrade `zod` to v4.x and migrate code/tests accordingly (schema types, resolver usage). Ensure build/tests green.
- [ ] T135 [P] Upgrade `@hookform/resolvers` to v5.x and update imports/integration with React Hook Form and Zod v4.
- [ ] T136 Upgrade `jsdom` to v27.x for Vitest; adjust config or test helpers if API changes impact env.
- [ ] T137 Upgrade `@rushstack/eslint-patch` to latest and verify ESLint config behavior remains unchanged.

## Backend Support for Customization (APIs)

- [x] T121 [P] Contract: extend OpenAPI with:
  - GET/PUT `/me/preferences` → `{ theme, density, locale, layouts? }`
  - GET/PUT `/leagues/{leagueId}/branding` → `{ theme?, logo_url?, name? }`
- [x] T122 [P] Implement endpoints + models: add `UserPreference` and `LeagueBranding` models; services; routers.
- [x] T123 [P] Frontend client: add `getPreferences`, `updatePreferences`, `getLeagueBranding`, `updateLeagueBranding` and integrate with ThemeProvider + Dashboard.
- [ ] T124 Migrations: Alembic migration for new tables and necessary indexes.
- [x] T124 Migrations: Alembic migration for new tables and necessary indexes.

## Parallel Execution Examples (Customizability)

```
# Theming + dashboards in parallel
task run "T098" & task run "T099" & task run "T102" & task run "T103" && wait

# Preferences + APIs + wiring
task run "T115" & task run "T121" & task run "T122" & task run "T123" && wait

# Docs + a11y + command palette
task run "T111" & task run "T113" & task run "T118" & task run "T119" && wait
```

# Next Tasks: UI Migration & Polish

- [x] T125 [P] Migrate Toast to Radix primitives; preserve API; add accessible close; live region.
- [x] T126 [P] Migrate Modal to Radix Dialog; preserve props; focus management.
- [x] T127 [P] Refactor Button to class-variance-authority + tailwind-merge; keep loading state.
- [x] T128 Icons + header polish: add lucide-react icons in header and actions; refine mobile nav affordances.
- [ ] T129 Toast motion & interactions: enable Radix swipe-to-dismiss, add subtle enter/exit animations, stacking behavior.
- [x] T129 Toast motion & interactions: enable Radix swipe-to-dismiss, add subtle enter/exit animations, stacking behavior.
- [ ] T130 Create League: map backend 422 validation errors into field-level messages; show form-level summary.
- [x] T130 Create League: map backend 422 validation errors into field-level messages; show form-level summary.
- [x] T131 Managers tab tests: cover list render, empty state, and keyboard navigation focus order.
- [x] T132 Waivers list UX: add sort/filter controls and saved preferences (per-user); maintain mobile readability.
- [x] T133 Docs: add a short guide to using Radix primitives and CVA patterns in frontend/README.md.

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

- [x] T045 [P] Unit test: Scoring aggregation — create `backend/tests/unit/test_scoring_service_aggregate.py` to seed teams, lineups, and player scores, then assert `ScoringService.compute_league_scoreboard(league_id, game_day=None)` returns per‑team totals (e.g., sum of `stats.points`) sorted descending.
- [x] T046 [P] Integration test: Scoreboard endpoint aggregation — create `backend/tests/integration/test_scoreboard_aggregate.py` to create a league, set lineups, ingest scores, then `GET /leagues/{leagueId}/scoreboard` returns structured items with totals and team identifiers.
- [x] T047 [P] Integration test: JWT auth — create `backend/tests/integration/test_auth_jwt.py` that issues a valid HS256 dev token (via `AUTH_MODE=dev` and `AUTH_DEV_SECRET`) and asserts protected endpoints reject requests without Authorization and accept with a valid token.

## Scoreboard Aggregation

- [x] T048 Implement aggregation in `backend/src/services/scoring_service.py`: add `compute_league_scoreboard(league_id: UUID, game_day: date | None)` that
  - Joins `Lineup` and `Score` by `player_id` and `game_day` (all days if `game_day is None`).
  - Sums `stats.points` per team, returns a list of items `{ team_id, total_points, lineup_count }` sorted by `total_points` desc.
  - Handles missing/empty stats as 0; SQLite compatibility maintained.
- [x] T049 Update API response in `backend/src/api/scoreboard.py` to call `ScoringService.compute_league_scoreboard` and return `ScoreboardResponse` with `items: [{ team_id, total_points }]` (may include `team_name` later when joining `Team`).
- [x] T050 Performance: add DB indexes for aggregation — create Alembic migration `backend/alembic/versions/<timestamp>_scoreboard_indexes.py` adding indexes on `scores (player_id, game_day)` and `lineups (team_id, game_day)`.
- [x] T051 [P] Docs: update `specs/001-ultimate-fantasy-platform/docs/api.md` to document the scoreboard item shape and example payloads.

## Auth Upgrade (JWT)

- [x] T052 [P] Backend deps: add `PyJWT[crypto]==2.9.0` to `backend/pyproject.toml` and run `uv sync`. Document env in `backend/README.md`.
- [x] T053 Implement JWT verification in `backend/src/api/middleware/auth.py`:
  - Support `Authorization: Bearer <token>`.
  - Modes via env: `AUTH_MODE=dev|jwks`.
    - `dev`: HS256 using `AUTH_DEV_SECRET`.
    - `jwks`: RS256 using `AUTH_JWKS_URL` (fetch with `httpx`), validate `aud` and `iss` via `AUTH_AUDIENCE`, `AUTH_ISSUER`.
  - Populate `request.state.user_id` (from `sub`) and `request.state.user_claims`.
- [x] T054 [P] Add `get_current_user_id()` in `backend/src/api/deps.py` that raises 401 when absent/invalid. Update write endpoints to depend on it. Keep compatibility to accept `x-user-id` only when `AUTH_MODE=dev`.
- [x] T055 Persist/update users: add `backend/src/services/user_service.py` with `ensure_user_from_claims(claims)` to upsert `User` on first seen `sub`/`email`. Wire it in the auth middleware for requests that have valid tokens.
- [x] T056 [P] Tests for auth:
  - Unit: `backend/tests/unit/test_auth_middleware.py` (token decode branches, bad sig, wrong aud/iss).
  - Integration: extend existing endpoint tests to use `Authorization` header under `AUTH_MODE=dev`. Remove reliance on `x-user-id` except where explicitly xfail‑marked for backwards compatibility.
- [x] T057 Frontend auth header: update `frontend/src/services/api.ts` to inject `Authorization: Bearer <token>` from `localStorage` (e.g., `uf_token`), fallback to none in dev. Update docs with a helper to set a dev token.

## E2E Tests (Playwright)

- [x] T058 [P] Add Playwright to frontend: dev dependency `@playwright/test@1.48.2`. Create `frontend/playwright.config.ts` with baseURL from `process.env.E2E_BASE_URL` (default `http://localhost:3000`). Add npm scripts: `test:e2e`, `e2e:headed`.
- [x] T059 [P] Author tests under `frontend/tests/e2e/`:
  - `leagues.spec.ts`: create league flow → asserts success banner and API 201.
  - `join.spec.ts`: join league from invite link → asserts membership.
  - `lineup.spec.ts`: set lineup → asserts 200 and UI echo.
  - `scoreboard.spec.ts`: view scoreboard → asserts aggregated items rendered.
  - `waivers.spec.ts`: place waiver bid → asserts 201.
  Each test sets a dev HS256 token into `localStorage` before navigation.
- [x] T060 CI: extend `/.github/workflows/ci.yml` with job `frontend-e2e` that uses Node 20, installs deps, runs `npx playwright install --with-deps`, starts backend (uvicorn) and frontend (Next.js) concurrently, waits on healthchecks, then runs `npm run test:e2e`. Use env: `AUTH_MODE=dev`, `AUTH_DEV_SECRET`, `NEXT_PUBLIC_API_URL`.
- [x] T061 [P] E2E compose: optional `docker-compose.e2e.yml` to run postgres, backend, frontend with seeded env for e2e. Add `scripts/e2e.sh` to orchestrate start/wait/test/teardown locally.
- [x] T062 Docs: update `README.md` with JWT auth instructions, how to mint a dev HS256 token, and how to run E2E locally and in CI.

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
