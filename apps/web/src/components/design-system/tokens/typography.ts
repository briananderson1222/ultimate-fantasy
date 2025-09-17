/**
 * Typography tokens for the fantasy sports design system
 * Optimized for sports content with mobile-first approach
 */

export interface TypographyStyle {
  fontSize: string;
  fontWeight: number;
  lineHeight: string;
  letterSpacing?: string;
  fontFamily?: string;
}

export interface TypographyScale {
  h1: TypographyStyle;
  h2: TypographyStyle;
  h3: TypographyStyle;
  h4: TypographyStyle;
  bodyLarge: TypographyStyle;
  body: TypographyStyle;
  bodySmall: TypographyStyle;
  caption: TypographyStyle;
  button: TypographyStyle;
  label: TypographyStyle;
}

export interface TypographyTokens {
  mobile: TypographyScale;
  base: TypographyScale;
  desktop: TypographyScale;
}

// Font family stacks optimized for sports content readability
const fontStacks = {
  sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  mono: '"SF Mono", Monaco, Inconsolata, "Roboto Mono", Consolas, "Courier New", monospace',
} as const;

export const typographyTokens: TypographyTokens = {
  // Mobile-first: Optimized for small screens and touch interfaces
  mobile: {
    h1: {
      fontSize: '1.75rem',      // 28px
      fontWeight: 700,
      lineHeight: '1.2',
      letterSpacing: '-0.025em',
      fontFamily: fontStacks.sans,
    },
    h2: {
      fontSize: '1.5rem',       // 24px
      fontWeight: 600,
      lineHeight: '1.25',
      letterSpacing: '-0.02em',
      fontFamily: fontStacks.sans,
    },
    h3: {
      fontSize: '1.25rem',      // 20px
      fontWeight: 600,
      lineHeight: '1.3',
      letterSpacing: '-0.015em',
      fontFamily: fontStacks.sans,
    },
    h4: {
      fontSize: '1.125rem',     // 18px
      fontWeight: 500,
      lineHeight: '1.35',
      fontFamily: fontStacks.sans,
    },
    bodyLarge: {
      fontSize: '1.125rem',     // 18px
      fontWeight: 400,
      lineHeight: '1.6',
      fontFamily: fontStacks.sans,
    },
    body: {
      fontSize: '1rem',         // 16px
      fontWeight: 400,
      lineHeight: '1.5',
      fontFamily: fontStacks.sans,
    },
    bodySmall: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 400,
      lineHeight: '1.4',
      fontFamily: fontStacks.sans,
    },
    caption: {
      fontSize: '0.75rem',      // 12px
      fontWeight: 400,
      lineHeight: '1.3',
      letterSpacing: '0.025em',
      fontFamily: fontStacks.sans,
    },
    button: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 500,
      lineHeight: '1',
      letterSpacing: '0.05em',
      fontFamily: fontStacks.sans,
    },
    label: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 500,
      lineHeight: '1.2',
      fontFamily: fontStacks.sans,
    },
  },

  // Base: Default scale for general use
  base: {
    h1: {
      fontSize: '2rem',         // 32px
      fontWeight: 700,
      lineHeight: '1.2',
      letterSpacing: '-0.025em',
      fontFamily: fontStacks.sans,
    },
    h2: {
      fontSize: '1.75rem',      // 28px
      fontWeight: 600,
      lineHeight: '1.25',
      letterSpacing: '-0.02em',
      fontFamily: fontStacks.sans,
    },
    h3: {
      fontSize: '1.5rem',       // 24px
      fontWeight: 600,
      lineHeight: '1.3',
      letterSpacing: '-0.015em',
      fontFamily: fontStacks.sans,
    },
    h4: {
      fontSize: '1.25rem',      // 20px
      fontWeight: 500,
      lineHeight: '1.35',
      fontFamily: fontStacks.sans,
    },
    bodyLarge: {
      fontSize: '1.25rem',      // 20px
      fontWeight: 400,
      lineHeight: '1.6',
      fontFamily: fontStacks.sans,
    },
    body: {
      fontSize: '1rem',         // 16px
      fontWeight: 400,
      lineHeight: '1.5',
      fontFamily: fontStacks.sans,
    },
    bodySmall: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 400,
      lineHeight: '1.4',
      fontFamily: fontStacks.sans,
    },
    caption: {
      fontSize: '0.75rem',      // 12px
      fontWeight: 400,
      lineHeight: '1.3',
      letterSpacing: '0.025em',
      fontFamily: fontStacks.sans,
    },
    button: {
      fontSize: '1rem',         // 16px
      fontWeight: 500,
      lineHeight: '1',
      letterSpacing: '0.025em',
      fontFamily: fontStacks.sans,
    },
    label: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 500,
      lineHeight: '1.2',
      fontFamily: fontStacks.sans,
    },
  },

  // Desktop: Enhanced scale for larger screens
  desktop: {
    h1: {
      fontSize: '2.5rem',       // 40px
      fontWeight: 700,
      lineHeight: '1.1',
      letterSpacing: '-0.03em',
      fontFamily: fontStacks.sans,
    },
    h2: {
      fontSize: '2rem',         // 32px
      fontWeight: 600,
      lineHeight: '1.2',
      letterSpacing: '-0.025em',
      fontFamily: fontStacks.sans,
    },
    h3: {
      fontSize: '1.75rem',      // 28px
      fontWeight: 600,
      lineHeight: '1.25',
      letterSpacing: '-0.02em',
      fontFamily: fontStacks.sans,
    },
    h4: {
      fontSize: '1.5rem',       // 24px
      fontWeight: 500,
      lineHeight: '1.3',
      letterSpacing: '-0.015em',
      fontFamily: fontStacks.sans,
    },
    bodyLarge: {
      fontSize: '1.375rem',     // 22px
      fontWeight: 400,
      lineHeight: '1.6',
      fontFamily: fontStacks.sans,
    },
    body: {
      fontSize: '1.125rem',     // 18px
      fontWeight: 400,
      lineHeight: '1.5',
      fontFamily: fontStacks.sans,
    },
    bodySmall: {
      fontSize: '1rem',         // 16px
      fontWeight: 400,
      lineHeight: '1.4',
      fontFamily: fontStacks.sans,
    },
    caption: {
      fontSize: '0.875rem',     // 14px
      fontWeight: 400,
      lineHeight: '1.3',
      letterSpacing: '0.025em',
      fontFamily: fontStacks.sans,
    },
    button: {
      fontSize: '1rem',         // 16px
      fontWeight: 500,
      lineHeight: '1',
      letterSpacing: '0.025em',
      fontFamily: fontStacks.sans,
    },
    label: {
      fontSize: '1rem',         // 16px
      fontWeight: 500,
      lineHeight: '1.2',
      fontFamily: fontStacks.sans,
    },
  },
};

// CSS custom property names for typography
export const typographyVariables = {
  // Font families
  fontSans: '--font-sans',
  fontMono: '--font-mono',

  // Font sizes
  h1Size: '--text-h1-size',
  h2Size: '--text-h2-size',
  h3Size: '--text-h3-size',
  h4Size: '--text-h4-size',
  bodyLargeSize: '--text-body-large-size',
  bodySize: '--text-body-size',
  bodySmallSize: '--text-body-small-size',
  captionSize: '--text-caption-size',
  buttonSize: '--text-button-size',
  labelSize: '--text-label-size',

  // Font weights
  weightLight: '--font-weight-light',
  weightNormal: '--font-weight-normal',
  weightMedium: '--font-weight-medium',
  weightSemibold: '--font-weight-semibold',
  weightBold: '--font-weight-bold',
} as const;

// Helper function to generate CSS custom properties for a scale
export const generateTypographyVariables = (scale: keyof TypographyTokens): Record<string, string> => {
  const tokens = typographyTokens[scale];

  return {
    [typographyVariables.fontSans]: fontStacks.sans,
    [typographyVariables.fontMono]: fontStacks.mono,

    [typographyVariables.h1Size]: tokens.h1.fontSize,
    [typographyVariables.h2Size]: tokens.h2.fontSize,
    [typographyVariables.h3Size]: tokens.h3.fontSize,
    [typographyVariables.h4Size]: tokens.h4.fontSize,
    [typographyVariables.bodyLargeSize]: tokens.bodyLarge.fontSize,
    [typographyVariables.bodySize]: tokens.body.fontSize,
    [typographyVariables.bodySmallSize]: tokens.bodySmall.fontSize,
    [typographyVariables.captionSize]: tokens.caption.fontSize,
    [typographyVariables.buttonSize]: tokens.button.fontSize,
    [typographyVariables.labelSize]: tokens.label.fontSize,

    [typographyVariables.weightLight]: '300',
    [typographyVariables.weightNormal]: '400',
    [typographyVariables.weightMedium]: '500',
    [typographyVariables.weightSemibold]: '600',
    [typographyVariables.weightBold]: '700',
  };
};

// Utility function to get responsive typography
export const getResponsiveTypography = (element: keyof TypographyScale) => ({
  mobile: typographyTokens.mobile[element],
  base: typographyTokens.base[element],
  desktop: typographyTokens.desktop[element],
});