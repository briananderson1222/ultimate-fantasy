# Data Model: Design System

**Date**: 2025-09-14
**Phase**: 1 - Data Model Definition

## Core Entities

### Theme Configuration
Represents the visual theme system with color schemes, typography, and spacing.

**Fields**:
- `id`: string (theme identifier, e.g., "dark", "light")
- `name`: string (human-readable theme name)
- `colors`: ColorTokens (semantic color definitions)
- `typography`: TypographyTokens (font scales and weights)
- `spacing`: SpacingTokens (consistent spacing scale)
- `shadows`: ShadowTokens (depth and elevation)
- `borderRadius`: BorderRadiusTokens (corner radius values)

**Relationships**:
- Used by all visual components
- Stored in user preferences

**Validation Rules**:
- Theme ID must be unique
- All color tokens must be valid CSS color values
- Typography scale must include base, mobile, and desktop variants

### Color Tokens
Semantic color system for consistent theming.

**Fields**:
- `primary`: string (main accent color, #00e5ff)
- `success`: string (positive actions, #00e676)
- `warning`: string (alerts and warnings, #ffb74d)
- `background`: ColorGradient (main background)
- `surface`: string (card and component backgrounds)
- `textPrimary`: string (main text color)
- `textSecondary`: string (secondary text color)
- `border`: string (component borders)

**State Transitions**:
- Light ↔ Dark theme switching
- Hover/focus state variations

### Match Card Data
Team matchup visualization with performance metrics.

**Fields**:
- `matchId`: string (unique match identifier)
- `homeTeam`: TeamInfo (home team details)
- `awayTeam`: TeamInfo (away team details)
- `projectedScore`: ScoreProjection (predicted scores)
- `winProbability`: number (0-100, win chance percentage)
- `gameStatus`: MatchStatus (scheduled, live, completed)
- `startTime`: Date (game start timestamp)

**Relationships**:
- Contains two TeamInfo entities
- Links to player roster data

**Validation Rules**:
- Win probability must be 0-100
- Start time must be future for scheduled games
- Team IDs must be valid and different

### Team Info
Individual team data for matches and standings.

**Fields**:
- `teamId`: string (unique team identifier)
- `name`: string (team name)
- `avatar`: string (team avatar URL)
- `logo`: string (team logo URL)
- `record`: TeamRecord (wins, losses, ties)
- `ownerName`: string (team owner/manager name)
- `ownerAvatar`: string (owner profile image)

**Validation Rules**:
- Team name must be 3-30 characters
- Avatar/logo URLs must be valid image formats
- Owner name required for league displays

### Player Card Data
Individual player information with performance metrics.

**Fields**:
- `playerId`: string (unique player identifier)
- `name`: string (player full name)
- `position`: Position (QB, RB, WR, TE, DEF, K)
- `team`: string (NFL team abbreviation)
- `rosteredPercent`: number (0-100, roster adoption rate)
- `startPercent`: number (0-100, starting lineup rate)
- `trendIndicator`: TrendData (popularity change)
- `projectedPoints`: number (fantasy point projection)
- `status`: PlayerStatus (active, injured, bye, questionable)

**Relationships**:
- Belongs to NFL team
- Can be on multiple fantasy rosters

**Validation Rules**:
- Position must be valid fantasy position
- Percentages must be 0-100
- Player name required and non-empty

### Trend Data
Player popularity and performance trending information.

**Fields**:
- `direction`: TrendDirection (up, down, neutral)
- `magnitude`: number (change amount, e.g., +416.6K)
- `timeframe`: TrendTimeframe (24h, 7d, season)
- `category`: TrendCategory (roster_adds, start_rate, points)

### League Chat Message
Communication data for league interactions.

**Fields**:
- `messageId`: string (unique message identifier)
- `userId`: string (sender user ID)
- `userName`: string (sender display name)
- `userAvatar`: string (sender profile image)
- `content`: string (message text content)
- `timestamp`: Date (message creation time)
- `type`: MessageType (user_message, transaction_notification)
- `transactionData`: TransactionInfo? (optional transaction details)

**Relationships**:
- Belongs to specific league
- May reference transaction data

**Validation Rules**:
- Content must be non-empty for user messages
- Transaction messages must include transaction data
- Timestamp must be valid date

### Setting Card
Configuration option presentation for league settings.

**Fields**:
- `settingId`: string (unique setting identifier)
- `title`: string (setting display name)
- `description`: string (setting explanation)
- `icon`: string (setting icon identifier)
- `category`: SettingCategory (scoring, roster, trade, waiver)
- `value`: SettingValue (current setting value)
- `options`: SettingOptions? (available choices)

**Validation Rules**:
- Title and description required
- Icon must reference valid icon identifier
- Value must match setting type constraints

## Enums & Types

### Position
```typescript
enum Position {
  QB = "QB",
  RB = "RB",
  WR = "WR",
  TE = "TE",
  DEF = "DEF",
  K = "K"
}
```

### MatchStatus
```typescript
enum MatchStatus {
  SCHEDULED = "scheduled",
  LIVE = "live",
  COMPLETED = "completed"
}
```

### TrendDirection
```typescript
enum TrendDirection {
  UP = "up",
  DOWN = "down",
  NEUTRAL = "neutral"
}
```

### MessageType
```typescript
enum MessageType {
  USER_MESSAGE = "user_message",
  TRANSACTION_NOTIFICATION = "transaction_notification"
}
```

## Composite Types

### ColorGradient
```typescript
interface ColorGradient {
  from: string;
  to: string;
  direction?: string; // "to-b", "to-r", etc.
}
```

### ScoreProjection
```typescript
interface ScoreProjection {
  home: number;
  away: number;
  confidence: number; // 0-100
}
```

### TeamRecord
```typescript
interface TeamRecord {
  wins: number;
  losses: number;
  ties: number;
}
```

## State Management

### Theme State
- Persisted in localStorage
- Applied via CSS custom properties
- Context provider for React components

### Component State
- Form inputs: controlled components with validation
- Modal states: boolean flags with cleanup
- Animation states: Framer Motion variants

### Data Flow
1. User interaction triggers component event
2. Component validates input and updates local state
3. Valid changes propagate to parent components
4. State changes trigger re-renders with new data
5. Visual feedback confirms user action

## Performance Considerations

### Data Loading
- Theme tokens loaded synchronously (critical rendering path)
- Player/team data loaded asynchronously with loading states
- Images lazy-loaded with placeholder states

### State Updates
- Debounced search inputs (300ms delay)
- Optimistic updates for non-critical actions
- Batch state updates for animation frames

### Memory Management
- Component cleanup on unmount
- Event listener removal
- Image preloading for critical assets only