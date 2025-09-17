"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import enUS from "../i18n/locales/en-US.json";
import esES from "../i18n/locales/es-ES.json";
import { loadPreferences, updatePreferences } from "../lib/preferences";

type Messages = Record<string, any>;
type Locale = string; // e.g., 'en-US'

const STATIC_CATALOGS: Record<string, Messages> = {
  "en-US": enUS as unknown as Messages,
  "es-ES": esES as unknown as Messages,
};

type I18nContextValue = {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  messages: Messages;
};

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

function lookup(messages: Messages, key: string): string | undefined {
  const parts = key.split(".");
  let cur: any = messages;
  for (const p of parts) {
    if (cur == null) return undefined;
    cur = cur[p];
  }
  if (typeof cur === "string") return cur as string;
  return undefined;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const pref = loadPreferences();
  const [locale, setLocaleState] = useState<Locale>(pref.locale || "en-US");
  const [messages, setMessages] = useState<Messages>(
    STATIC_CATALOGS[locale] || STATIC_CATALOGS["en-US"],
  );

  useEffect(() => {
    let cancelled = false;
    async function load() {
      // Try dynamic import for lazy-loading; fall back to statically bundled catalogs
      try {
        const mod: any = await import(`../i18n/locales/${locale}.json`);
        if (!cancelled) setMessages(mod.default || mod);
      } catch {
        if (!cancelled) setMessages(STATIC_CATALOGS[locale] || STATIC_CATALOGS["en-US"]);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    updatePreferences({ locale: next });
  };

  const t = (key: string, vars?: Record<string, string | number>) => {
    const raw = lookup(messages, key) ?? key;
    if (!vars) return raw;
    return raw.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? `{${k}}`));
  };

  const value = useMemo(() => ({ locale, setLocale, t, messages }), [locale, messages]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
