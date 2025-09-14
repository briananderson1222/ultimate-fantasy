# Quickstart: Backend Modularization

## Overview
This guide validates that the backend modularization maintains all existing functionality while establishing clear domain boundaries.

## Prerequisites
- Python 3.11+
- FastAPI development environment
- Existing database with current schema
- pytest test framework

## Quick Validation Steps

### 1. Domain Structure Validation
```bash
# Verify new domain structure exists
ls backend/src/domains/
# Expected: leagues/ users/ lineups/ trading/ scoring/ waitlist/ shared/

# Verify each domain has required structure
for domain in leagues users lineups trading scoring waitlist; do
    ls backend/src/domains/$domain/
    # Expected: api/ models/ services/ schemas/
done
```

### 2. API Functionality Test
```bash
# Run existing API tests to ensure no regression
cd backend && python -m pytest tests/api/ -v

# Test each domain's endpoints independently
python -m pytest tests/api/test_leagues* -v
python -m pytest tests/api/test_lineups* -v
python -m pytest tests/api/test_waivers* -v
python -m pytest tests/api/test_scoreboard* -v
```

### 3. Domain Interface Validation
```bash
# Run contract tests for domain interfaces
python -m pytest tests/contracts/ -v

# Test cross-domain communication
python -m pytest tests/integration/test_domain_boundaries.py -v
```

### 4. Database Migration Validation
```bash
# Verify database schema integrity
python -c "from backend.src.database import engine; engine.connect()"

# Run database validation tests
python -m pytest tests/database/test_domain_isolation.py -v
```

### 5. Performance Baseline Validation
```bash
# Run performance tests to establish baseline
python -m pytest tests/performance/ --benchmark-only -v

# Compare with pre-modularization benchmarks
python scripts/compare_performance.py
```

## User Story Validation

### Story 1: Domain Independence
**Given** the modularized structure exists
**When** running domain-specific tests in isolation
**Then** each domain operates without external dependencies

```bash
# Test leagues domain in isolation
PYTHONPATH=backend/src python -m pytest backend/tests/domains/leagues/ -v

# Test users domain in isolation
PYTHONPATH=backend/src python -m pytest backend/tests/domains/users/ -v
```

### Story 2: Cross-Domain Communication
**Given** domains are separated
**When** one domain needs data from another
**Then** communication happens through defined interfaces

```bash
# Test league service requesting user data
python -m pytest tests/integration/test_league_user_interface.py -v

# Test lineup service requesting league data
python -m pytest tests/integration/test_lineup_league_interface.py -v
```

### Story 3: Backward Compatibility
**Given** the modularized backend
**When** existing API clients make requests
**Then** all responses match previous behavior

```bash
# Run full API regression test suite
python -m pytest tests/regression/ -v

# Test specific API contracts
python scripts/validate_api_contracts.py
```

### Story 4: Independent Development
**Given** separate domain modules
**When** developers modify different domains simultaneously
**Then** no conflicts or interference occurs

```bash
# Simulate parallel development with test branches
git checkout -b test-leagues-feature
git checkout -b test-users-feature

# Run parallel test suites
python scripts/test_parallel_development.py
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Check domain module imports
python -c "from backend.src.domains.leagues import api"
python -c "from backend.src.domains.users import services"
```

**Database Connection Issues**
```bash
# Verify domain-specific database sessions
python scripts/test_domain_db_sessions.py
```

**Cross-Domain Interface Failures**
```bash
# Debug interface communication
python scripts/debug_domain_interfaces.py
```

## Success Criteria Checklist

- [ ] All existing API endpoints respond correctly
- [ ] All existing tests pass without modification
- [ ] Domain modules can be tested independently
- [ ] Cross-domain interfaces work as specified
- [ ] Performance meets or exceeds baseline metrics
- [ ] Database integrity maintained throughout
- [ ] No circular dependencies between domains
- [ ] Event-driven communication functions correctly

## Next Steps

After successful quickstart validation:

1. **Phase 2**: Implement interface contracts and event system
2. **Phase 3**: Database schema isolation
3. **Phase 4**: Microservice readiness preparation

## Rollback Procedure

If validation fails:
```bash
# Return to previous working state
git checkout [previous-commit]

# Restore database if needed
python scripts/restore_database.py

# Verify system functionality
python -m pytest tests/smoke_test.py
```

## Support

For issues during validation:
- Check logs: `backend/logs/modularization.log`
- Review domain interface contracts in `/contracts/`
- Consult troubleshooting guide in project documentation