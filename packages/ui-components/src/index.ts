// UI Components Package - Main Exports

// Models
export * from './models/UIComponent';
export * from './models/DesignToken';

// Platform Adapters
export * from './adapters/platform';

// Design Tokens
export * from './tokens/design-tokens';
export * from './tokens/fantasy-theme';

// Theme Provider
export * from './providers/ThemeProvider';

// Primitive Components
export * from './primitives/Button';
export * from './primitives/Card';
export * from './primitives/Input';
export * from './primitives/Modal';

// Fantasy Sports Components
export * from './components/PlayerCard';
export * from './components/LeagueCard';
export * from './components/ScoreCard';
export * from './components/DraftBoard';

// Re-export types for convenience
export type {
  Platform,
  PlatformAdapter,
  StyleAdapter,
  NavigationAdapter
} from './adapters/platform';

export type {
  DesignTokenData,
  TokenCategory,
  ColorValue,
  SpacingValue,
  TypographyValue,
  ShadowValue
} from './models/DesignToken';