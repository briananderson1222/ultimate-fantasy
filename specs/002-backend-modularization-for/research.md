# Research: Backend Modularization for Future Microservices

## Performance Benchmarks Research

**Decision**: Establish baseline performance metrics before modularization
**Rationale**: Need measurable criteria to ensure no performance regression during restructuring
**Alternatives considered**: Skip benchmarking and rely on user feedback - rejected due to lack of objectivity

### Current Performance Analysis Needed:
- API response times (95th percentile)
- Database query performance
- Memory usage patterns
- Concurrent request handling capacity

### Recommended Approach:
- Use FastAPI's built-in performance monitoring
- Implement performance tests using pytest-benchmark
- Monitor database connection pooling efficiency
- Track memory usage with domain separation

## Cross-Domain Foreign Key Strategy Research

**Decision**: Implement domain boundaries with eventual consistency approach
**Rationale**: Maintains data integrity while enabling future microservice extraction
**Alternatives considered**:
- Hard foreign keys across domains - rejected (prevents microservice separation)
- Immediate denormalization - rejected (too risky for initial phase)

### Strategy Components:
1. **Phase 1**: Keep existing foreign keys but add domain service interfaces
2. **Phase 2**: Replace direct foreign key references with domain service calls
3. **Phase 3**: Implement event-driven updates for cross-domain data consistency
4. **Phase 4**: Add saga pattern for complex cross-domain transactions

### Domain Relationship Mapping:
- **Leagues ↔ Users**: League membership, ownership
- **Lineups ↔ Leagues**: Lineup belongs to league
- **Lineups ↔ Users**: User owns lineup
- **Trading ↔ Users**: User initiates trades
- **Trading ↔ Leagues**: Trades within league context
- **Scoring ↔ Lineups**: Scores calculated for lineups
- **Scoring ↔ Leagues**: Scores aggregated by league
- **Waitlist ↔ Leagues**: Waitlist for league joining

## Domain Interface Patterns Research

**Decision**: Use Abstract Base Classes (ABCs) with dependency injection
**Rationale**: Provides strong typing and clear contracts while maintaining testability
**Alternatives considered**:
- Duck typing - rejected (lacks explicit contracts)
- Protocol classes - considered but ABCs provide better inheritance structure

### Interface Pattern:
```python
# Example structure (not implementation)
from abc import ABC, abstractmethod

class LeagueServiceInterface(ABC):
    @abstractmethod
    async def get_league_members(self, league_id: str) -> List[User]:
        pass

    @abstractmethod
    async def validate_league_access(self, league_id: str, user_id: str) -> bool:
        pass
```

## Database Schema Isolation Strategy

**Decision**: Gradual schema separation with shared database initially
**Rationale**: Minimizes risk while preparing for future database splitting
**Alternatives considered**:
- Immediate database splitting - rejected (too risky, complex transaction management)
- Keep single schema forever - rejected (doesn't enable microservices)

### Isolation Approach:
1. **Phase 1**: Logical separation with domain-specific table prefixes
2. **Phase 2**: Domain-specific database sessions/connections
3. **Phase 3**: Schema validation to prevent cross-domain queries
4. **Phase 4**: Separate database instances with data synchronization

## Testing Strategy for Domain Boundaries

**Decision**: Contract testing with real database interactions
**Rationale**: Ensures domain interfaces work correctly and catch integration issues early
**Alternatives considered**:
- Mock everything - rejected (doesn't catch real integration issues)
- Only end-to-end tests - rejected (too slow for development cycle)

### Testing Levels:
1. **Contract Tests**: Verify domain interface compliance
2. **Integration Tests**: Test cross-domain interactions
3. **Domain Tests**: Test internal domain logic in isolation
4. **System Tests**: Full API workflow validation

## Migration Strategy Research

**Decision**: Blue-green deployment approach with feature flags
**Rationale**: Enables safe rollback and gradual migration
**Alternatives considered**:
- Big bang migration - rejected (too risky)
- Strangler fig pattern - considered but feature flags provide better control

### Migration Steps:
1. Feature flags for domain routing
2. Parallel running of old and new domain code
3. Gradual traffic shifting to new domains
4. Monitoring and rollback capabilities
5. Complete cutover after validation

## Configuration Management

**Decision**: Domain-specific configuration with inheritance from global config
**Rationale**: Enables independent domain configuration while maintaining consistency
**Alternatives considered**:
- Single global config - rejected (doesn't support domain independence)
- Completely separate configs - rejected (too much duplication)

### Configuration Structure:
- Global configuration for shared infrastructure
- Domain-specific overrides for specialized needs
- Environment-specific variations
- Configuration validation per domain

All NEEDS CLARIFICATION items from Technical Context have been researched and resolved with specific implementation strategies.