<!--
Sync Impact Report:
- Version change: template → 1.0.0
- Modified principles: All sections initialized from template
- Added sections: Package-First, API-First, Test-First, Platform-First, Observability
- Removed sections: N/A (initial constitution)
- Templates requiring updates: ✅ all validated
- Follow-up TODOs: None
-->

# Ultimate Fantasy Platform Constitution

## Core Principles

### I. Package-First
Every feature MUST start as a standalone package. Packages MUST be self-contained, independently testable, and documented. Clear business purpose required - no organizational-only packages. All packages MUST support both web and mobile platforms through unified interfaces.

**Rationale**: Ensures reusability across web and mobile applications while maintaining clear architectural boundaries and enabling parallel development.

### II. API-First
Every service MUST expose functionality via well-defined APIs. REST endpoints MUST follow OpenAPI specifications. All contract changes MUST be backward compatible or versioned. Real-time features MUST use WebSocket protocols with fallback mechanisms.

**Rationale**: Enables independent development of frontend applications, supports multiple client platforms, and ensures consistent integration patterns.

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. Contract tests MUST validate API specifications. Performance tests MUST verify <200ms p95 response times.

**Rationale**: Ensures code quality, prevents regressions, validates requirements early, and maintains performance standards under load.

### IV. Platform-First
All shared code MUST work on web and mobile platforms. UI components MUST support responsive design and native mobile interfaces. API clients MUST handle network failures and offline scenarios gracefully.

**Rationale**: Maximizes code reuse across platforms while providing optimal user experience on each target platform.

### V. Observability
Structured logging required using JSON format. All services MUST implement health checks and metrics collection. Performance monitoring MUST track key business metrics. Distributed tracing MUST be enabled for debugging complex flows.

**Rationale**: Enables proactive issue detection, supports data-driven optimization decisions, and facilitates rapid debugging in production environments.

## Technology Standards

TypeScript MUST be used for all frontend code with strict mode enabled. Python 3.11+ MUST be used for backend services with type hints required. Database schema changes MUST use migrations with rollback procedures. All code MUST pass linting (ESLint/ruff) and formatting (Prettier/black) checks.

## Quality Gates

Code review required for all changes with automated CI/CD checks. Test coverage MUST maintain >90% for critical business logic. Performance regression tests MUST pass before deployment. Security scans MUST clear before production release.

## Governance

This constitution supersedes all other development practices. Amendments require documentation of impact, stakeholder approval, and migration plan for existing code. All implementation plans and code reviews MUST verify constitutional compliance.

Complexity deviations from these principles MUST be explicitly justified in writing with simpler alternatives documented and rejected rationale provided. Use `.specify/templates/` for development guidance aligned with these principles.

**Version**: 1.0.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20