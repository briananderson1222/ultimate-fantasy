// Shared Logic Package - Main Exports

// Models
export * from './models/SharedPackage';
export * from './models/Export';
export * from './models/SharedHook';

// Stores are intentionally NOT re-exported from the root to avoid
// pulling Zustand into bundles that only need utilities/hooks.
// Import them via subpaths, e.g. `@ultimate-fantasy/shared-logic/store/userStore`.

// Hooks are not re-exported from the root to keep the root import lightweight.
// Import hooks via subpaths (e.g., `@ultimate-fantasy/shared-logic/hooks/usePlayerStats`).

// Utilities
export * from './utils/dashboard';
export * from './utils/fantasy';

// State Management
export * from './state/StateManager';

// Validation
export * from './validation/league';
export * from './validation/fantasy';

// Re-export types for convenience
export type { WidgetKey, WidgetSizes, WidgetSettings, StorageAdapter } from './utils/dashboard';

export type { StateStore, StateManagerConfig } from './state/StateManager';

export type {
  League,
  LeagueSettings,
  CreateLeague,
  UpdateLeague,
  DraftSettings,
  ScoringSettings,
  RosterSettings,
} from './validation/league';

export type {
  ValidationResult as FantasyValidationResult,
  PlayerValidation,
  LineupValidation,
  TradeValidation,
} from './validation/fantasy';

export type { Player, TeamStats } from './utils/fantasy';

// Store types are not re-exported from the root to prevent importing store modules.

export type { PlayerStats, PlayerInfo } from './hooks/usePlayerStats';

export type { SharedHookData, HookParameter, HookReturn } from './models/SharedHook';
