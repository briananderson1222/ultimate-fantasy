"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle } from "../../../components/ui/card";
import { Skeleton } from "../../../components/ui/skeleton";
import { EmptyState } from "../../../components/ui/empty-state";
import { PageHeader } from "../../../components/ui/page-header";
import { Badge } from "../../../components/ui/badge";
import {
  listLineups,
  getMyLeagues,
  getLeagueMembers,
  type LineupListResponse,
  type MembersResponse,
  type MeLeaguesResponse,
} from "../../../services/api";
import { useMemo } from "react";

export default function TeamPage() {
  const params = useParams<{ teamId: string }>();
  const teamId = params?.teamId;

  const lineups = useQuery<LineupListResponse, Error>({
    queryKey: ["lineups", { team_id: teamId, limit: 1, offset: 0 }],
    queryFn: () => {
      if (!teamId) throw new Error("teamId is required");
      return listLineups({ team_id: teamId, limit: 1, offset: 0 });
    },
    enabled: !!teamId,
  });

  const myLeagues = useQuery<MeLeaguesResponse, Error>({
    queryKey: ["myLeagues"],
    queryFn: () => getMyLeagues(),
  });

  const leagueId = useMemo(() => {
    if (!teamId || !myLeagues.data) return undefined;
    return myLeagues.data.items.find((it) => String(it.team_id) === String(teamId))?.league_id;
  }, [teamId, myLeagues.data]);

  const members = useQuery<MembersResponse, Error>({
    queryKey: ["leagueMembers", leagueId],
    queryFn: () => {
      if (!leagueId) throw new Error("leagueId is required");
      return getLeagueMembers(String(leagueId));
    },
    enabled: !!leagueId,
  });

  const latest = lineups.data?.items?.[0];

  const projection = useMemo(() => {
    // Simple deterministic pseudo-projection based on teamId and roster length
    const count = latest?.players?.length ?? 0;
    const seedStr = String(teamId || "") + (latest?.game_day || "");
    let seed = 0;
    for (let i = 0; i < seedStr.length; i++) seed = (seed * 31 + seedStr.charCodeAt(i)) % 1000;
    const base = 7 * count; // base per-player
    const noise = (seed % 250) / 10; // 0..25.0
    const conf = 60 + (seed % 30); // 60..89
    return { points: Math.round((base + noise) * 10) / 10, confidence: conf };
  }, [teamId, latest?.players, latest?.game_day]);

  const upcoming = useMemo(() => {
    if (!leagueId || !members.data) return null;
    const teams = members.data.items.map((m) => String(m.team_id)).sort();
    const idx = teams.indexOf(String(teamId));
    if (idx === -1) return null;
    // Pair by rotating list by week number and chunking into pairs
    const now = new Date();
    const week = Math.floor(+now / (1000 * 60 * 60 * 24 * 7)) % Math.max(1, teams.length);
    const rotated = teams.map((_, i) => teams[(i + week) % teams.length]);
    const pairs: Array<[string, string | null]> = [];
    for (let i = 0; i < rotated.length; i += 2) {
      const a = rotated[i];
      const b = rotated[i + 1] ?? null; // bye if odd
      pairs.push([a, b]);
    }
    const pair = pairs.find(([a, b]) => a === String(teamId) || b === String(teamId));
    if (!pair) return null;
    const [a, b] = pair;
    const opponent = a === String(teamId) ? b : a;
    return opponent ? { opponent, week } : { opponent: null, week };
  }, [leagueId, members.data, teamId]);

  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <PageHeader
          title="Team"
          actions={
            leagueId ? (
              <Link
                className="text-blue-700 underline px-2 py-1 rounded focus-visible:ring-2 focus-visible:ring-offset-2"
                href={`/leagues/${leagueId}/matchups`}
              >
                View Matchups
              </Link>
            ) : null
          }
        />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Roster</CardTitle>
          </CardHeader>
          {lineups.isLoading && <Skeleton className="h-16 w-full" />}
          {lineups.isError && <p className="text-sm text-red-600">{lineups.error.message}</p>}
          {latest && (
            <ul className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              {latest.players.map((p, idx) => (
                <li
                  key={`${p.player_id}-${idx}`}
                  className="surface rounded-[var(--radius-md)] p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">
                        {String(p.player_id).slice(0, 8)}
                      </div>
                      <div className="text-xs text-[var(--color-muted)]">
                        ID: {String(p.player_id)}
                      </div>
                    </div>
                    <Badge variant="secondary">{p.position?.toUpperCase() || "POS"}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {!latest && !lineups.isLoading && (
            <EmptyState
              title="No roster yet"
              description="Save a lineup to populate your roster."
            />
          )}
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="space-y-2">
            <CardHeader>
              <CardTitle>Upcoming Matchup</CardTitle>
            </CardHeader>
            {!leagueId && <p className="text-sm text-gray-600">Link a league to see matchups.</p>}
            {members.isLoading && <Skeleton className="h-10 w-full" />}
            {members.isError && <p className="text-sm text-red-600">{members.error.message}</p>}
            {leagueId && upcoming && (
              <div className="rounded border p-3">
                {upcoming.opponent ? (
                  <div className="flex items-center justify-between">
                    <div className="text-sm">
                      <div className="font-medium">Week {upcoming.week + 1}</div>
                      <div className="text-gray-600">
                        Team {String(teamId).slice(0, 6)} vs Team{" "}
                        {String(upcoming.opponent).slice(0, 6)}
                      </div>
                    </div>
                    <Link
                      className="text-blue-700 underline"
                      href={`/leagues/${leagueId}/matchups`}
                    >
                      Details
                    </Link>
                  </div>
                ) : (
                  <div className="text-sm text-gray-700">Bye week</div>
                )}
              </div>
            )}
          </Card>

          <Card className="space-y-2">
            <CardHeader>
              <CardTitle>Projection</CardTitle>
            </CardHeader>
            <div className="rounded border p-3">
              <div className="text-2xl font-semibold">{projection.points.toFixed(1)} pts</div>
              <div className="text-sm text-gray-600">Confidence: {projection.confidence}%</div>
              <div className="mt-2 text-xs text-gray-500">
                Based on roster size and form. For demo purposes only.
              </div>
            </div>
          </Card>
        </div>

        {leagueId && (
          <div className="text-xs text-gray-600">
            Data: /lineups?team_id=..., /me/leagues, /leagues/{"{leagueId}"}/members
          </div>
        )}
      </div>
    </div>
  );
}
