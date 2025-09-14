# Tasks: Frontend Shared Logic Extraction for NextJS + React Native

**Input**: Design documents from `/specs/003-2-frontend-shared/`
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
- **Web app**: `packages/`, `frontend/src/` at repository root
- Paths shown below follow web application structure from plan.md

## Phase 3.1: Setup
- [ ] T001 Create packages directory structure (shared-logic, ui-components, api-client, mobile-app)
- [ ] T002 [P] Initialize shared-logic package in packages/shared-logic/package.json
- [ ] T003 [P] Initialize ui-components package in packages/ui-components/package.json
- [ ] T004 [P] Initialize api-client package in packages/api-client/package.json
- [ ] T005 Configure TypeScript configs for all packages with shared path mappings
- [ ] T006 [P] Configure linting and formatting for shared packages
- [ ] T007 [P] Set up Rollup build configuration for shared packages

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T008 [P] Contract test SharedPackage manifest validation in packages/shared-logic/src/__tests__/contract/package-manifest.test.ts
- [ ] T009 [P] Contract test UIComponent props validation in packages/ui-components/src/__tests__/contract/component-props.test.ts
- [ ] T010 [P] Contract test SharedHook signature validation in packages/shared-logic/src/__tests__/contract/shared-hooks.test.ts
- [ ] T011 [P] Integration test API service extraction in packages/api-client/src/__tests__/integration/api-extraction.test.ts
- [ ] T012 [P] Integration test UI component sharing in packages/ui-components/src/__tests__/integration/component-sharing.test.ts
- [ ] T013 [P] Integration test business logic sharing in packages/shared-logic/src/__tests__/integration/logic-sharing.test.ts
- [ ] T014 [P] Integration test cross-platform state management in packages/shared-logic/src/__tests__/integration/state-sharing.test.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T015 [P] SharedPackage model in packages/shared-logic/src/models/SharedPackage.ts
- [ ] T016 [P] Export model in packages/shared-logic/src/models/Export.ts
- [ ] T017 [P] ApiService model in packages/api-client/src/models/ApiService.ts
- [ ] T018 [P] Endpoint model in packages/api-client/src/models/Endpoint.ts
- [ ] T019 [P] UIComponent model in packages/ui-components/src/models/UIComponent.ts
- [ ] T020 [P] DesignToken model in packages/ui-components/src/models/DesignToken.ts
- [ ] T021 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/leagues.ts
- [ ] T022 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/scoreboard.ts
- [ ] T023 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/waivers.ts
- [ ] T024 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/lineups.ts
- [ ] T025 Move frontend/src/lib/dashboard.ts to packages/shared-logic/src/utils/dashboard.ts
- [ ] T026 [P] Create shared HTTP client in packages/api-client/src/client/http.ts
- [ ] T027 [P] Create platform adapter system in packages/ui-components/src/adapters/platform.ts
- [ ] T028 [P] Create design token system in packages/ui-components/src/tokens/design-tokens.ts

## Phase 3.4: Integration
- [ ] T029 Update frontend components to import API services from packages/api-client
- [ ] T030 Update frontend components to import business logic from packages/shared-logic
- [ ] T031 Extract Button component from frontend/src/components/ui/button.tsx to packages/ui-components/src/primitives/Button.tsx
- [ ] T032 Extract Card component from frontend/src/components/ui/card.tsx to packages/ui-components/src/primitives/Card.tsx
- [ ] T033 Extract Input component from frontend/src/components/ui/input.tsx to packages/ui-components/src/forms/Input.tsx
- [ ] T034 Extract Modal component from frontend/src/components/ui/modal.tsx to packages/ui-components/src/navigation/Modal.tsx
- [ ] T035 Update frontend components to import UI components from packages/ui-components
- [ ] T036 [P] Configure shared state management with Zustand in packages/shared-logic/src/store/
- [ ] T037 [P] Set up shared validation schemas with Zod in packages/shared-logic/src/validation/

## Phase 3.5: Mobile App Initialization
- [ ] T038 Initialize React Native Expo app in packages/mobile-app/
- [ ] T039 Configure packages/mobile-app/package.json to use shared packages as dependencies
- [ ] T040 [P] Create test component using shared API client in packages/mobile-app/src/components/TestApiClient.tsx
- [ ] T041 [P] Create test component using shared UI components in packages/mobile-app/src/components/TestUIComponents.tsx
- [ ] T042 [P] Create test component using shared business logic in packages/mobile-app/src/components/TestLogic.tsx
- [ ] T043 Configure platform-specific styling adapters for React Native in packages/ui-components/src/adapters/mobile.ts

## Phase 3.6: Polish
- [ ] T044 [P] Unit tests for dashboard utilities in packages/shared-logic/src/utils/__tests__/dashboard.test.ts
- [ ] T045 [P] Unit tests for HTTP client in packages/api-client/src/client/__tests__/http.test.ts
- [ ] T046 [P] Unit tests for design tokens in packages/ui-components/src/tokens/__tests__/design-tokens.test.ts
- [ ] T047 [P] Performance validation: shared packages bundle size < 50KB each
- [ ] T048 [P] Performance validation: NextJS app load time unchanged
- [ ] T049 [P] Performance validation: shared module load time < 100ms
- [ ] T050 [P] Update package documentation in packages/*/README.md
- [ ] T051 Run complete quickstart validation from specs/003-2-frontend-shared/quickstart.md
- [ ] T052 [P] Update frontend/package.json workspace configuration
- [ ] T053 [P] Update root package.json workspace configuration

## Dependencies
- Setup (T001-T007) before all other tasks
- Tests (T008-T014) before implementation (T015-T043)
- Models (T015-T020) before services and extraction (T021-T028)
- API extraction (T021-T025) before integration (T029-T030)
- UI models (T019-T020) before UI extraction (T031-T035)
- Shared packages complete (T015-T037) before mobile app (T038-T043)
- Implementation before polish (T044-T053)

## Parallel Example
```bash
# Launch T008-T014 together (contract and integration tests):
Task --subagent_type=general-purpose --description="Contract test SharedPackage" --prompt="Write failing contract test for SharedPackage manifest validation in packages/shared-logic/src/__tests__/contract/package-manifest.test.ts"
Task --subagent_type=general-purpose --description="Contract test UIComponent" --prompt="Write failing contract test for UIComponent props validation in packages/ui-components/src/__tests__/contract/component-props.test.ts"
Task --subagent_type=general-purpose --description="Contract test SharedHook" --prompt="Write failing contract test for SharedHook signature validation in packages/shared-logic/src/__tests__/contract/shared-hooks.test.ts"
Task --subagent_type=general-purpose --description="Integration test API extraction" --prompt="Write failing integration test for API service extraction in packages/api-client/src/__tests__/integration/api-extraction.test.ts"

# Launch T015-T020 together (model creation):
Task --subagent_type=general-purpose --description="Create SharedPackage model" --prompt="Implement SharedPackage model in packages/shared-logic/src/models/SharedPackage.ts"
Task --subagent_type=general-purpose --description="Create Export model" --prompt="Implement Export model in packages/shared-logic/src/models/Export.ts"
Task --subagent_type=general-purpose --description="Create ApiService model" --prompt="Implement ApiService model in packages/api-client/src/models/ApiService.ts"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task completion
- Follow TDD: RED (failing test) → GREEN (minimal implementation) → REFACTOR

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - shared-package.json → T008 contract test [P]
   - ui-component.json → T009 contract test [P]
   - shared-hook.json → T010 contract test [P]

2. **From Data Model**:
   - SharedPackage → T015 model task [P]
   - Export → T016 model task [P]
   - ApiService → T017 model task [P]
   - Endpoint → T018 model task [P]
   - UIComponent → T019 model task [P]
   - DesignToken → T020 model task [P]

3. **From User Stories**:
   - API extraction → T011 integration test [P]
   - UI sharing → T012 integration test [P]
   - Logic sharing → T013 integration test [P]
   - State management → T014 integration test [P]

4. **From Quickstart Scenarios**:
   - API layer extraction → T021-T025 (sequential)
   - UI component extraction → T031-T035 (sequential)
   - Mobile app setup → T038-T043 (mixed)

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T008-T010)
- [x] All entities have model tasks (T015-T020)
- [x] All tests come before implementation (T008-T014 before T015+)
- [x] Parallel tasks truly independent (different files/packages)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task