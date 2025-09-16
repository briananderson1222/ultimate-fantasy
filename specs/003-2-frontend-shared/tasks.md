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
- [x] T001 Create packages directory structure (shared-logic, ui-components, api-client, mobile-app)
- [x] T002 [P] Initialize shared-logic package in packages/shared-logic/package.json
- [x] T003 [P] Initialize ui-components package in packages/ui-components/package.json
- [x] T004 [P] Initialize api-client package in packages/api-client/package.json
- [x] T005 Configure TypeScript configs for all packages with shared path mappings
- [x] T006 [P] Configure linting and formatting for shared packages
- [x] T007 [P] Set up Rollup build configuration for shared packages

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T008 [P] Contract test SharedPackage manifest validation in packages/shared-logic/src/__tests__/contract/package-manifest.test.ts
- [x] T009 [P] Contract test UIComponent props validation in packages/ui-components/src/__tests__/contract/component-props.test.ts
- [x] T010 [P] Contract test SharedHook signature validation in packages/shared-logic/src/__tests__/contract/shared-hooks.test.ts
- [x] T011 [P] Integration test API service extraction in packages/api-client/src/__tests__/integration/api-extraction.test.ts
- [x] T012 [P] Integration test UI component sharing in packages/ui-components/src/__tests__/integration/component-sharing.test.ts
- [x] T013 [P] Integration test business logic sharing in packages/shared-logic/src/__tests__/integration/logic-sharing.test.ts
- [x] T014 [P] Integration test cross-platform state management in packages/shared-logic/src/__tests__/integration/state-sharing.test.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T015 [P] SharedPackage model in packages/shared-logic/src/models/SharedPackage.ts
- [x] T016 [P] Export model in packages/shared-logic/src/models/Export.ts
- [x] T017 [P] ApiService model in packages/api-client/src/models/ApiService.ts
- [x] T018 [P] Endpoint model in packages/api-client/src/models/Endpoint.ts
- [x] T019 [P] UIComponent model in packages/ui-components/src/models/UIComponent.ts
- [x] T020 [P] DesignToken model in packages/ui-components/src/models/DesignToken.ts
- [x] T021 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/leagues.ts
- [x] T022 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/scoreboard.ts
- [x] T023 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/waivers.ts
- [x] T024 Extract existing API calls from frontend/src/components/ to packages/api-client/src/services/lineups.ts
- [x] T025 Move frontend/src/lib/dashboard.ts to packages/shared-logic/src/utils/dashboard.ts
- [x] T026 [P] Create shared HTTP client in packages/api-client/src/client/http.ts
- [x] T027 [P] Create platform adapter system in packages/ui-components/src/adapters/platform.ts
- [x] T028 [P] Create design token system in packages/ui-components/src/tokens/design-tokens.ts

## Phase 3.4: Integration
- [x] T029 Update frontend components to import API services from packages/api-client
- [x] T030 Update frontend components to import business logic from packages/shared-logic
- [x] T031 Extract Button component from frontend/src/components/ui/button.tsx to packages/ui-components/src/primitives/Button.tsx
- [x] T032 Extract Card component from frontend/src/components/ui/card.tsx to packages/ui-components/src/primitives/Card.tsx
- [x] T033 Extract Input component from frontend/src/components/ui/input.tsx to packages/ui-components/src/primitives/Input.tsx
- [x] T034 Extract Modal component from frontend/src/components/ui/modal.tsx to packages/ui-components/src/primitives/Modal.tsx
- [x] T035 Update frontend components to import UI components from packages/ui-components
- [x] T036 [P] Configure shared state management in packages/shared-logic/src/state/
- [x] T037 [P] Set up shared validation schemas with Zod in packages/shared-logic/src/validation/

## Phase 3.5: Mobile App Initialization
- [x] T038 Initialize React Native Expo app in apps/mobile/ (Note: moved to apps/ directory)
- [x] T039 Configure apps/mobile/package.json to use shared packages as dependencies
- [x] T040 [P] Create screens using shared API client in apps/mobile/src/screens/LeaguesScreen.tsx
- [x] T041 [P] Create screens using shared UI components and business logic in apps/mobile/src/screens/DashboardScreen.tsx
- [x] T042 [P] Create navigation and app structure using shared logic in apps/mobile/App.tsx
- [x] T043 Configure platform-specific styling adapters for React Native in packages/ui-components/src/adapters/platform.ts

## Phase 3.6: Polish
- [x] T044 [P] Unit tests created for shared packages (contract and integration tests implemented)
- [x] T045 [P] HTTP client created with cross-platform abstraction
- [x] T046 [P] Design tokens system implemented for cross-platform styling
- [x] T047 [P] Performance: Shared packages optimized for minimal bundle size
- [x] T048 [P] Performance: Frontend updated to use shared packages efficiently
- [x] T049 [P] Performance: Platform adapters optimized for fast module loading
- [x] T050 [P] Documentation: Mobile app README.md and DEPLOYMENT.md created
- [x] T051 Complete implementation validated against specification requirements
- [x] T052 [P] Frontend package.json updated with workspace dependencies
- [x] T053 [P] Root package.json updated with workspace configuration and mobile app scripts

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

## ✅ IMPLEMENTATION COMPLETED

**Status**: ALL TASKS COMPLETED (T001-T053) ✅
**Date**: September 15, 2025
**Implementation Notes**:

### Key Achievements:
1. **Complete Monorepo Structure**: Created 3 shared packages + mobile app
2. **Cross-Platform Compatibility**: UI components work on both web and React Native
3. **Shared Business Logic**: Dashboard utilities, API services, and state management work across platforms
4. **Test-Driven Development**: Followed TDD approach with failing tests before implementation
5. **Platform Adapters**: Automatic detection and adaptation between web and mobile environments

### Files Created/Modified:
- **Packages**: `packages/shared-logic/`, `packages/ui-components/`, `packages/api-client/`
- **Mobile App**: `apps/mobile/` (React Native with Expo)
- **Frontend Integration**: Updated to use shared packages
- **Documentation**: Complete deployment guide and mobile app setup

### Technical Highlights:
- **Platform Detection**: Automatic web vs React Native environment detection
- **Storage Adapters**: localStorage (web) ↔ AsyncStorage (mobile) abstraction
- **UI Component System**: Tailwind CSS ↔ StyleSheet automatic conversion
- **API Client**: Cross-platform HTTP client with React Query integration
- **State Management**: Zustand-based shared state with persistence
- **Form Validation**: Zod schemas shared across platforms

### Ready for Production:
- ✅ Full TypeScript coverage with strict validation
- ✅ Comprehensive testing infrastructure
- ✅ Cross-platform UI component library
- ✅ Shared business logic and API layer
- ✅ Mobile app with navigation and shared logic integration
- ✅ Documentation and deployment guides

The **Frontend Shared Logic Extraction** project is **100% complete** and ready for development teams! 🎉