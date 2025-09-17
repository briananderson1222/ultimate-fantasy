"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trophy, Users, LayoutDashboard, LineChart } from "lucide-react";
import { Button } from "../components/ui/button";

export default function HomePage() {
  const router = useRouter();
  const [invite, setInvite] = React.useState("");
  const [error, setError] = React.useState("");

  function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const v = invite.trim();
    if (!v) return;
    // Accept full URL or direct league ID
    try {
      let leagueId = "";
      if (/^https?:\/\//i.test(v)) {
        const url = new URL(v);
        const parts = url.pathname.split("/").filter(Boolean);
        const idx = parts.indexOf("leagues");
        if (idx >= 0 && parts[idx + 1]) leagueId = parts[idx + 1];
      } else if (/^[0-9a-fA-F-]{8,}$/.test(v)) {
        leagueId = v;
      }
      if (!leagueId) throw new Error("Enter a valid invite link or league ID");
      router.push(`/leagues/${leagueId}`);
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  return (
    <>
      {/* Override layout wrapper for full-width design */}
      <style jsx global>{`
        #main > div {
          max-width: none !important;
          padding: 0 !important;
        }
        body {
          background: var(--gradient-hero) !important;
        }
      `}</style>

      {/* Hero */}
      <section className="relative py-12 md:py-20" style={{ background: "var(--gradient-hero)" }}>
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid items-center gap-8 md:grid-cols-2">
            <div>
              <h1 className="mb-4 text-3xl font-bold text-[var(--color-text)] md:text-5xl drop-shadow">
                Build the league you want.
              </h1>
              <p className="mb-6 text-lg text-[var(--color-muted)]">
                Ultimate Fantasy is a flexible platform for leagues, lineups, scoreboards, and
                waivers.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <Link href="/leagues/create">
                  <Button size="lg" variant="primary">
                    Create League
                  </Button>
                </Link>
                <Link
                  href="/leagues"
                  className="underline text-[var(--color-muted)] hover:text-[var(--color-text)]"
                >
                  Browse Leagues
                </Link>
              </div>
            </div>
            <div className="bg-[var(--color-surface)] border border-[var(--border)] rounded-xl p-6 shadow-lg">
              <div className="flex items-center gap-3 mb-3">
                <Trophy className="h-6 w-6 text-[var(--color-primary)]" aria-hidden />
                <h2 className="text-lg font-semibold text-[var(--color-text)] m-0">
                  Join a league
                </h2>
              </div>
              <p className="mb-4 text-sm text-[var(--color-muted)]">
                Have an invite link or league ID? Paste it here.
              </p>
              <form className="flex gap-2" onSubmit={handleJoin}>
                <label htmlFor="invite" className="sr-only">
                  Invite link or league ID
                </label>
                <input
                  id="invite"
                  value={invite}
                  onChange={(e) => setInvite(e.target.value)}
                  placeholder="League ID or URL"
                  className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] placeholder-[var(--color-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
                <Button type="submit" variant="primary">
                  Go
                </Button>
              </form>
              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
            </div>
          </div>
        </div>
      </section>

      {/* Highlights */}
      <section className="bg-[var(--color-bg)] py-12">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid gap-6 md:grid-cols-3">
            <Feature
              icon={<LayoutDashboard className="h-5 w-5" aria-hidden />}
              title="Customizable UI"
              text="Widgets, saved views, filters, and themes."
            />
            <Feature
              icon={<LineChart className="h-5 w-5" aria-hidden />}
              title="Live Scoreboard"
              text="Real-time points and lineup tracking."
            />
            <Feature
              icon={<Users className="h-5 w-5" aria-hidden />}
              title="Easy Management"
              text="Create, join, and manage leagues easily."
            />
          </div>
        </div>
      </section>
    </>
  );
}

function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--border)] rounded-xl p-4 hover:bg-[var(--color-elevated)] transition-colors">
      <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)] text-[var(--color-primary-contrast)]">
        {icon}
      </div>
      <h3 className="mb-2 text-base font-semibold text-[var(--color-text)]">{title}</h3>
      <p className="text-sm text-[var(--color-muted)]">{text}</p>
    </div>
  );
}
