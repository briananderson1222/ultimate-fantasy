/**
 * Shadow tokens for the fantasy sports design system
 * Subtle depth shadows for glass-morphism effects
 */

export interface ShadowTokens {
  // Elevation levels
  none: string;       // No shadow
  sm: string;         // Small shadow for subtle elevation
  md: string;         // Medium shadow for cards and buttons
  lg: string;         // Large shadow for modals and overlays
  xl: string;         // Extra large shadow for floating elements
  '2xl': string;      // Maximum shadow for highest elevation

  // Interactive shadows
  button: string;     // Default button shadow
  buttonHover: string; // Button hover state shadow
  buttonActive: string; // Button active/pressed state shadow

  // Component-specific shadows
  card: string;       // Card shadow for content containers
  modal: string;      // Modal/dialog shadow
  dropdown: string;   // Dropdown/popover shadow
  tooltip: string;    // Tooltip shadow

  // Special effects
  glow: string;       // Glow effect for primary elements
  focus: string;      // Focus ring shadow
  error: string;      // Error state shadow
}

export const shadowTokens: ShadowTokens = {
  // Base elevation shadows with subtle opacity
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

  // Interactive element shadows
  button: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  buttonHover: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  buttonActive: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',

  // Component shadows with subtle elevation
  card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  modal: '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1)',
  dropdown: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  tooltip: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',

  // Special effect shadows
  glow: '0 0 20px rgba(0, 229, 255, 0.3)', // Primary color glow
  focus: '0 0 0 3px rgba(0, 229, 255, 0.3)', // Focus ring with primary color
  error: '0 0 0 3px rgba(239, 68, 68, 0.3)', // Error focus ring
};

// Theme-specific shadows for light and dark themes
export interface ThemeShadows {
  light: ShadowTokens;
  dark: ShadowTokens;
}

export const themeShadows: ThemeShadows = {
  light: {
    ...shadowTokens,
    // Light theme uses standard black shadows
  },

  dark: {
    // Dark theme shadows with adjusted opacity and some colored shadows
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.6)',

    // Enhanced shadows for dark theme
    button: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    buttonHover: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    buttonActive: '0 1px 2px 0 rgba(0, 0, 0, 0.2)',

    card: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 229, 255, 0.1)',
    modal: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(0, 229, 255, 0.2)',
    dropdown: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    tooltip: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',

    // Enhanced special effects for dark theme
    glow: '0 0 20px rgba(0, 229, 255, 0.5), 0 0 40px rgba(0, 229, 255, 0.2)',
    focus: '0 0 0 3px rgba(0, 229, 255, 0.5)',
    error: '0 0 0 3px rgba(239, 68, 68, 0.5)',
  },
};

// CSS custom property names for shadows
export const shadowVariables = {
  none: '--shadow-none',
  sm: '--shadow-sm',
  md: '--shadow-md',
  lg: '--shadow-lg',
  xl: '--shadow-xl',
  '2xl': '--shadow-2xl',

  button: '--shadow-button',
  buttonHover: '--shadow-button-hover',
  buttonActive: '--shadow-button-active',

  card: '--shadow-card',
  modal: '--shadow-modal',
  dropdown: '--shadow-dropdown',
  tooltip: '--shadow-tooltip',

  glow: '--shadow-glow',
  focus: '--shadow-focus',
  error: '--shadow-error',
} as const;

// Helper function to generate CSS custom properties
export const generateShadowVariables = (theme: 'light' | 'dark'): Record<string, string> => {
  const tokens = themeShadows[theme];

  return {
    [shadowVariables.none]: tokens.none,
    [shadowVariables.sm]: tokens.sm,
    [shadowVariables.md]: tokens.md,
    [shadowVariables.lg]: tokens.lg,
    [shadowVariables.xl]: tokens.xl,
    [shadowVariables['2xl']]: tokens['2xl'],

    [shadowVariables.button]: tokens.button,
    [shadowVariables.buttonHover]: tokens.buttonHover,
    [shadowVariables.buttonActive]: tokens.buttonActive,

    [shadowVariables.card]: tokens.card,
    [shadowVariables.modal]: tokens.modal,
    [shadowVariables.dropdown]: tokens.dropdown,
    [shadowVariables.tooltip]: tokens.tooltip,

    [shadowVariables.glow]: tokens.glow,
    [shadowVariables.focus]: tokens.focus,
    [shadowVariables.error]: tokens.error,
  };
};

// Border radius tokens to complement shadows
export interface BorderRadiusTokens {
  none: string;
  sm: string;      // 4px
  md: string;      // 8px
  lg: string;      // 12px
  xl: string;      // 16px
  '2xl': string;   // 24px
  full: string;    // 50% (for circles)
}

export const borderRadiusTokens: BorderRadiusTokens = {
  none: '0',
  sm: '0.25rem',   // 4px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px - primary radius for cards
  xl: '1rem',      // 16px
  '2xl': '1.5rem', // 24px
  full: '50%',     // For circular elements
};

// CSS custom property names for border radius
export const borderRadiusVariables = {
  none: '--radius-none',
  sm: '--radius-sm',
  md: '--radius-md',
  lg: '--radius-lg',
  xl: '--radius-xl',
  '2xl': '--radius-2xl',
  full: '--radius-full',
} as const;

// Helper function to generate border radius CSS variables
export const generateBorderRadiusVariables = (): Record<string, string> => {
  return {
    [borderRadiusVariables.none]: borderRadiusTokens.none,
    [borderRadiusVariables.sm]: borderRadiusTokens.sm,
    [borderRadiusVariables.md]: borderRadiusTokens.md,
    [borderRadiusVariables.lg]: borderRadiusTokens.lg,
    [borderRadiusVariables.xl]: borderRadiusTokens.xl,
    [borderRadiusVariables['2xl']]: borderRadiusTokens['2xl'],
    [borderRadiusVariables.full]: borderRadiusTokens.full,
  };
};