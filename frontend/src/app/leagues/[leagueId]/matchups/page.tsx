"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Skeleton } from "../../../../components/ui/skeleton";
import { EmptyState } from "../../../../components/ui/empty-state";
import { PageHeader } from "../../../../components/ui/page-header";
import { getLeagueMembers, type MembersResponse } from "../../../../services/api";
import { useMemo, useState } from "react";

function rotate<T>(arr: T[], k: number): T[] {
  if (!arr.length) return arr;
  const shift = ((k % arr.length) + arr.length) % arr.length;
  return arr.map((_, i) => arr[(i + shift) % arr.length]);
}

export default function MatchupsPage() {
  const params = useParams<{ leagueId: string }>();
  const leagueId = params?.leagueId;
  const [weekOffset, setWeekOffset] = useState(0);

  const members = useQuery<MembersResponse, Error>({
    queryKey: ["leagueMembers", leagueId],
    queryFn: () => {
      if (!leagueId) throw new Error("leagueId is required");
      return getLeagueMembers(String(leagueId));
    },
    enabled: !!leagueId,
  });

  const baseWeek = useMemo(() => Math.floor((Date.now() / (1000 * 60 * 60 * 24 * 7))), []);
  const week = baseWeek + weekOffset;

  const pairings = useMemo(() => {
    if (!members.data?.items?.length) return [] as Array<[string, string | null]>;
    const ids = members.data.items.map((m) => String(m.team_id)).sort();
    const rot = rotate(ids, week);
    const pairs: Array<[string, string | null]> = [];
    for (let i = 0; i < rot.length; i += 2) {
      const a = rot[i];
      const b = rot[i + 1] ?? null;
      pairs.push([a, b]);
    }
    return pairs;
  }, [members.data, week]);

  function projectedPoints(teamId: string): number {
    let seed = 0;
    const s = teamId + String(week);
    for (let i = 0; i < s.length; i++) seed = (seed * 31 + s.charCodeAt(i)) % 1000;
    return Math.round((70 + (seed % 60) + (seed % 13) / 10) * 10) / 10; // 70..129.9
  }

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <PageHeader
          title="Weekly Matchups"
          actions={
            <div className="flex items-center gap-2 text-sm">
              <button className="rounded bg-gray-200 px-2 py-1" onClick={() => setWeekOffset((w) => w - 1)} aria-label="Previous week">← Prev</button>
              <span className="px-2">Week {week + 1}</span>
              <button className="rounded bg-gray-200 px-2 py-1" onClick={() => setWeekOffset((w) => w + 1)} aria-label="Next week">Next →</button>
            </div>
          }
        />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Schedule</CardTitle>
          </CardHeader>
          {members.isLoading && <Skeleton className="h-16 w-full" />}
          {members.isError && (
            <p className="text-sm text-red-600">{members.error.message}</p>
          )}
          {!members.isLoading && members.data && members.data.items.length === 0 && (
            <EmptyState title="No teams" description="Add managers to this league to see matchups." />
          )}
          {pairings.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              {pairings.map(([a, b], i) => (
                <div key={`${a}-${b ?? "bye"}-${i}`} className="surface rounded-[var(--radius-md)] p-3">
                  {b ? (
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">
                          <Link className="underline underline-offset-2" href={`/teams/${a}`}>Team {a.slice(0, 6)}</Link>
                          <span className="mx-2 text-[var(--color-muted)]">vs</span>
                          <Link className="underline underline-offset-2" href={`/teams/${b}`}>Team {b.slice(0, 6)}</Link>
                        </div>
                        <div className="text-xs text-[var(--color-muted)]">Projected: {projectedPoints(a)} – {projectedPoints(b)}</div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-medium">{new Date().toLocaleDateString()}</div>
                        <div className="text-[var(--color-muted)] text-xs">7:00 PM</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm">Team {a.slice(0, 6)} — Bye</div>
                  )}
                </div>
              ))}
            </div>
          )}
          <div className="text-xs text-gray-600">Data: /leagues/{"{leagueId}"}/members (pairings generated client-side)</div>
        </Card>
      </div>
    </main>
  );
}

