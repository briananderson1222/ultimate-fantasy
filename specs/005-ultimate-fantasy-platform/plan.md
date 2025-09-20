# Implementation Plan: Ultimate Fantasy Platform - Comprehensive Implementation

**Branch**: `005-ultimate-fantasy-platform` | **Date**: 2025-09-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-ultimate-fantasy-platform/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Transform the fantasy sports platform from foundation to professional-grade with real sports data integration, advanced fantasy features, mobile app feature parity, professional theming, real-time updates, social features, AI analytics, and performance optimization across 6 implementation phases. The platform will rival industry leaders like ESPN Fantasy or Yahoo Fantasy.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5.9+ (frontend), React Native (mobile)
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, Next.js 15, React 19, Expo 54, TanStack Query
**Storage**: PostgreSQL for primary data, Redis for caching, File storage for media
**Testing**: pytest (backend), Vitest (frontend), Jest (mobile), Playwright (E2E), Detox (mobile E2E)
**Target Platform**: Linux server (backend), Web browsers (frontend), iOS/Android (mobile)
**Project Type**: web + mobile (determines multi-app source structure)
**Performance Goals**: <200ms API response times, <300ms frontend load, 60fps mobile animations
**Constraints**: Real-time sports data updates, offline mobile capabilities, 99.9% uptime during peak
**Scale/Scope**: 10k+ concurrent users, millions of sports data points, 50+ mobile screens

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 3 (apps/api, apps/web, apps/mobile) ✓
- Using framework directly? Yes (FastAPI, Next.js, Expo directly) ✓
- Single data model? Yes (shared entities, no DTOs except API serialization) ✓
- Avoiding patterns? Yes (domain services, no Repository/UoW initially) ✓

**Architecture**:
- EVERY feature as library? Yes (packages/shared-logic, packages/api-client, packages/ui-components) ✓
- Libraries listed: api-client (HTTP client), shared-logic (business logic), ui-components (React components)
- CLI per library: Yes (uf api/logic/ui commands for dev workflow, testing, build)
- Library docs: llms.txt format planned? Yes (for each package)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (tests written first, must fail)
- Git commits show tests before implementation? Yes (enforced by git hooks)
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual PostgreSQL, Redis in tests)
- Integration tests for: new libraries, contract changes, shared schemas? Yes
- FORBIDDEN: Implementation before test, skipping RED phase ✓

**Observability**:
- Structured logging included? Yes (JSON logs, correlation IDs)
- Frontend logs → backend? Yes (unified logging pipeline)
- Error context sufficient? Yes (error tracking, user context)

**Versioning**:
- Version number assigned? Yes (MAJOR.MINOR.BUILD format)
- BUILD increments on every change? Yes (automated CI/CD)
- Breaking changes handled? Yes (API versioning, migration plans)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 & 3 Hybrid - Multi-app structure (apps/api, apps/web, apps/mobile) with shared packages/ libraries

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base template
- Generate tasks from Phase 1 artifacts:
  * 2 OpenAPI contracts → 2 contract test tasks [P]
  * 12 entities in data-model → 12 model creation tasks [P]
  * 5 quickstart scenarios → 5 integration test tasks [P]
  * 35 functional requirements → implementation tasks grouped by domain
  * CLI tools → 3 package CLI implementation tasks [P]

**Ordering Strategy**:
- **Setup Phase**: Environment, dependencies, linting configuration
- **Test Phase**: Contract tests → Integration tests → Unit test frameworks
- **Foundation Phase**: Database models → Service interfaces → Basic CRUD
- **Core Features**: Draft system → Trading → Scoring → Real-time updates
- **Advanced Features**: AI analytics → Mobile parity → Performance optimization
- **Polish Phase**: Documentation → Performance testing → Deployment

**Parallel Execution Groups**:
- [P] Contract tests (fantasy-api.yaml + sports-data-api.yaml)
- [P] Entity models (12 entities in separate files)
- [P] Package CLIs (api-client, shared-logic, ui-components)
- [P] Platform apps (web + mobile implementation)

**Estimated Output**: 45-50 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*