"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { colorTokens, generateCSSVariables } from "../tokens/colors";
import { generateShadowVariables } from "../tokens/shadows";
import { generateSpacingVariables } from "../tokens/spacing";
import { generateTypographyVariables } from "../tokens/typography";

export type Theme = "light" | "dark" | "system";

export interface ThemeTokens {
  colors: typeof colorTokens.dark;
  // Add other token types as we need them
}

export interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  systemTheme: Theme;
  tokens: ThemeTokens;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export interface ThemeProviderProps {
  children: React.ReactNode;
  initialTheme?: Theme;
  defaultTheme?: Theme;
  enableSystemTheme?: boolean;
}

export const ThemeProvider = ({
  children,
  initialTheme = "dark",
  defaultTheme,
  enableSystemTheme = false,
}: ThemeProviderProps) => {
  const [theme, setThemeState] = useState<Theme>(defaultTheme || initialTheme);
  const [systemTheme, setSystemTheme] = useState<Theme>("dark");

  // Detect system theme preference
  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      setSystemTheme(mediaQuery.matches ? "dark" : "light");

      const handleChange = (e: MediaQueryListEvent) => {
        setSystemTheme(e.matches ? "dark" : "light");
      };

      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, []);

  // Load theme from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined" && !enableSystemTheme) {
      const savedTheme = localStorage.getItem("theme") as Theme;
      if (savedTheme && (savedTheme === "light" || savedTheme === "dark")) {
        setThemeState(savedTheme);
      }
    }
  }, [enableSystemTheme]);

  // Use system theme if enabled or if theme is 'system'
  const effectiveTheme = enableSystemTheme || theme === "system" ? systemTheme : theme;
  const resolvedTheme = effectiveTheme === "system" ? systemTheme : effectiveTheme;

  // Apply CSS custom properties when theme changes
  useEffect(() => {
    if (typeof document !== "undefined") {
      const root = document.documentElement;

      // Apply color variables
      const colorVars = generateCSSVariables(resolvedTheme as "light" | "dark");
      Object.entries(colorVars).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });

      // Apply shadow variables
      const shadowVars = generateShadowVariables(resolvedTheme as "light" | "dark");
      Object.entries(shadowVars).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });

      // Apply spacing variables (using mobile as default)
      const spacingVars = generateSpacingVariables("mobile");
      Object.entries(spacingVars).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });

      // Apply typography variables (using base as default)
      const typographyVars = generateTypographyVariables("base");
      Object.entries(typographyVars).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });

      // Set data attribute for CSS selectors
      root.setAttribute("data-theme", resolvedTheme);
    }
  }, [effectiveTheme, resolvedTheme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    if (typeof window !== "undefined" && !enableSystemTheme) {
      localStorage.setItem("theme", newTheme);
    }
  };

  const tokens: ThemeTokens = {
    colors: colorTokens[resolvedTheme as "light" | "dark"],
  };

  const value: ThemeContextValue = {
    theme: theme,
    setTheme,
    systemTheme,
    tokens,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
