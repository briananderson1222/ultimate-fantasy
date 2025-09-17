import { describe, it, expect, beforeEach } from "vitest";
import { loadPreferences, savePreferences, updatePreferences } from "../../src/lib/preferences";

describe("preferences store", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns defaults when empty", () => {
    const p = loadPreferences();
    expect(p.theme).toBe("light");
    expect(p.density).toBe("comfortable");
    expect(p.locale).toBe("en-US");
  });

  it("persists updates to localStorage", () => {
    const next = updatePreferences({ theme: "dark", density: "compact" });
    expect(next.theme).toBe("dark");
    expect(next.density).toBe("compact");
    const loaded = loadPreferences();
    expect(loaded.theme).toBe("dark");
    expect(loaded.density).toBe("compact");
  });

  it.skip("syncs with server API when available", async () => {
    // To be implemented with /me/preferences endpoint
  });
});
