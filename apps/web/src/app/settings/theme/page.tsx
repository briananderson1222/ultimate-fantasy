"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useTheme } from "../../theme";

export default function ThemeSettingsPage() {
  const { theme, setTheme, custom, setCustom } = useTheme();
  const [raw, setRaw] = useState<string>(JSON.stringify(custom, null, 2));
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setRaw(JSON.stringify(custom, null, 2));
  }, [custom]);

  const apply = () => {
    setError("");
    try {
      const parsed = JSON.parse(raw) as Record<string, string>;
      setCustom(parsed);
      setTheme("custom");
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  };

  const preset = (name: "light" | "dark") => () => setTheme(name);

  const example = useMemo(() => ({ "--color-bg": "#ffefd5", "--color-text": "#111111" }), []);

  async function loadFantasyPack() {
    setError("");
    try {
      const res = await fetch("/themes/fantasy-football.json", { cache: "no-store" });
      if (!res.ok) throw new Error(`Failed to load theme preset: ${res.status}`);
      const data = (await res.json()) as Record<string, string>;
      setRaw(JSON.stringify(data, null, 2));
      setCustom(data);
      setTheme("custom");
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Theme Settings</h1>
          <Link href="/leagues" className="underline text-blue-700">
            Back
          </Link>
        </div>

        <div className="rounded border p-4 space-y-3">
          <p className="text-sm text-gray-600">
            Current theme: <strong>{theme}</strong>
          </p>
          <div className="flex gap-2">
            <button className="rounded bg-gray-200 px-3 py-2" onClick={preset("light")}>
              Light
            </button>
            <button className="rounded bg-gray-800 px-3 py-2 text-white" onClick={preset("dark")}>
              Dark
            </button>
            <button
              className="rounded bg-indigo-600 px-3 py-2 text-white"
              onClick={() => setTheme("custom")}
            >
              Custom
            </button>
            <Link className="rounded bg-gray-100 px-3 py-2" href="/settings/theme">
              Reload
            </Link>
          </div>
        </div>

        <div className="rounded border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Custom Theme JSON</h2>
            <div className="flex items-center gap-2">
              <button
                className="rounded bg-gray-700 px-3 py-1.5 text-white"
                onClick={() => setRaw(JSON.stringify(example, null, 2))}
              >
                Load Example
              </button>
              <button
                className="rounded bg-green-700 px-3 py-1.5 text-white"
                onClick={loadFantasyPack}
              >
                Load Fantasy Pack
              </button>
            </div>
          </div>
          <textarea
            aria-label="Custom Theme JSON"
            className="w-full h-48 rounded border p-2 font-mono text-sm"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <button className="rounded bg-green-600 px-3 py-2 text-white" onClick={apply}>
              Apply
            </button>
            <span className="text-xs text-gray-600">
              Provide a JSON object of CSS variables: e.g.,{" "}
              {`{ "--color-bg": "#fff", "--color-text": "#111" }`}
            </span>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </div>
    </main>
  );
}
