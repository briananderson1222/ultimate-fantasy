/**
 * Spacing tokens for the fantasy sports design system
 * Dense mobile-friendly spacing with consistent scale
 */

export interface SpacingTokens {
  // Base spacing units (px values)
  xs: string; // 4px  - Minimal spacing
  sm: string; // 8px  - Small spacing
  md: string; // 16px - Base spacing unit
  lg: string; // 24px - Large spacing
  xl: string; // 32px - Extra large spacing
  "2xl": string; // 48px - 2x extra large
  "3xl": string; // 64px - 3x extra large
  "4xl": string; // 96px - 4x extra large

  // Semantic spacing
  component: string; // Internal component spacing
  section: string; // Between sections
  page: string; // Page margins/padding

  // Interactive elements
  button: string; // Button padding
  input: string; // Input field padding
  card: string; // Card internal padding

  // Layout spacing
  grid: string; // Grid gaps
  stack: string; // Vertical stack spacing
  inline: string; // Inline element spacing
}

export const spacingTokens: SpacingTokens = {
  // Base scale using 4px as fundamental unit
  xs: "0.25rem", // 4px
  sm: "0.5rem", // 8px
  md: "1rem", // 16px
  lg: "1.5rem", // 24px
  xl: "2rem", // 32px
  "2xl": "3rem", // 48px
  "3xl": "4rem", // 64px
  "4xl": "6rem", // 96px

  // Semantic spacing based on use cases
  component: "0.5rem", // 8px - internal component spacing
  section: "1.5rem", // 24px - between logical sections
  page: "1rem", // 16px - page-level margins (mobile-friendly)

  // Interactive element spacing
  button: "0.75rem 1rem", // 12px vertical, 16px horizontal
  input: "0.75rem", // 12px - input field padding
  card: "1rem", // 16px - card internal padding

  // Layout spacing
  grid: "1rem", // 16px - grid gaps
  stack: "0.75rem", // 12px - vertical spacing in stacks
  inline: "0.5rem", // 8px - horizontal spacing for inline elements
};

// Responsive spacing tokens for different screen sizes
export interface ResponsiveSpacing {
  mobile: SpacingTokens;
  tablet: SpacingTokens;
  desktop: SpacingTokens;
}

export const responsiveSpacing: ResponsiveSpacing = {
  mobile: {
    ...spacingTokens,
    // Override specific values for mobile
    page: "0.75rem", // 12px - tighter page margins on mobile
    section: "1rem", // 16px - reduced section spacing
    card: "0.75rem", // 12px - tighter card padding
  },

  tablet: {
    ...spacingTokens,
    // Default values work well for tablet
    page: "1.5rem", // 24px - more breathing room on tablet
    section: "2rem", // 32px - increased section spacing
  },

  desktop: {
    ...spacingTokens,
    // Enhanced spacing for larger screens
    page: "2rem", // 32px - generous page margins
    section: "3rem", // 48px - large section spacing
    card: "1.5rem", // 24px - more generous card padding
    grid: "1.5rem", // 24px - larger grid gaps
  },
};

// CSS custom property names for spacing
export const spacingVariables = {
  xs: "--space-xs",
  sm: "--space-sm",
  md: "--space-md",
  lg: "--space-lg",
  xl: "--space-xl",
  "2xl": "--space-2xl",
  "3xl": "--space-3xl",
  "4xl": "--space-4xl",

  component: "--space-component",
  section: "--space-section",
  page: "--space-page",

  button: "--space-button",
  input: "--space-input",
  card: "--space-card",

  grid: "--space-grid",
  stack: "--space-stack",
  inline: "--space-inline",
} as const;

// Helper function to generate CSS custom properties
export const generateSpacingVariables = (
  breakpoint: keyof ResponsiveSpacing,
): Record<string, string> => {
  const tokens = responsiveSpacing[breakpoint];

  return {
    [spacingVariables.xs]: tokens.xs,
    [spacingVariables.sm]: tokens.sm,
    [spacingVariables.md]: tokens.md,
    [spacingVariables.lg]: tokens.lg,
    [spacingVariables.xl]: tokens.xl,
    [spacingVariables["2xl"]]: tokens["2xl"],
    [spacingVariables["3xl"]]: tokens["3xl"],
    [spacingVariables["4xl"]]: tokens["4xl"],

    [spacingVariables.component]: tokens.component,
    [spacingVariables.section]: tokens.section,
    [spacingVariables.page]: tokens.page,

    [spacingVariables.button]: tokens.button,
    [spacingVariables.input]: tokens.input,
    [spacingVariables.card]: tokens.card,

    [spacingVariables.grid]: tokens.grid,
    [spacingVariables.stack]: tokens.stack,
    [spacingVariables.inline]: tokens.inline,
  };
};

// Utility functions for spacing calculations
export const addSpacing = (space1: string, space2: string): string => {
  // Simple implementation - could be enhanced with calc() for complex cases
  const value1 = parseFloat(space1);
  const value2 = parseFloat(space2);
  const unit = space1.includes("rem") ? "rem" : "px";

  return `${value1 + value2}${unit}`;
};

export const multiplySpacing = (space: string, multiplier: number): string => {
  const value = parseFloat(space);
  const unit = space.includes("rem") ? "rem" : "px";

  return `${value * multiplier}${unit}`;
};

// Predefined spacing combinations for common use cases
export const spacingCombinations = {
  // Card spacing: padding + internal spacing
  cardFull: `${spacingTokens.card} ${spacingTokens.component}`,

  // Button spacing with hover state expansion
  buttonComfort: spacingTokens.button,
  buttonCompact: "0.5rem 0.75rem", // 8px 12px
  buttonLarge: "1rem 1.5rem", // 16px 24px

  // Form element spacing
  formField: spacingTokens.stack, // Between form fields
  formGroup: spacingTokens.section, // Between form groups

  // Layout containers
  containerPadding: spacingTokens.page,
  sectionMargin: spacingTokens.section,
  componentGap: spacingTokens.component,
} as const;
