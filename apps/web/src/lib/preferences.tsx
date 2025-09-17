import React from "react";

export type Preferences = {
  theme: "light" | "dark" | "custom";
  density: "comfortable" | "compact";
  locale: string;
  layouts?: Record<string, unknown>; // optional per-view or per-scope layouts
};

const DEFAULTS: Preferences = {
  theme: "light",
  density: "comfortable",
  locale: "en-US",
};

const KEY = "uf_prefs";
const KEY_SERVER = "uf_prefs_server";

export function loadPreferences(): Preferences {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return DEFAULTS;
    const p = JSON.parse(raw) as Partial<Preferences>;
    return { ...DEFAULTS, ...p };
  } catch {
    return DEFAULTS;
  }
}

export function savePreferences(prefs: Preferences): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(prefs));
  } catch {}
}

export function updatePreferences(partial: Partial<Preferences>) {
  const current = loadPreferences();
  const next = { ...current, ...partial };
  savePreferences(next);
  return next;
}

// React context + hook for preferences with optimistic (future) server sync
type Ctx = {
  preferences: Preferences;
  setTheme: (t: Preferences["theme"]) => void;
  setDensity: (d: Preferences["density"]) => void;
  setLocale: (l: string) => void;
  setLayouts: (layouts: Record<string, unknown>) => void;
  update: (partial: Partial<Preferences>) => void;
  syncNow: () => Promise<void>;
  // Conflict and reset helpers
  hasConflict: boolean;
  resetToDefaults: () => void;
  resetToServer: () => Promise<void>;
  applyLocalOverrides: () => void;
};

const PreferencesContext = React.createContext<Ctx | undefined>(undefined);

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences] = React.useState<Preferences>(() => loadPreferences());
  const [hasConflict, setHasConflict] = React.useState(false);
  // Keep track of last server snapshot and last synced value to avoid loops
  const lastServerRef = React.useRef<Preferences | null>(null);
  const lastSyncedRef = React.useRef<string | null>(null);
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Persist on change
  React.useEffect(() => {
    savePreferences(preferences);
  }, [preferences]);

  // Reflect density on <html> for CSS variable overrides
  React.useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.dataset.density = preferences.density;
    }
  }, [preferences.density]);

  // Placeholder for future server sync; safe to call before API exists
  const syncNow = React.useCallback(async () => {
    try {
      // Lazy import to avoid coupling before API exists
      const mod = await import("../services/api");
      const fn = (mod as any).updatePreferences as undefined | ((p: Preferences) => Promise<any>);
      if (typeof fn === "function") {
        await fn(preferences);
        lastSyncedRef.current = JSON.stringify(preferences);
      }
    } catch {
      // no-op when API is unavailable
    }
  }, [preferences]);

  const setTheme = (t: Preferences["theme"]) => setPreferences((p) => ({ ...p, theme: t }));
  const setDensity = (d: Preferences["density"]) => setPreferences((p) => ({ ...p, density: d }));
  const setLocale = (l: string) => setPreferences((p) => ({ ...p, locale: l }));
  const setLayouts = (layouts: Record<string, unknown>) =>
    setPreferences((p) => ({ ...p, layouts }));
  const update = (partial: Partial<Preferences>) => setPreferences((p) => ({ ...p, ...partial }));

  // Debounced server sync when preferences change
  React.useEffect(() => {
    // Avoid syncing right after we applied the server snapshot
    const serialized = JSON.stringify(preferences);
    if (lastSyncedRef.current === serialized) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      // Fire-and-forget; errors are swallowed in syncNow
      void syncNow();
    }, 800);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [preferences, syncNow]);

  // Load and merge server preferences on mount
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const rawLast = localStorage.getItem(KEY_SERVER);
        const lastServer = rawLast ? (JSON.parse(rawLast) as Preferences) : null;
        lastServerRef.current = lastServer;
        const mod = await import("../services/api");
        const getFn = (mod as any).getPreferences as
          | undefined
          | (() => Promise<Preferences & { user_id: string }>);
        if (!getFn) return;
        const server = await getFn();
        if (cancelled || !server) return;
        // Store latest server snapshot
        localStorage.setItem(KEY_SERVER, JSON.stringify(server));
        lastServerRef.current = server;
        // Three-way merge: base=lastServer (or server), local=current, remote=server
        const base = lastServer ?? server;
        const local = preferences;
        const remote = server as Preferences;

        const differs = (a: any, b: any) => JSON.stringify(a) !== JSON.stringify(b);
        const localChanged = differs(local, base);
        const remoteChanged = differs(remote, base);

        if (localChanged && remoteChanged && differs(local, remote)) {
          // Conflict: prefer remote by default, but mark conflict to allow manual override
          setHasConflict(true);
          setPreferences(remote);
          lastSyncedRef.current = JSON.stringify(remote);
        } else if (localChanged && !remoteChanged) {
          // Local diverged since last server snapshot, push local up
          setHasConflict(false);
          lastSyncedRef.current = null; // allow debounced sync to PUT local
        } else {
          // Use server
          setHasConflict(false);
          setPreferences(remote);
          lastSyncedRef.current = JSON.stringify(remote);
        }
      } catch {
        // ignore when unauthenticated or API unavailable
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const resetToDefaults = React.useCallback(() => {
    setHasConflict(false);
    setPreferences({ theme: "light", density: "comfortable", locale: "en-US" });
  }, []);

  const resetToServer = React.useCallback(async () => {
    try {
      const raw = localStorage.getItem(KEY_SERVER);
      if (raw) {
        const server = JSON.parse(raw) as Preferences;
        setHasConflict(false);
        setPreferences(server);
        lastSyncedRef.current = JSON.stringify(server);
        return;
      }
      const mod = await import("../services/api");
      const getFn = (mod as any).getPreferences as
        | undefined
        | (() => Promise<Preferences & { user_id: string }>);
      if (getFn) {
        const server = await getFn();
        localStorage.setItem(KEY_SERVER, JSON.stringify(server));
        setHasConflict(false);
        setPreferences(server);
        lastSyncedRef.current = JSON.stringify(server);
      }
    } catch {
      // ignore
    }
  }, []);

  const applyLocalOverrides = React.useCallback(() => {
    // When conflict, re-apply local prefs on top of remote
    try {
      const local = loadPreferences();
      setPreferences(local);
      setHasConflict(false);
      lastSyncedRef.current = null; // trigger debounced sync
    } catch {
      // ignore
    }
  }, []);

  const value: Ctx = {
    preferences,
    setTheme,
    setDensity,
    setLocale,
    setLayouts,
    update,
    syncNow,
    hasConflict,
    resetToDefaults,
    resetToServer,
    applyLocalOverrides,
  };

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences(): Ctx {
  const ctx = React.useContext(PreferencesContext);
  if (!ctx) throw new Error("usePreferences must be used within PreferencesProvider");
  return ctx;
}
