/**
 * Fantasy Sports Design Tokens
 *
 * Comprehensive design system tokens for the Ultimate Fantasy Platform.
 * Provides consistent colors, typography, spacing, and animations across
 * web and mobile applications with fantasy sports-specific theming.
 */

// Core Brand Colors
export const brandColors = {
  // Primary fantasy sports colors
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9', // Main brand color
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
    950: '#082f49',
  },

  // Secondary accent colors
  secondary: {
    50: '#fefce8',
    100: '#fef9c3',
    200: '#fef08a',
    300: '#fde047',
    400: '#facc15',
    500: '#eab308', // Fantasy gold
    600: '#ca8a04',
    700: '#a16207',
    800: '#854d0e',
    900: '#713f12',
    950: '#422006',
  },

  // Success colors (wins, positive stats)
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
    950: '#052e16',
  },

  // Warning colors (injuries, alerts)
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
    950: '#451a03',
  },

  // Error colors (losses, negative stats)
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
    950: '#450a0a',
  },

  // Info colors (neutral information)
  info: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },
} as const;

// Fantasy Sports Specific Colors
export const fantasyColors = {
  // Player status colors
  player: {
    available: brandColors.success[500],
    owned: brandColors.info[400],
    injured: brandColors.error[500],
    questionable: brandColors.warning[500],
    out: brandColors.error[600],
    bye: brandColors.info[300],
    suspended: brandColors.error[700],
  },

  // Position colors
  position: {
    qb: '#8b5cf6',  // Violet
    rb: '#f59e0b',  // Amber
    wr: '#10b981',  // Emerald
    te: '#3b82f6',  // Blue
    k: '#6b7280',   // Gray
    dst: '#1f2937', // Dark gray
    flex: '#8b5cf6', // Purple
    superflex: '#ec4899', // Pink
  },

  // Score impact colors
  scoring: {
    positive: brandColors.success[500],
    negative: brandColors.error[500],
    neutral: brandColors.info[400],
    boom: brandColors.success[600],
    bust: brandColors.error[600],
  },

  // League status colors
  league: {
    active: brandColors.success[500],
    draft: brandColors.warning[500],
    setup: brandColors.info[500],
    completed: brandColors.info[600],
    playoffs: brandColors.secondary[600],
  },

  // Trade and waiver colors
  transaction: {
    proposed: brandColors.warning[400],
    accepted: brandColors.success[500],
    rejected: brandColors.error[500],
    pending: brandColors.info[400],
    expired: brandColors.info[300],
  },
} as const;

// Typography tokens
export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Consolas', 'monospace'],
    display: ['Inter', 'system-ui', 'sans-serif'],
  },

  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
  },

  fontWeight: {
    thin: '100',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
} as const;

// Spacing tokens
export const spacing = {
  0: '0',
  1: '0.25rem',     // 4px
  2: '0.5rem',      // 8px
  3: '0.75rem',     // 12px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  8: '2rem',        // 32px
  10: '2.5rem',     // 40px
  12: '3rem',       // 48px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
} as const;

// Border radius tokens
export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  default: '0.25rem', // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',
} as const;

// Shadow tokens
export const shadows = {
  xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  default: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
} as const;

export interface FantasyTheme {
  name: string;
  colors: typeof fantasyColors;
  brandColors: typeof brandColors;
  spacing: typeof spacing;
  typography: typeof typography;
  borderRadius: typeof borderRadius;
  shadows: typeof shadows;
}

// Complete fantasy theme
export const fantasyTheme: FantasyTheme = {
  name: 'ultimate-fantasy',
  colors: fantasyColors,
  brandColors,
  spacing,
  typography,
  borderRadius,
  shadows,
};

// Dark theme variations
export const darkTheme = {
  background: {
    primary: '#0f172a',
    secondary: '#1e293b',
    tertiary: '#334155',
    elevated: '#475569',
  },

  text: {
    primary: '#f8fafc',
    secondary: '#e2e8f0',
    tertiary: '#cbd5e1',
    muted: '#94a3b8',
  },

  border: {
    default: '#334155',
    light: '#475569',
    heavy: '#64748b',
  },

  surface: {
    default: '#1e293b',
    hover: '#334155',
    pressed: '#475569',
    disabled: '#64748b',
  },
} as const;

// Light theme variations
export const lightTheme = {
  background: {
    primary: '#ffffff',
    secondary: '#f8fafc',
    tertiary: '#f1f5f9',
    elevated: '#ffffff',
  },

  text: {
    primary: '#0f172a',
    secondary: '#334155',
    tertiary: '#64748b',
    muted: '#94a3b8',
  },

  border: {
    default: '#e2e8f0',
    light: '#f1f5f9',
    heavy: '#cbd5e1',
  },

  surface: {
    default: '#ffffff',
    hover: '#f8fafc',
    pressed: '#f1f5f9',
    disabled: '#f8fafc',
  },
} as const;

// Type definitions for TypeScript
export type ThemeMode = 'light' | 'dark';

// Utility functions
export const getThemeColors = (mode: ThemeMode) => {
  return mode === 'dark' ? darkTheme : lightTheme;
};

export const getPositionColor = (position: string): string => {
  const pos = position.toLowerCase();
  return fantasyColors.position[pos as keyof typeof fantasyColors.position] || fantasyColors.position.flex;
};

export const getPlayerStatusColor = (status: string): string => {
  const statusLower = status.toLowerCase();
  return fantasyColors.player[statusLower as keyof typeof fantasyColors.player] || fantasyColors.player.available;
};

export const getScoringColor = (points: number): string => {
  if (points > 20) return fantasyColors.scoring.boom;
  if (points > 0) return fantasyColors.scoring.positive;
  if (points < -5) return fantasyColors.scoring.bust;
  if (points < 0) return fantasyColors.scoring.negative;
  return fantasyColors.scoring.neutral;
};

export default fantasyTheme;

// CSS custom properties generator for fantasy themes
export const generateFantasyCSS = (theme: FantasyTheme): string => {
  const flattenColors = (obj: any, prefix = ''): Record<string, string> => {
    const result: Record<string, string> = {};

    Object.entries(obj).forEach(([key, value]) => {
      if (typeof value === 'string') {
        result[`${prefix}${key}`] = value;
      } else if (typeof value === 'object' && value !== null) {
        Object.assign(result, flattenColors(value, `${prefix}${key}-`));
      }
    });

    return result;
  };

  const colors = flattenColors(theme.colors, 'fantasy-color-');
  const brandColorsFlat = flattenColors(theme.brandColors, 'brand-');

  const cssProperties = [
    ...Object.entries(colors).map(([key, value]) => `  --uf-${key}: ${value};`),
    ...Object.entries(brandColorsFlat).map(([key, value]) => `  --uf-${key}: ${value};`)
  ].join('\n');

  return `:root {\n${cssProperties}\n}`;
};