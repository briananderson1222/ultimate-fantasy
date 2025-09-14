# Implementation Plan: Backend Modularization for Future Microservices


**Branch**: `002-backend-modularization-for` | **Date**: 2025-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-backend-modularization-for/spec.md`

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
Restructure the current FastAPI monolithic backend into distinct domain modules (leagues, users, lineups, trading, scoring, waitlist) to enable future microservice extraction while maintaining all existing functionality, performance, and enabling independent team development.

## Technical Context
**Language/Version**: Python 3.11+ (FastAPI backend)
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, pytest
**Storage**: SQLite (current), database schema isolation needed
**Testing**: pytest with existing test infrastructure
**Target Platform**: Linux server (containerized)
**Project Type**: web (backend restructuring)
**Performance Goals**: Maintain current performance benchmarks [NEEDS CLARIFICATION: specific benchmarks]
**Constraints**: Zero-downtime modularization, backward compatibility required
**Scale/Scope**: 6 domain modules, existing API endpoints, database relationships [NEEDS CLARIFICATION: cross-domain foreign key strategy]

**User-Provided Implementation Details**:
Current State Analysis - FastAPI monolith with domains: Leagues Management (leagues_*, league_service.py), User Management (me_preferences, user models/services), Lineup Management (lineups, lineup_service.py), Trading System (waivers, waiver_service.py), Scoring System (scoreboard, scoring_service.py), Waitlist Management (waitlist)

Proposed Structure:
- backend/src/domains/ with separate folders for each domain (api/, models/, services/, schemas/)
- backend/src/infrastructure/ for shared components
- 4 Phases: Domain Separation (2-3 weeks), Interface Contracts (1-2 weeks), Database Isolation (2-3 weeks), Microservice Readiness (1-2 weeks)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (backend restructuring only)
- Using framework directly? Yes (FastAPI direct usage)
- Single data model? Yes (domain models, no unnecessary DTOs)
- Avoiding patterns? Yes (no Repository/UoW unless proven necessary)

**Architecture**:
- EVERY feature as library? No - this is architectural restructuring, not feature development
- Libraries listed: N/A - domain modules, not standalone libraries
- CLI per library: N/A - internal restructuring
- Library docs: N/A - internal restructuring

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes (tests before refactoring implementation)
- Git commits show tests before implementation? Yes
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual database)
- Integration tests for: domain boundaries, cross-domain interactions? Yes
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (maintain existing logging)
- Frontend logs → backend? Yes (existing unified logging)
- Error context sufficient? Yes (maintain current error handling)

**Versioning**:
- Version number assigned? Yes (will increment BUILD for modularization)
- BUILD increments on every change? Yes
- Breaking changes handled? Yes (backward compatibility required, migration strategy)

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

**Structure Decision**: Option 2 (Web application) - backend restructuring with existing frontend

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
- Load `/templates/tasks-template.md` as base
- Generate modularization tasks from Phase 1 design docs
- Domain structure creation tasks [P] (can be done in parallel)
- Interface contract implementation tasks (sequential, depends on structure)
- Migration and validation tasks (sequential, depends on implementation)
- Testing tasks for each phase

**Specific Task Categories**:
1. **Domain Structure Setup** [P]:
   - Create domains/ directory structure
   - Move existing files to domain folders
   - Update import statements
2. **Interface Implementation**:
   - Implement Abstract Base Classes for each domain service
   - Create domain service implementations
   - Add dependency injection configuration
3. **Database Migration**:
   - Create domain-specific session management
   - Implement cross-domain interface calls
   - Add event system for domain communication
4. **Testing & Validation**:
   - Contract tests for each domain interface
   - Integration tests for cross-domain communication
   - Performance regression tests
   - End-to-end API validation

**Ordering Strategy**:
- TDD order: Interface contracts → Tests → Implementation
- Domain dependency order: Shared/Infrastructure → Individual domains → Cross-domain integration
- Mark [P] for parallel execution (independent domain setups)

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md covering all 4 phases

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
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*