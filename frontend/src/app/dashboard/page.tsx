"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Settings,
  Trophy,
  Calendar,
  BarChart3,
  Gavel,
  Lightbulb,
} from "lucide-react";
import {
  DEFAULT_WIDGETS,
  loadLayout,
  saveLayout,
  loadSizes,
  saveSizes,
  loadWidgetSettings,
  saveWidgetSettings,
  type WidgetKey,
  type WidgetSizes,
} from "../../lib/dashboard";

type WidgetMeta = { key: WidgetKey; title: string };
const WIDGETS: WidgetMeta[] = [
  { key: "myLeagues", title: "My Leagues" },
  { key: "upcoming", title: "Upcoming" },
  { key: "scoreboard", title: "Scoreboard" },
  { key: "waivers", title: "Waivers" },
  { key: "tips", title: "Tips" },
];

function getWidgetIcon(key: WidgetKey) {
  switch (key) {
    case "myLeagues":
      return <Trophy className="h-4 w-4" />;
    case "upcoming":
      return <Calendar className="h-4 w-4" />;
    case "scoreboard":
      return <BarChart3 className="h-4 w-4" />;
    case "waivers":
      return <Gavel className="h-4 w-4" />;
    case "tips":
      return <Lightbulb className="h-4 w-4" />;
    default:
      return null;
  }
}

function widgetTitle(key: WidgetKey): string {
  return WIDGETS.find((w) => w.key === key)?.title || key;
}

export default function DashboardPage() {
  const [order, setOrder] = useState<WidgetKey[]>(DEFAULT_WIDGETS);
  const [saved, setSaved] = useState(false);
  const [sizes, setSizes] = useState<WidgetSizes>({
    myLeagues: 1,
    upcoming: 1,
    scoreboard: 2,
    waivers: 1,
    tips: 1,
  });
  const [settings, setSettings] = useState(loadWidgetSettings());
  const [openKey, setOpenKey] = useState<WidgetKey | null>(null);

  useEffect(() => {
    setOrder(loadLayout());
    setSizes(loadSizes());
    setSettings(loadWidgetSettings());
  }, []);

  function moveUp(idx: number) {
    if (idx <= 0) return;
    const next = order.slice();
    [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
    setOrder(next);
    setSaved(false);
  }
  function moveDown(idx: number) {
    if (idx >= order.length - 1) return;
    const next = order.slice();
    [next[idx + 1], next[idx]] = [next[idx], next[idx + 1]];
    setOrder(next);
    setSaved(false);
  }
  function reset() {
    setOrder(DEFAULT_WIDGETS);
    setSaved(false);
  }
  function save() {
    saveLayout(order);
    saveSizes(sizes);
    saveWidgetSettings(settings);
    setSaved(true);
  }

  function spanClass(key: WidgetKey) {
    const s = sizes[key] || 1;
    return s === 1 ? "lg:col-span-1" : s === 2 ? "lg:col-span-2" : "lg:col-span-3";
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <div className="flex items-center gap-2">
            <button
              className="rounded bg-[var(--color-primary)] px-3 py-2 text-[var(--color-primary-contrast)] hover:opacity-90"
              onClick={save}
              data-testid="save-layout"
            >
              Save Layout
            </button>
            <button
              className="rounded bg-[var(--color-surface)] border border-[var(--border)] text-[var(--color-text)] px-3 py-2 hover:bg-[var(--color-elevated)]"
              onClick={reset}
              data-testid="reset-layout"
            >
              Reset
            </button>
            {saved && (
              <span className="text-xs text-green-700" aria-live="polite">
                Saved
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {order.map((key, idx) => (
            <section
              key={key}
              className={`rounded border border-[var(--border)] p-3 bg-[var(--color-surface)] ${spanClass(key)}`}
              data-testid="widget"
              aria-roledescription="widget"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData("text/plain", String(idx));
                e.dataTransfer.effectAllowed = "move";
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const from = Number(e.dataTransfer.getData("text/plain"));
                const to = idx;
                if (Number.isNaN(from) || from === to) return;
                const next = order.slice();
                const [moved] = next.splice(from, 1);
                next.splice(to, 0, moved);
                setOrder(next);
                setSaved(false);
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[var(--color-primary)]">{getWidgetIcon(key)}</span>
                  <h2 className="font-medium text-[var(--color-text)]" data-testid="widget-title">
                    {widgetTitle(key)}
                  </h2>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    className="rounded bg-[var(--color-elevated)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface)]"
                    onClick={() => moveUp(idx)}
                    aria-label={`Move ${widgetTitle(key)} up`}
                  >
                    <ChevronUp className="h-3 w-3" />
                  </button>
                  <button
                    className="rounded bg-[var(--color-elevated)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface)]"
                    onClick={() => moveDown(idx)}
                    aria-label={`Move ${widgetTitle(key)} down`}
                  >
                    <ChevronDown className="h-3 w-3" />
                  </button>
                  <button
                    className="rounded bg-[var(--color-elevated)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface)]"
                    onClick={() =>
                      setSizes((prev) => ({
                        ...prev,
                        [key]: Math.max(1, (prev[key] || 1) - 1) as 1 | 2 | 3,
                      }))
                    }
                    aria-label={`Narrow ${widgetTitle(key)}`}
                  >
                    <ChevronLeft className="h-3 w-3" />
                  </button>
                  <button
                    className="rounded bg-[var(--color-elevated)} border border-[var(--border)] px-2 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface)]"
                    onClick={() =>
                      setSizes((prev) => ({
                        ...prev,
                        [key]: Math.min(3, (prev[key] || 1) + 1) as 1 | 2 | 3,
                      }))
                    }
                    aria-label={`Widen ${widgetTitle(key)}`}
                  >
                    <ChevronRight className="h-3 w-3" />
                  </button>
                  <button
                    className="rounded bg-[var(--color-elevated)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface)]"
                    onClick={() => setOpenKey(key)}
                    aria-label={`Settings for ${widgetTitle(key)}`}
                    title="Settings"
                  >
                    <Settings className="h-3 w-3" />
                  </button>
                </div>
              </div>
              <div className="text-sm text-[var(--color-muted)]">
                {/* Placeholder content for each widget */}
                {key === "myLeagues" && (
                  <div>
                    <p>Quick access to your leagues.</p>
                    <Link className="underline text-blue-700" href="/leagues">
                      Go to Leagues
                    </Link>
                  </div>
                )}
                {key === "upcoming" && <p>Upcoming matchups and deadlines.</p>}
                {key === "scoreboard" && <p>Recent scores at a glance.</p>}
                {key === "waivers" && <p>Waiver bids and activity.</p>}
                {key === "tips" && <p>Helpful tips and onboarding links.</p>}
              </div>
            </section>
          ))}
        </div>
        {openKey && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            role="dialog"
            aria-modal
          >
            <div className="absolute inset-0 bg-black/30" onClick={() => setOpenKey(null)} />
            <div className="relative z-10 w-full max-w-md rounded bg-[var(--color-surface)] border border-[var(--border)] p-4 shadow-lg">
              <h2 className="mb-2 text-lg font-medium text-[var(--color-text)]">
                {widgetTitle(openKey)} Settings
              </h2>
              {openKey === "scoreboard" && (
                <div className="space-y-2">
                  <label className="block text-sm text-gray-700">Default League ID</label>
                  <input
                    className="w-full rounded border px-3 py-2"
                    value={settings.scoreboard?.leagueId || ""}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        scoreboard: { ...(prev.scoreboard || {}), leagueId: e.target.value },
                      }))
                    }
                    placeholder="optional league uuid"
                  />
                  <p className="text-xs text-gray-600">
                    Used by the Scoreboard widget when configured.
                  </p>
                </div>
              )}
              {openKey !== "scoreboard" && (
                <div className="text-sm text-gray-600">No configurable options yet.</div>
              )}
              <div className="mt-3 flex items-center justify-end gap-2">
                <button
                  className="rounded bg-[var(--color-surface)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-elevated)]"
                  onClick={() => setOpenKey(null)}
                >
                  Close
                </button>
                <button
                  className="rounded bg-[var(--color-primary)] px-3 py-2 text-sm text-[var(--color-primary-contrast)] hover:opacity-90"
                  onClick={() => {
                    saveWidgetSettings(settings);
                    setOpenKey(null);
                  }}
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
