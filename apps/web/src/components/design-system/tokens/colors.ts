/**
 * Color tokens for the fantasy sports design system
 * Based on the research findings and specification
 */

export interface ColorGradient {
  from: string;
  to: string;
  direction?: string;
}

export interface ColorTokens {
  primary: string;
  success: string;
  warning: string;
  background: ColorGradient;
  surface: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
}

export interface ThemeColors {
  light: ColorTokens;
  dark: ColorTokens;
}

export const colorTokens: ThemeColors = {
  dark: {
    // Semantic colors from specification
    primary: "#00e5ff", // Bright cyan (main accent)
    success: "#00e676", // Success green (positive actions)
    warning: "#ffb74d", // Warning amber (alerts/warnings)

    // Background system
    background: {
      from: "#0f0f23", // Deep navy start
      to: "#1a1a2e", // Deep navy with subtle gradient
      direction: "to-b", // Top to bottom gradient
    },

    // Surface and container colors
    surface: "#2d2d44", // Card backgrounds with subtle accent

    // Text colors
    textPrimary: "#ffffff", // Main text color
    textSecondary: "#b0b0b0", // Secondary text

    // Border color with primary accent
    border: "rgba(0, 229, 255, 0.1)", // Primary with low opacity
  },

  light: {
    // Semantic colors (same as dark for consistency)
    primary: "#00e5ff",
    success: "#00e676",
    warning: "#ffb74d",

    // Light theme background
    background: {
      from: "#ffffff",
      to: "#f8fafc",
      direction: "to-b",
    },

    // Light surface colors
    surface: "#ffffff",

    // Light text colors
    textPrimary: "#1a1a1a",
    textSecondary: "#6b7280",

    // Light border
    border: "rgba(0, 0, 0, 0.1)",
  },
};

// CSS custom property names for runtime theme switching
export const cssVariables = {
  primary: "--color-primary",
  success: "--color-success",
  warning: "--color-warning",
  backgroundFrom: "--color-background-from",
  backgroundTo: "--color-background-to",
  surface: "--color-surface",
  textPrimary: "--color-text-primary",
  textSecondary: "--color-text-secondary",
  border: "--color-border",
} as const;

// Helper function to generate CSS custom properties
export const generateCSSVariables = (theme: "light" | "dark"): Record<string, string> => {
  const tokens = colorTokens[theme];

  return {
    [cssVariables.primary]: tokens.primary,
    [cssVariables.success]: tokens.success,
    [cssVariables.warning]: tokens.warning,
    [cssVariables.backgroundFrom]: tokens.background.from,
    [cssVariables.backgroundTo]: tokens.background.to,
    [cssVariables.surface]: tokens.surface,
    [cssVariables.textPrimary]: tokens.textPrimary,
    [cssVariables.textSecondary]: tokens.textSecondary,
    [cssVariables.border]: tokens.border,
  };
};

// Utility functions for common color operations
export const getContrastColor = (backgroundColor: string): string => {
  // Simple contrast calculation - could be enhanced with more sophisticated logic
  const isDark =
    backgroundColor.includes("#0") ||
    backgroundColor.includes("#1") ||
    backgroundColor.includes("#2");
  return isDark ? colorTokens.dark.textPrimary : colorTokens.light.textPrimary;
};

export const applyAlpha = (color: string, alpha: number): string => {
  // Convert hex to rgba with alpha
  if (color.startsWith("#")) {
    const hex = color.substring(1);
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return color;
};
