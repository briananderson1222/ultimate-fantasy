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
      {/* Hero */}
      <section className="hero-gradient">
        <div className="mx-auto max-w-6xl px-4 py-10 md:py-16">
          <div className="grid items-center gap-8 md:grid-cols-2">
            <div>
              <h1 className="h1 mb-2 text-white drop-shadow">Build the league you want.</h1>
              <p className="mb-4 max-w-prose text-[var(--color-accent-contrast)]/90">
                Ultimate Fantasy is a flexible, brandable platform for leagues, lineups, scoreboards, and waivers — with powerful theming and a polished UX.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <Link href="/leagues/create">
                  <Button size="lg" variant="secondary">Create League</Button>
                </Link>
                <a className="underline text-white/90" href="/leagues">Browse Leagues</a>
              </div>
            </div>
            <div className="surface-textured rounded-[var(--radius-lg)] p-6 shadow-md">
              <div className="flex items-center gap-3">
                <Trophy className="h-8 w-8 text-[var(--color-accent)]" aria-hidden />
                <h2 className="h2 m-0">Join a league</h2>
              </div>
              <p className="mt-1 text-[var(--color-muted)]">Have an invite link or league ID? Paste it here.</p>
              <form className="mt-3 flex gap-2" onSubmit={handleJoin}>
                <label htmlFor="invite" className="sr-only">Invite link or league ID</label>
                <input
                  id="invite"
                  value={invite}
                  onChange={(e) => setInvite(e.target.value)}
                  placeholder="https://…/leagues/… or league-id"
                  className="flex-1 rounded-[var(--radius-md)] border px-[var(--space-3)] py-[var(--space-2)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)]"
                  style={{ background: 'var(--color-surface)', color: 'var(--color-text)', borderColor: 'var(--border)' }}
                />
                <Button type="submit" variant="primary">Go</Button>
              </form>
              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
            </div>
          </div>
        </div>
      </section>

      {/* Highlights */}
      <section>
        <div className="mx-auto max-w-6xl px-4 py-10">
          <div className="grid gap-4 md:grid-cols-3">
            <Feature
              icon={<LayoutDashboard className="h-6 w-6" aria-hidden />}
              title="Customizable UI"
              text="Widgets, saved views, filters, and themes. Make it yours."
            />
            <Feature
              icon={<LineChart className="h-6 w-6" aria-hidden />}
              title="Live Scoreboard"
              text="Aggregated points and lineup tracking with fast updates."
            />
            <Feature
              icon={<Users className="h-6 w-6" aria-hidden />}
              title="Easy League Management"
              text="Create, join, and manage members with clear, accessible flows."
            />
          </div>
        </div>
      </section>
    </>
  );
}

function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="surface rounded-[var(--radius-md)] p-4">
      <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[rgba(0,0,0,0.04)]">
        <span className="text-[var(--color-primary)]">{icon}</span>
      </div>
      <h3 className="h3 mb-1">{title}</h3>
      <p className="text-[var(--color-muted)]">{text}</p>
    </div>
  );
}
