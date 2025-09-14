# Tasks: Modern Fantasy Sports Design System

**Input**: Design documents from `/specs/004-design-system-insights/`
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

## Format: `[ID] [P] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/src/`, `frontend/tests/`
- **Design System**: `frontend/src/components/design-system/`
- Paths based on existing web application structure

## Phase 3.1: Setup

- [ ] T001 Install design system dependencies (@dnd-kit/core, framer-motion, @storybook/react) in frontend/package.json
- [ ] T002 [P] Create design system folder structure in frontend/src/components/design-system/{tokens,primitives,patterns,templates}
- [ ] T003 [P] Configure Storybook for design system in frontend/.storybook/
- [ ] T004 [P] Set up Playwright visual regression testing in frontend/tests/visual/

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Design Token Tests
- [ ] T005 [P] Storybook story for ThemeProvider component in frontend/.storybook/stories/ThemeProvider.stories.tsx
- [ ] T006 [P] Storybook story for Color Tokens in frontend/.storybook/stories/ColorTokens.stories.tsx
- [ ] T007 [P] Storybook story for Typography Tokens in frontend/.storybook/stories/TypographyTokens.stories.tsx

### Primitive Component Tests
- [ ] T008 [P] Storybook story for ProgressBar component in frontend/.storybook/stories/ProgressBar.stories.tsx
- [ ] T009 [P] Storybook story for Button variants in frontend/.storybook/stories/Button.stories.tsx
- [ ] T010 [P] Storybook story for Card component in frontend/.storybook/stories/Card.stories.tsx

### Pattern Component Tests
- [ ] T011 [P] Storybook story for MatchCard component in frontend/.storybook/stories/MatchCard.stories.tsx
- [ ] T012 [P] Storybook story for PlayerCard component in frontend/.storybook/stories/PlayerCard.stories.tsx
- [ ] T013 [P] Storybook story for SettingsGrid component in frontend/.storybook/stories/SettingsGrid.stories.tsx
- [ ] T014 [P] Storybook story for TrendingPlayers component in frontend/.storybook/stories/TrendingPlayers.stories.tsx
- [ ] T015 [P] Storybook story for LeagueChat component in frontend/.storybook/stories/LeagueChat.stories.tsx

### Integration Tests
- [ ] T016 [P] Theme switching integration test in frontend/tests/integration/theme-switching.test.tsx
- [ ] T017 [P] Match card display integration test in frontend/tests/integration/match-card-display.test.tsx
- [ ] T018 [P] Player management drag-drop integration test in frontend/tests/integration/player-management.test.tsx
- [ ] T019 [P] Trending players filtering integration test in frontend/tests/integration/trending-players.test.tsx
- [ ] T020 [P] League chat messaging integration test in frontend/tests/integration/league-chat.test.tsx

### Visual Regression Tests
- [ ] T021 [P] Visual regression test for dark theme in frontend/tests/visual/dark-theme.spec.ts
- [ ] T022 [P] Visual regression test for light theme in frontend/tests/visual/light-theme.spec.ts
- [ ] T023 [P] Visual regression test for responsive breakpoints in frontend/tests/visual/responsive.spec.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Design Tokens Implementation
- [ ] T024 [P] Color tokens definition in frontend/src/components/design-system/tokens/colors.ts
- [ ] T025 [P] Typography tokens definition in frontend/src/components/design-system/tokens/typography.ts
- [ ] T026 [P] Spacing tokens definition in frontend/src/components/design-system/tokens/spacing.ts
- [ ] T027 [P] Shadow tokens definition in frontend/src/components/design-system/tokens/shadows.ts

### Theme System Implementation
- [ ] T028 ThemeProvider context implementation in frontend/src/components/design-system/providers/ThemeProvider.tsx
- [ ] T029 Theme hook implementation in frontend/src/components/design-system/hooks/useTheme.ts
- [ ] T030 CSS custom properties setup in frontend/src/styles/design-tokens.css

### Primitive Components Implementation
- [ ] T031 [P] ProgressBar component implementation in frontend/src/components/design-system/primitives/ProgressBar.tsx
- [ ] T032 [P] Button component with variants in frontend/src/components/design-system/primitives/Button.tsx
- [ ] T033 [P] Card component implementation in frontend/src/components/design-system/primitives/Card.tsx
- [ ] T034 [P] Avatar component implementation in frontend/src/components/design-system/primitives/Avatar.tsx
- [ ] T035 [P] Badge component implementation in frontend/src/components/design-system/primitives/Badge.tsx

### Pattern Components Implementation
- [ ] T036 [P] MatchCard component implementation in frontend/src/components/design-system/patterns/MatchCard.tsx
- [ ] T037 [P] PlayerCard component implementation in frontend/src/components/design-system/patterns/PlayerCard.tsx
- [ ] T038 [P] SettingsGrid component implementation in frontend/src/components/design-system/patterns/SettingsGrid.tsx
- [ ] T039 [P] TrendingPlayers component implementation in frontend/src/components/design-system/patterns/TrendingPlayers.tsx
- [ ] T040 LeagueChat component implementation in frontend/src/components/design-system/patterns/LeagueChat.tsx

## Phase 3.4: Integration

### Theme Integration
- [ ] T041 Integrate ThemeProvider in frontend/src/app/layout.tsx
- [ ] T042 Add theme toggle component to user preferences
- [ ] T043 Implement theme persistence in localStorage

### Component Library Export
- [ ] T044 Create design system index exports in frontend/src/components/design-system/index.ts
- [ ] T045 Update existing pages to use new components
- [ ] T046 Replace legacy card components with new MatchCard

### Animation System
- [ ] T047 [P] Framer Motion page transitions in frontend/src/components/design-system/animations/PageTransitions.tsx
- [ ] T048 [P] Micro-interaction animations in frontend/src/components/design-system/animations/MicroInteractions.tsx
- [ ] T049 Drag-and-drop visual feedback implementation

## Phase 3.5: Polish

### Component Testing
- [ ] T050 [P] Unit tests for ProgressBar component in frontend/tests/unit/ProgressBar.test.tsx
- [ ] T051 [P] Unit tests for MatchCard component in frontend/tests/unit/MatchCard.test.tsx
- [ ] T052 [P] Unit tests for PlayerCard component in frontend/tests/unit/PlayerCard.test.tsx
- [ ] T053 [P] Unit tests for theme switching logic in frontend/tests/unit/useTheme.test.ts

### Accessibility & Performance
- [ ] T054 [P] Accessibility audit and fixes for all components
- [ ] T055 [P] Performance optimization: lazy loading for animations
- [ ] T056 [P] Bundle size analysis and optimization
- [ ] T057 [P] WCAG 2.1 AA compliance testing

### Documentation
- [ ] T058 [P] Component API documentation in frontend/docs/design-system.md
- [ ] T059 [P] Migration guide from old components in frontend/docs/migration.md
- [ ] T060 [P] Storybook addon configuration for accessibility testing

### Validation
- [ ] T061 Execute Theme System Validation from quickstart.md
- [ ] T062 Execute Match Card Display Validation from quickstart.md
- [ ] T063 Execute Player Management Validation from quickstart.md
- [ ] T064 Execute Trending Players Validation from quickstart.md
- [ ] T065 Execute League Chat Integration Validation from quickstart.md

## Dependencies

### Critical Dependencies
- Tests (T005-T023) before implementation (T024-T040)
- Design tokens (T024-T027) before components (T031-T040)
- ThemeProvider (T028) before theme integration (T041-T043)
- Primitive components (T031-T035) before pattern components (T036-T040)

### Implementation Dependencies
- T028 blocks T029, T041
- T024-T027 block T031-T040
- T031-T035 block T036-T040
- T044 requires T024-T040 complete
- T045-T046 require T044 complete

### Validation Dependencies
- T061-T065 require all implementation tasks complete

## Parallel Execution Examples

### Design Token Stories (can run together)
```bash
# Launch T005-T007 together:
Task: "Storybook story for ThemeProvider component in frontend/.storybook/stories/ThemeProvider.stories.tsx"
Task: "Storybook story for Color Tokens in frontend/.storybook/stories/ColorTokens.stories.tsx"
Task: "Storybook story for Typography Tokens in frontend/.storybook/stories/TypographyTokens.stories.tsx"
```

### Primitive Component Stories (can run together)
```bash
# Launch T008-T010 together:
Task: "Storybook story for ProgressBar component in frontend/.storybook/stories/ProgressBar.stories.tsx"
Task: "Storybook story for Button variants in frontend/.storybook/stories/Button.stories.tsx"
Task: "Storybook story for Card component in frontend/.storybook/stories/Card.stories.tsx"
```

### Token Implementation (can run together)
```bash
# Launch T024-T027 together:
Task: "Color tokens definition in frontend/src/components/design-system/tokens/colors.ts"
Task: "Typography tokens definition in frontend/src/components/design-system/tokens/typography.ts"
Task: "Spacing tokens definition in frontend/src/components/design-system/tokens/spacing.ts"
Task: "Shadow tokens definition in frontend/src/components/design-system/tokens/shadows.ts"
```

### Primitive Components (can run together)
```bash
# Launch T031-T035 together:
Task: "ProgressBar component implementation in frontend/src/components/design-system/primitives/ProgressBar.tsx"
Task: "Button component with variants in frontend/src/components/design-system/primitives/Button.tsx"
Task: "Card component implementation in frontend/src/components/design-system/primitives/Card.tsx"
Task: "Avatar component implementation in frontend/src/components/design-system/primitives/Avatar.tsx"
Task: "Badge component implementation in frontend/src/components/design-system/primitives/Badge.tsx"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify Storybook stories and tests fail before implementing components
- Commit after each task completion
- Visual regression tests capture component appearance
- Design tokens must be implemented before any components
- Theme system must work before component integration

## Task Generation Rules
*Applied during main() execution*

1. **From Component Contracts**:
   - MatchCard contract → T011 story + T036 implementation
   - PlayerCard contract → T012 story + T037 implementation
   - SettingsGrid contract → T013 story + T038 implementation
   - TrendingPlayers contract → T014 story + T039 implementation
   - LeagueChat contract → T015 story + T040 implementation
   - ProgressBar contract → T008 story + T031 implementation
   - ThemeProvider contract → T005 story + T028 implementation

2. **From Data Model**:
   - Theme Configuration entity → T024-T027 token tasks
   - Color Tokens entity → T024 colors.ts task
   - Match Card Data entity → T036 MatchCard.tsx task
   - Player Card Data entity → T037 PlayerCard.tsx task

3. **From Quickstart User Stories**:
   - Theme switching story → T016 integration test + T061 validation
   - Match card display story → T017 integration test + T062 validation
   - Player management story → T018 integration test + T063 validation
   - Trending players story → T019 integration test + T064 validation
   - League chat story → T020 integration test + T065 validation

4. **From Research Decisions**:
   - @dnd-kit/core dependency → T001 setup + T018 drag-drop test + T049 implementation
   - Framer Motion dependency → T001 setup + T047-T048 animation tasks
   - Storybook dependency → T003 setup + T005-T015 story tasks

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T005-T015)
- [x] All entities have model/implementation tasks (T024-T040)
- [x] All tests come before implementation (T005-T023 before T024-T040)
- [x] Parallel tasks truly independent (different files, marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Integration tests cover all user scenarios from quickstart
- [x] Visual regression tests cover theme variations
- [x] Accessibility testing included in polish phase