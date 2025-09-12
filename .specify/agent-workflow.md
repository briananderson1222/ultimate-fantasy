# Agent Workflow: Ultimate Fantasy Platform

This repository follows Spec-Driven Development. The single source of truth for delivery is the feature tasks file:

- Feature tasks: `specs/001-ultimate-fantasy-platform/tasks.md`
- Contracts: `specs/001-ultimate-fantasy-platform/contracts/openapi.yml`

## Operating Principles
- Always run `.specify/scripts/check-task-prerequisites.sh --json` to resolve `FEATURE_DIR` and available docs.
- Work strictly in task order and TDD flow: Setup → Tests (RED) → Implementation (GREEN) → Refactor.
- After completing a task, update `tasks.md` to check it off, keep descriptions accurate, and avoid scope creep.
- Keep changes scoped to the files named in each task. Use [P] to parallelize only if tasks don’t touch the same file.
- Prefer small, frequent commits with conventional messages. Reference task IDs.

## Execution Loop (per task)
1) Read the next unchecked task in `tasks.md`.
2) If it’s a test task: write the test and ensure it fails (RED) without implementation.
3) If it’s an implementation task: make the smallest change to pass the existing failing tests (GREEN).
4) Run formatters and linters.
5) Run the relevant tests (start narrow near the changed code, then broaden).
6) Update `tasks.md` checkbox for the task and add any clarifying notes discovered.
7) Commit using a conventional message with the task ID.

## Commands
- Backend
  - Install: `cd backend && pip install -U pip && pip install -e .[dev]`
  - Lint/format: `ruff check . && black . && isort . && mypy .`
  - Test: `pytest -q`
- Frontend
  - Install: `cd frontend && npm install`
  - Lint/format: `npm run lint && npm run format:check`
  - Type check: `npm run typecheck`

## Commit Message Format (Conventional)
- `chore: ...` tooling, CI, docs
- `feat(api): ...` new API endpoints
- `feat(model): ...` new models
- `fix: ...` bug fixes
- `test(contract): ...` contract tests
- `test(integration): ...` integration tests
- `refactor: ...` code movement without behavior change

Always include the task ID, e.g. `test(contract): add OpenAPI coverage (T004)`.

## Parallelization Guidance
- Only run [P] tasks concurrently when they touch different files and have no dependency edges.
- Use the parallel examples block in `tasks.md` for safe combos.

## Validation Gates
- Before starting implementation, contract and integration tests for the scope must exist and fail.
- Before merging: all linters and tests pass locally and in CI.

