"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { LeaguesService, httpClient } from "@ultimate-fantasy/api-client";
import { Skeleton } from "../../components/ui/skeleton";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Button } from "../../components/ui/button";
import { Plus } from "lucide-react";

export default function LeaguesListPage() {
  const router = useRouter();
  const [inviteLink, setInviteLink] = useState("");
  const [error, setError] = useState("");

  const leaguesService = LeaguesService.create(httpClient);

  const leagues = useQuery({
    queryKey: ["myLeagues"],
    queryFn: () => leaguesService.getMyLeagues(),
  });

  function handleJoinLeague(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const v = inviteLink.trim();
    if (!v) return;

    try {
      let leagueId = "";
      if (/^https?:\/\//i.test(v)) {
        // Extract league ID from URL
        const url = new URL(v);
        const parts = url.pathname.split("/").filter(Boolean);
        const idx = parts.indexOf("leagues");
        if (idx >= 0 && parts[idx + 1]) leagueId = parts[idx + 1];
      } else if (/^[0-9a-fA-F-]{8,}$/.test(v)) {
        // Direct league ID
        leagueId = v;
      }
      if (!leagueId) throw new Error("Please enter a valid invite link or league ID");
      router.push(`/leagues/${leagueId}`);
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader
          title="My Leagues"
          actions={
            <Link href="/leagues/create">
              <Button leftIcon={<Plus className="h-4 w-4" aria-hidden />}>Create League</Button>
            </Link>
          }
        />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Your Leagues</CardTitle>
          </CardHeader>
          {leagues.isLoading && <Skeleton className="h-16 w-full" />}
          {leagues.isError && (
            <div className="text-sm text-red-700 flex items-center justify-between">
              <span>{(leagues.error as Error)?.message}</span>
              <button
                className="rounded bg-[var(--color-surface)] border border-[var(--border)] px-3 py-1 text-[var(--color-text)] hover:bg-[var(--color-elevated)]"
                onClick={() => leagues.refetch()}
              >
                Retry
              </button>
            </div>
          )}
          {leagues.data && (
            <ul className="divide-y text-sm">
              {leagues.data.items.map((it) => (
                <li key={it.team_id} className="flex items-center justify-between py-3">
                  <div>
                    <div className="font-medium">{it.name}</div>
                    <div className="text-[var(--color-muted)] text-xs">Season {it.season}</div>
                  </div>
                  <Link
                    className="text-[var(--color-primary)] hover:underline px-2 py-1 rounded focus-visible:ring-2 focus-visible:ring-offset-2"
                    href={`/leagues/${it.league_id}`}
                  >
                    View League
                  </Link>
                </li>
              ))}
              {leagues.data.items.length === 0 && (
                <li className="py-4">
                  <EmptyState
                    title="No leagues yet"
                    description="Create your first league or join one using an invite link."
                    action={
                      <div className="flex gap-2">
                        <Link href="/leagues/create">
                          <Button>Create League</Button>
                        </Link>
                      </div>
                    }
                  />
                </li>
              )}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Join a League</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <p className="text-sm text-[var(--color-muted)]">
              Have an invite link? Paste it here to join the league.
            </p>
            <form onSubmit={handleJoinLeague} className="flex gap-2">
              <div className="flex-1">
                <label htmlFor="invite-input" className="sr-only">
                  Invite link or league ID
                </label>
                <input
                  id="invite-input"
                  value={inviteLink}
                  onChange={(e) => setInviteLink(e.target.value)}
                  placeholder="https://ultimatefantasy.app/leagues/abc-123 or league-id"
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] placeholder-[var(--color-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
              <Button type="submit" disabled={!inviteLink.trim()}>
                Join League
              </Button>
            </form>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        </Card>
      </div>
    </main>
  );
}
