# Data Model: Backend Modularization

## Domain Entities

### Leagues Domain
- **League**: Core league entity with settings, rules, commissioner
- **Team**: Team within a league, owned by a user
- **LeagueMembership**: User participation in league with role/status
- **LeagueSettings**: Configuration and rules for league operation

### Users Domain
- **User**: Core user entity with authentication and profile
- **UserPreference**: User-specific settings and preferences
- **UserProfile**: Extended user information and statistics

### Lineups Domain
- **Lineup**: User's team lineup for a specific time period
- **LineupSlot**: Individual player slot within a lineup
- **LineupHistory**: Historical lineup changes and timestamps

### Trading Domain
- **Waiver**: Waiver wire transaction request
- **WaiverClaim**: User claim on waiver wire player
- **Trade**: Trade transaction between users
- **Transaction**: Generic transaction record

### Scoring Domain
- **Score**: Calculated scores for lineups/players
- **ScoringRule**: Rules for how points are calculated
- **PlayerPerformance**: Individual player performance data
- **ScoreAudit**: Historical scoring calculations and changes

### Waitlist Domain
- **WaitlistEntry**: User waiting to join a league
- **WaitlistInvite**: Invitation to join from waitlist

## Domain Relationships

### Cross-Domain Dependencies
- **Leagues → Users**: League membership and ownership
- **Lineups → Leagues**: Lineups belong to leagues
- **Lineups → Users**: Users own lineups
- **Trading → Users**: Users initiate trades/waivers
- **Trading → Leagues**: Trades occur within league context
- **Scoring → Lineups**: Scores calculated for lineups
- **Scoring → Leagues**: Scoring rules defined by league
- **Waitlist → Leagues**: Waitlist for specific leagues
- **Waitlist → Users**: Users on waitlist

### Interface Contracts
Each domain exposes specific interfaces for cross-domain communication:

#### League Service Interface
- `get_league_members(league_id) -> List[User]`
- `validate_league_access(league_id, user_id) -> bool`
- `get_league_settings(league_id) -> LeagueSettings`

#### User Service Interface
- `get_user(user_id) -> User`
- `validate_user_permissions(user_id, resource) -> bool`
- `get_user_preferences(user_id) -> UserPreferences`

#### Lineup Service Interface
- `get_lineup(lineup_id) -> Lineup`
- `validate_lineup_ownership(lineup_id, user_id) -> bool`
- `get_lineup_by_user_league(user_id, league_id) -> Lineup`

#### Trading Service Interface
- `validate_trade_eligibility(user_id, league_id) -> bool`
- `process_waiver_claim(waiver_id, user_id) -> Transaction`
- `get_active_waivers(league_id) -> List[Waiver]`

#### Scoring Service Interface
- `calculate_lineup_score(lineup_id, period) -> Score`
- `get_scoring_rules(league_id) -> ScoringRules`
- `audit_score_calculation(score_id) -> ScoreAudit`

#### Waitlist Service Interface
- `add_to_waitlist(user_id, league_id) -> WaitlistEntry`
- `process_waitlist_invite(invite_id) -> bool`
- `get_waitlist_position(entry_id) -> int`

## Data Consistency Rules

### Eventual Consistency Scenarios
- User changes propagated to all domains containing user references
- League setting changes affecting scoring rules
- Lineup changes triggering score recalculation

### Strong Consistency Requirements
- Financial transactions (trades with monetary value)
- Waiver claim processing (first-come-first-served)
- League membership limits enforcement

### Validation Rules
- Cross-domain referential integrity through service interfaces
- Business rule validation within domain boundaries
- Data synchronization auditing and reconciliation

## Migration Strategy

### Phase 1: Logical Separation
- Maintain existing database schema
- Add domain service interfaces
- Implement cross-domain validation

### Phase 2: Service Integration
- Replace direct database calls with service calls
- Add event publishing for cross-domain updates
- Implement consistency checking

### Phase 3: Schema Isolation
- Separate domain data into logical schemas
- Implement domain-specific database sessions
- Add data synchronization mechanisms

### Phase 4: Database Separation
- Split domains into separate databases
- Implement cross-database transaction handling
- Add data replication for read queries