// Shared Logic Package - Main Exports

// Models
export * from './models/SharedPackage';
export * from './models/Export';
export * from './models/SharedHook';

// Stores
export * from './store/leagueStore';
export * from './store/userStore';
export * from './store/appStore';

// Hooks
export * from './hooks/useLeagueData';
export * from './hooks/usePlayerStats';

// Utilities
export * from './utils/dashboard';

// State Management
export * from './state/StateManager';

// Validation
export * from './validation/FormValidator';
export * from './validation/league';

// Re-export types for convenience
export type {
  WidgetKey,
  WidgetSizes,
  WidgetSettings,
  StorageAdapter
} from './utils/dashboard';

export type {
  StateStore,
  StateManagerConfig
} from './state/StateManager';

export type {
  ValidationResult,
  FieldValidationResult
} from './validation/FormValidator';

export type {
  League,
  LeagueSettings,
  CreateLeague,
  UpdateLeague,
  DraftSettings,
  ScoringSettings,
  RosterSettings
} from './validation/league';

export type {
  User,
  UserPreferences
} from './store/userStore';

export type {
  PlayerStats,
  PlayerInfo
} from './hooks/usePlayerStats';

export type {
  SharedHookData,
  HookParameter,
  HookReturn
} from './models/SharedHook';