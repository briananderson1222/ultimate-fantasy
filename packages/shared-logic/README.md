# @ultimate-fantasy/shared-logic

Shared business logic, utilities, and state management for the Ultimate Fantasy platform. This package provides cross-platform functionality that works seamlessly between NextJS web applications and React Native mobile apps.

## Features

- 🔄 **Cross-Platform State Management** - Zustand stores with persistence
- 🎯 **Business Logic Utilities** - Dashboard management, data processing
- 🔧 **React Hooks** - Reusable hooks for data fetching and state management
- ✅ **Validation Schemas** - Zod-based form and data validation
- 📱 **Platform Adapters** - Automatic web/mobile environment detection
- 💾 **Storage Abstraction** - localStorage ↔ AsyncStorage compatibility

## Installation

```bash
npm install @ultimate-fantasy/shared-logic
```

## Core Modules

### State Management

Zustand-based stores for managing application state:

```typescript
import { useLeagueStore, useUserStore, useAppStore } from '@ultimate-fantasy/shared-logic';

// League management
const { leagues, selectedLeague, setLeagues } = useLeagueStore();

// User authentication and preferences
const { user, preferences, setUser } = useUserStore();

// Application-wide state
const { settings, connection, navigation } = useAppStore();
```

### Hooks

Reusable React hooks for common functionality:

```typescript
import { useLeagueData, usePlayerStats } from '@ultimate-fantasy/shared-logic';

// League data management
const { leagues, isLoading, refetch } = useLeagueData({
  autoFetch: true,
  refetchInterval: 30000
});

// Player statistics
const { stats, playerInfo, getTopPerformers } = usePlayerStats({
  week: 1,
  season: '2025'
});
```

### Utilities

Cross-platform utility functions:

```typescript
import { dashboardUtils } from '@ultimate-fantasy/shared-logic';

// Dashboard widget management
const widgets = dashboardUtils.loadLayout();
dashboardUtils.saveLayout(['myLeagues', 'upcoming', 'scoreboard']);

// Platform detection
const isNative = dashboardUtils.isNativePlatform();
const storage = dashboardUtils.getStorageAdapter();
```

### Validation

Zod schemas for form and data validation:

```typescript
import { leagueValidation } from '@ultimate-fantasy/shared-logic';

// Validate league data
const league = leagueValidation.validateCreateLeague({
  name: 'My League',
  total_rosters: 12,
  settings: {
    scoring: { scoring_type: 'ppr' },
    roster: { roster_positions: ['QB', 'RB', 'WR'] }
  }
});

// League filtering
const filters = leagueValidation.validateLeagueFilter({
  status: ['active', 'drafting'],
  total_rosters: { min: 8, max: 14 }
});
```

## API Reference

### State Stores

#### useLeagueStore()

Manages league data and selection state.

**State:**
- `leagues: League[]` - Array of user's leagues
- `selectedLeague: League | null` - Currently selected league
- `isLoading: boolean` - Loading state
- `error: string | null` - Error message

**Actions:**
- `setLeagues(leagues: League[])` - Set leagues array
- `setSelectedLeague(league: League | null)` - Select a league
- `addLeague(league: League)` - Add new league
- `updateLeague(id: string, updates: Partial<League>)` - Update league
- `removeLeague(id: string)` - Remove league

#### useUserStore()

Manages user authentication and preferences.

**State:**
- `user: User | null` - Current user data
- `preferences: UserPreferences` - User preferences
- `isAuthenticated: boolean` - Authentication status
- `isLoading: boolean` - Loading state
- `error: string | null` - Error message

**Actions:**
- `setUser(user: User | null)` - Set user data
- `updateUser(updates: Partial<User>)` - Update user
- `setPreferences(prefs: Partial<UserPreferences>)` - Update preferences
- `logout()` - Clear user session

#### useAppStore()

Manages application-wide state.

**State:**
- `settings: AppSettings` - App configuration
- `connection: ConnectionState` - Network status
- `navigation: NavigationState` - Navigation history
- `notifications: Notification[]` - In-app notifications

**Actions:**
- `setSettings(settings: Partial<AppSettings>)` - Update settings
- `setOnlineStatus(isOnline: boolean)` - Update connectivity
- `addNotification(notification)` - Add notification
- `navigateTo(route: string)` - Track navigation

### Hooks

#### useLeagueData(options?)

Hook for managing league data with automatic fetching and caching.

**Parameters:**
- `options.autoFetch?: boolean` - Auto-fetch on mount (default: true)
- `options.refetchInterval?: number` - Refetch interval in ms
- `options.onError?: (error: Error) => void` - Error callback
- `options.onSuccess?: (leagues: League[]) => void` - Success callback

**Returns:**
- `leagues: League[]` - Leagues array
- `selectedLeague: League | null` - Selected league
- `isLoading: boolean` - Loading state
- `error: string | null` - Error state
- `refetch: () => Promise<void>` - Manual refetch
- `selectLeague: (id: string | null) => void` - Select league
- `updateLeague: (id: string, updates: Partial<League>) => void` - Update league

#### usePlayerStats(options?)

Hook for fetching and managing player statistics.

**Parameters:**
- `options.week?: number` - Target week
- `options.season?: string` - Target season
- `options.position?: string` - Filter by position
- `options.team?: string` - Filter by team

**Returns:**
- `stats: PlayerStats[]` - Player statistics
- `playerInfo: Record<string, PlayerInfo>` - Player information
- `isLoading: boolean` - Loading state
- `error: string | null` - Error state
- `getPlayerStats: (id: string) => PlayerStats | null` - Get specific player
- `filterByPosition: (position: string) => PlayerStats[]` - Filter by position
- `sortByFantasyPoints: (ppr?: boolean) => PlayerStats[]` - Sort by points

### Validation Schemas

#### League Validation

```typescript
import { leagueValidation, type League, type CreateLeague } from '@ultimate-fantasy/shared-logic';

// Validate league creation
const league: CreateLeague = leagueValidation.validateCreateLeague(data);

// Validate league updates
const updates = leagueValidation.validateUpdateLeague(data);

// Validate league filters
const filters = leagueValidation.validateLeagueFilter(data);

// Get default settings
const defaultSettings = leagueValidation.getDefaultSettings('ppr');
```

#### Available Schemas

- `LeagueSchema` - Complete league data validation
- `CreateLeagueSchema` - League creation validation
- `UpdateLeagueSchema` - League update validation
- `LeagueFilterSchema` - League search/filter validation
- `DraftSettingsSchema` - Draft configuration validation
- `ScoringSettingsSchema` - Scoring rules validation
- `RosterSettingsSchema` - Roster configuration validation

### Models

#### SharedPackage

Model for representing shared package metadata.

```typescript
import { SharedPackage } from '@ultimate-fantasy/shared-logic';

const pkg = new SharedPackage({
  name: '@ultimate-fantasy/shared-logic',
  version: '1.0.0',
  platform: 'universal',
  dependencies: ['react', 'zustand'],
  exports: [
    {
      name: 'useLeagueStore',
      type: 'hook',
      signature: '() => LeagueStore',
      platform: 'universal',
      deprecated: false
    }
  ]
});
```

#### SharedHook

Model for representing React hook contracts.

```typescript
import { SharedHook } from '@ultimate-fantasy/shared-logic';

const hook = SharedHook.create('useLeagueData', 'Hook for managing league data')
  .withCategory('api')
  .addParameter('options', 'LeagueDataOptions', { optional: true })
  .withReturnType('LeagueDataReturn', 'League data and actions')
  .addExample('const { leagues, isLoading } = useLeagueData();')
  .build();
```

## Platform Compatibility

This package is designed to work seamlessly across platforms:

### Web (NextJS)
- Uses `localStorage` for persistence
- Full DOM API access
- Web-specific optimizations

### Mobile (React Native)
- Uses `AsyncStorage` for persistence
- React Native API compatibility
- Touch-optimized interactions

### Automatic Detection

The package automatically detects the platform and adapts accordingly:

```typescript
import { dashboardUtils } from '@ultimate-fantasy/shared-logic';

// Automatically uses correct storage adapter
const storage = dashboardUtils.getStorageAdapter();
// Web: localStorage, Mobile: AsyncStorage

// Platform detection
const isNative = dashboardUtils.isNativePlatform();
// Web: false, Mobile: true
```

## Development

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

### Type Checking

```bash
npm run typecheck
```

## Dependencies

### Peer Dependencies

- `react` ^18.0.0
- `zustand` ^4.0.0
- `zod` ^3.0.0

### Platform-Specific Dependencies

- **Web**: None (uses browser APIs)
- **Mobile**: `@react-native-async-storage/async-storage`

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure cross-platform compatibility

## License

MIT