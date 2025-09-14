"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type ThemeName = "light" | "dark" | "custom";
type ThemeVars = Partial<Record<string, string>>; // CSS variable map like { "--color-bg": "#fff" }

type ThemeContextValue = {
  theme: ThemeName;
  setTheme: (t: ThemeName) => void;
  custom: ThemeVars;
  setCustom: (vars: ThemeVars) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const DEFAULTS: Record<ThemeName, ThemeVars> = {
  light: {
    "--color-bg": "rgb(249, 250, 251)", // slate-50
    "--color-text": "rgb(17, 24, 39)", // slate-900
  },
  dark: {
    "--color-bg": "rgb(17, 24, 39)", // slate-900
    "--color-text": "rgb(229, 231, 235)", // slate-200
  },
  custom: {},
};

function applyVars(vars: ThemeVars) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  Object.entries(vars).forEach(([k, v]) => {
    root.style.setProperty(k, v || null);
  });
}

function loadLocal<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function saveLocal<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {}
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>("light");
  const [custom, setCustomState] = useState<ThemeVars>({});

  useEffect(() => {
    const initialTheme = loadLocal<ThemeName>("uf_theme", "light");
    const initialCustom = loadLocal<ThemeVars>("uf_theme_custom", {});
    setThemeState(initialTheme);
    setCustomState(initialCustom);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    const base = DEFAULTS[theme];
    applyVars(base);
    if (theme === "custom") applyVars(custom);
  }, [theme, custom]);

  const setTheme = useCallback((t: ThemeName) => {
    setThemeState(t);
    saveLocal("uf_theme", t);
  }, []);

  const setCustom = useCallback((vars: ThemeVars) => {
    setCustomState(vars);
    saveLocal("uf_theme_custom", vars);
  }, []);

  const value = useMemo(() => ({ theme, setTheme, custom, setCustom }), [theme, setTheme, custom, setCustom]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

