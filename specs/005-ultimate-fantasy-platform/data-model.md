# Data Model: Ultimate Fantasy Platform

**Date**: 2025-09-19
**Feature**: Ultimate Fantasy Platform - Comprehensive Implementation

## Core Entities

### Player
**Purpose**: Real sports athletes with comprehensive statistics and status
**Fields**:
- `player_id`: UUID (primary key)
- `external_id`: String (sports API identifier)
- `name`: String (full player name)
- `position`: String (e.g., "QB", "RB", "WR" for NFL)
- `team_id`: String (current team affiliation)
- `sport`: String (MLB, NFL, WNBA)
- `injury_status`: String (healthy, questionable, doubtful, out)
- `injury_description`: String (optional details)
- `season_stats`: JSON (current season statistics)
- `game_stats`: JSON (recent game performance)
- `projections`: JSON (projected fantasy points)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-many with Team (through roster)
- One-to-many with LineupPlayer
- One-to-many with TradePlayer
- One-to-many with WaiverBid

**Validation Rules**:
- Position must be valid for sport
- Injury status must be from enum
- External ID must be unique per sport
- Stats must be valid JSON schema

### League
**Purpose**: User-created fantasy leagues with custom rules and settings
**Fields**:
- `league_id`: UUID (primary key)
- `name`: String (league name, max 200 chars)
- `sport`: String (MLB, NFL, WNBA)
- `league_type`: String (head_to_head, rotisserie)
- `season`: String (e.g., "2025")
- `commissioner_id`: UUID (foreign key to User)
- `max_teams`: Integer (default 12)
- `scoring_rules`: JSON (points per stat)
- `roster_settings`: JSON (position requirements)
- `draft_settings`: JSON (draft type, date, order)
- `waiver_settings`: JSON (processing schedule, budget)
- `trade_settings`: JSON (deadline, veto rules)
- `playoff_settings`: JSON (teams, weeks, format)
- `status`: String (setup, drafting, active, completed)
- `invite_code`: String (unique league identifier)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with User (commissioner)
- One-to-many with Team
- One-to-many with Draft
- One-to-many with Trade
- One-to-many with WaiverPeriod
- One-to-many with ChatMessage
- One-to-many with Achievement

**Validation Rules**:
- Max teams between 2-20
- Sport must be supported
- Commissioner must be league member
- Scoring rules must be valid JSON schema

**State Transitions**:
- setup → drafting (when draft starts)
- drafting → active (when draft completes)
- active → completed (when season ends)

### Team
**Purpose**: Individual user teams within leagues
**Fields**:
- `team_id`: UUID (primary key)
- `league_id`: UUID (foreign key)
- `user_id`: UUID (foreign key)
- `name`: String (team name)
- `logo_url`: String (optional team logo)
- `wins`: Integer (season wins)
- `losses`: Integer (season losses)
- `ties`: Integer (season ties)
- `points_for`: Float (total points scored)
- `points_against`: Float (total points allowed)
- `waiver_priority`: Integer (waiver claim order)
- `faab_budget`: Integer (remaining auction budget)
- `roster`: JSON (array of player_ids)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with League
- Many-to-one with User
- One-to-many with Lineup
- Many-to-many with Trade
- One-to-many with WaiverBid

**Validation Rules**:
- Team name unique within league
- Roster size within league limits
- Budget must be non-negative
- User can only have one team per league

### Lineup
**Purpose**: Daily/weekly player selections for scoring
**Fields**:
- `lineup_id`: UUID (primary key)
- `team_id`: UUID (foreign key)
- `week`: Integer (scoring period)
- `game_day`: Date (specific day for daily sports)
- `players`: JSON (array of {player_id, position})
- `points_scored`: Float (calculated total points)
- `is_locked`: Boolean (cannot be modified)
- `version`: Integer (optimistic locking)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with Team
- References Players through JSON array

**Validation Rules**:
- Players must be on team roster
- Position requirements met
- Cannot modify when locked
- Version increments on each update

### Draft
**Purpose**: Structured player selection process
**Fields**:
- `draft_id`: UUID (primary key)
- `league_id`: UUID (foreign key)
- `draft_type`: String (snake, auction, linear)
- `status`: String (scheduled, active, paused, completed)
- `current_pick`: Integer (pick number in progress)
- `current_team_id`: UUID (team with current pick)
- `picks`: JSON (array of completed picks)
- `pick_timer`: Integer (seconds per pick)
- `started_at`: Timestamp
- `completed_at`: Timestamp
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with League
- One-to-many with DraftPick

**Validation Rules**:
- Draft type must be supported
- Pick timer reasonable (30-300 seconds)
- Cannot restart completed draft
- All league teams must participate

**State Transitions**:
- scheduled → active (manual start)
- active → paused (manual pause)
- paused → active (resume)
- active → completed (all picks made)

### Trade
**Purpose**: Player exchange proposals between teams
**Fields**:
- `trade_id`: UUID (primary key)
- `league_id`: UUID (foreign key)
- `proposing_team_id`: UUID (foreign key)
- `receiving_team_id`: UUID (foreign key)
- `proposed_players`: JSON (array from proposing team)
- `requested_players`: JSON (array from receiving team)
- `status`: String (pending, accepted, rejected, expired)
- `message`: String (optional trade note)
- `evaluation_score`: Float (fairness analysis)
- `expires_at`: Timestamp
- `processed_at`: Timestamp
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with League
- Many-to-one with Team (proposing)
- Many-to-one with Team (receiving)

**Validation Rules**:
- Cannot trade with self
- Players must be owned by correct teams
- Trade deadline enforcement
- Reasonable evaluation score

**State Transitions**:
- pending → accepted (receiving team accepts)
- pending → rejected (receiving team rejects)
- pending → expired (timeout)

### WaiverBid
**Purpose**: Free agent acquisition system
**Fields**:
- `waiver_id`: UUID (primary key)
- `league_id`: UUID (foreign key)
- `team_id`: UUID (foreign key)
- `player_id`: UUID (foreign key)
- `bid_amount`: Integer (FAAB bid)
- `drop_player_id`: UUID (player to release)
- `priority`: Integer (waiver priority when tied)
- `status`: String (pending, won, lost, expired)
- `processed_at`: Timestamp
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with League
- Many-to-one with Team
- Many-to-one with Player (add)
- Many-to-one with Player (drop)

**Validation Rules**:
- Bid amount within team budget
- Drop player must be owned
- Add player must be available
- Cannot bid on owned player

### Score
**Purpose**: Calculated points based on real performance
**Fields**:
- `score_id`: UUID (primary key)
- `player_id`: UUID (foreign key)
- `league_id`: UUID (foreign key)
- `week`: Integer (scoring period)
- `game_day`: Date (specific day)
- `stats`: JSON (raw statistics)
- `points`: Float (calculated fantasy points)
- `breakdown`: JSON (points per stat category)
- `is_final`: Boolean (official/projected)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Relationships**:
- Many-to-one with Player
- Many-to-one with League

**Validation Rules**:
- Points must match breakdown calculation
- Stats must be valid for sport
- Cannot modify final scores
- Week/day within league season

### Notification
**Purpose**: Real-time alerts for user actions
**Fields**:
- `notification_id`: UUID (primary key)
- `user_id`: UUID (foreign key)
- `league_id`: UUID (foreign key, optional)
- `type`: String (draft_pick, trade_offer, waiver_result)
- `title`: String (notification headline)
- `message`: String (detailed content)
- `data`: JSON (additional context)
- `read_at`: Timestamp (null if unread)
- `expires_at`: Timestamp
- `created_at`: Timestamp

**Relationships**:
- Many-to-one with User
- Many-to-one with League (optional)

**Validation Rules**:
- Type must be from enum
- Message length limits
- Reasonable expiration time

### ChatMessage
**Purpose**: Communication between league members
**Fields**:
- `message_id`: UUID (primary key)
- `league_id`: UUID (foreign key)
- `user_id`: UUID (foreign key)
- `content`: String (message text)
- `type`: String (text, image, system)
- `moderation_status`: String (approved, flagged, removed)
- `reply_to_id`: UUID (optional reply reference)
- `edited_at`: Timestamp (last edit time)
- `created_at`: Timestamp

**Relationships**:
- Many-to-one with League
- Many-to-one with User
- Self-referential (replies)

**Validation Rules**:
- Content length limits (500 chars)
- Moderation status from enum
- Cannot edit system messages

### Achievement
**Purpose**: Gamification elements for engagement
**Fields**:
- `achievement_id`: UUID (primary key)
- `user_id`: UUID (foreign key)
- `league_id`: UUID (foreign key, optional)
- `type`: String (first_win, perfect_week, trade_master)
- `name`: String (achievement title)
- `description`: String (achievement details)
- `icon_url`: String (badge image)
- `earned_at`: Timestamp
- `season`: String (when earned)

**Relationships**:
- Many-to-one with User
- Many-to-one with League (optional)

**Validation Rules**:
- Type must be from predefined list
- Cannot duplicate achievements
- Valid season format

## Aggregate Relationships

### User-League Ecosystem
- User → Team → Lineup (ownership chain)
- League → Draft → Picks (draft process)
- League → Trade → Teams (multi-team transactions)
- League → WaiverPeriod → Bids (waiver processing)

### Real-time Data Flow
- External APIs → Player (stats updates)
- Player → Score → Lineup (point calculation)
- Draft → Pick → Roster (player acquisition)
- Trade → Roster Updates (player movement)

### Analytics Aggregations
- League → Team Performance (standings)
- User → Cross-League Stats (overall performance)
- Player → Usage Rates (popularity metrics)
- Trade → Market Values (player valuations)

## Schema Evolution

### Migration Strategy
- Backward-compatible JSON field additions
- Versioned API contracts during schema changes
- Parallel table approach for major restructuring
- Zero-downtime deployment patterns

### Performance Optimization
- Indexes on frequently queried fields
- Partial indexes for status-based queries
- Composite indexes for multi-field filters
- Archive strategy for historical data

This data model supports all 35 functional requirements while maintaining referential integrity and performance characteristics suitable for real-time fantasy sports operations.