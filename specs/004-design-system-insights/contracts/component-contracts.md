# Component Contracts

**Date**: 2025-09-14
**Phase**: 1 - Component API Definitions

## Component API Contracts

### MatchCard Component

**Purpose**: Display team matchup with win probabilities and scores

**Props Interface**:
```typescript
interface MatchCardProps {
  matchData: {
    matchId: string;
    homeTeam: TeamInfo;
    awayTeam: TeamInfo;
    projectedScore: { home: number; away: number };
    winProbability: number; // 0-100
    startTime: Date;
    status: "scheduled" | "live" | "completed";
  };
  onTeamClick?: (teamId: string) => void;
  variant?: "default" | "compact";
  className?: string;
}
```

**Required Features**:
- Team avatars and names
- Win percentage progress bar
- Projected scores
- Game status indicator
- Responsive layout

**Accessibility**:
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast color compliance

---

### PlayerCard Component

**Purpose**: Display player information with roster percentages and actions

**Props Interface**:
```typescript
interface PlayerCardProps {
  playerData: {
    playerId: string;
    name: string;
    position: Position;
    team: string;
    rosteredPercent: number; // 0-100
    startPercent: number; // 0-100
    projectedPoints: number;
    trendIndicator?: TrendData;
    status: PlayerStatus;
  };
  actions?: {
    onAddToRoster?: () => void;
    onTrade?: () => void;
    onWaiver?: () => void;
  };
  showActions?: boolean;
  variant?: "default" | "compact" | "minimal";
  className?: string;
}
```

**Required Features**:
- Position badge styling
- Roster/start percentage bars
- Trend indicators with direction
- Action buttons (contextual)
- Player status indicators

---

### SettingsGrid Component

**Purpose**: Display league settings in card-based layout

**Props Interface**:
```typescript
interface SettingsGridProps {
  settings: SettingCard[];
  onSettingClick: (settingId: string) => void;
  columns?: number; // responsive grid columns
  gap?: "sm" | "md" | "lg";
  className?: string;
}

interface SettingCard {
  settingId: string;
  title: string;
  description: string;
  icon: string;
  category: "scoring" | "roster" | "trade" | "waiver";
  enabled?: boolean;
}
```

**Required Features**:
- Responsive grid layout
- Icon display with consistent sizing
- Hover/focus states
- Category-based styling
- Disabled state support

---

### TrendingPlayers Component

**Purpose**: Player discovery interface with filtering and trends

**Props Interface**:
```typescript
interface TrendingPlayersProps {
  players: PlayerCardData[];
  onPlayerSelect: (playerId: string) => void;
  onFilterChange: (position: Position | "all") => void;
  currentFilter: Position | "all";
  loading?: boolean;
  onLoadMore?: () => void;
  className?: string;
}
```

**Required Features**:
- Position filter tabs
- Infinite scroll or pagination
- Loading states
- Empty state handling
- Search functionality

---

### LeagueChat Component

**Purpose**: Real-time chat with transaction notifications

**Props Interface**:
```typescript
interface LeagueChatProps {
  messages: ChatMessage[];
  currentUserId: string;
  onSendMessage: (content: string) => void;
  onLoadHistory?: () => void;
  disabled?: boolean;
  className?: string;
}

interface ChatMessage {
  messageId: string;
  userId: string;
  userName: string;
  userAvatar: string;
  content: string;
  timestamp: Date;
  type: "user_message" | "transaction_notification";
  transactionData?: TransactionInfo;
}
```

**Required Features**:
- Message bubbles with timestamps
- Transaction notification styling
- Input field with emoji support
- Auto-scroll to new messages
- Message history loading

---

### ProgressBar Component

**Purpose**: Visual representation of percentages and probabilities

**Props Interface**:
```typescript
interface ProgressBarProps {
  value: number; // 0-100
  max?: number; // default 100
  variant?: "default" | "success" | "warning" | "danger";
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  label?: string;
  animated?: boolean;
  className?: string;
}
```

**Required Features**:
- Smooth animation on value changes
- Color variants based on value ranges
- Accessibility with proper ARIA attributes
- Responsive sizing

---

### ThemeProvider Component

**Purpose**: Theme management and switching

**Props Interface**:
```typescript
interface ThemeProviderProps {
  children: React.ReactNode;
  initialTheme?: "light" | "dark";
  enableSystemTheme?: boolean;
}

interface ThemeContextValue {
  theme: "light" | "dark";
  setTheme: (theme: "light" | "dark") => void;
  systemTheme: "light" | "dark";
  tokens: ThemeTokens;
}
```

**Required Features**:
- System theme detection
- Smooth theme transitions
- Persistent theme storage
- CSS custom property updates

## Contract Testing Requirements

### Visual Regression Tests
- Component renders correctly with sample data
- Theme switching maintains layout
- Responsive breakpoint behavior
- Accessibility compliance

### Interaction Tests
- Button clicks trigger correct callbacks
- Form inputs update internal state
- Keyboard navigation works properly
- Loading states display correctly

### Error Handling Tests
- Invalid props display fallback content
- Network failures show error states
- Missing data shows empty states
- Malformed data doesn't break components

## Integration Points

### Design Tokens
All components must use centralized design tokens:
- Colors from theme provider
- Typography scale from token system
- Spacing from consistent scale
- Border radius from token definitions

### Animation System
Consistent animation patterns:
- Enter/exit transitions
- Hover/focus state changes
- Loading state animations
- Page transition coordination

### Data Flow
Component communication patterns:
- Props down, events up
- Context for shared state
- Custom hooks for complex logic
- Event emission for cross-component communication