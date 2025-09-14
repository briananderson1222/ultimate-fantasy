"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import DevAuthToken from "../../components/DevAuthToken";
import { getMyLeagues } from "../../services/api";
import { Skeleton } from "../../components/ui/skeleton";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Button } from "../../components/ui/button";
import { Plus } from "lucide-react";

export default function LeaguesListPage() {
  const router = useRouter();
  const [leagueId, setLeagueId] = useState("");

  const leagues = useQuery({
    queryKey: ["myLeagues"],
    queryFn: getMyLeagues,
  });

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader
          title="Leagues"
          actions={<Link href="/leagues/create"><Button leftIcon={<Plus className="h-4 w-4" aria-hidden />} >Create League</Button></Link>}
        />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>My Leagues</CardTitle>
          </CardHeader>
          {leagues.isLoading && <Skeleton className="h-16 w-full" />}
          {leagues.isError && (
            <div className="text-sm text-red-700 flex items-center justify-between">
              <span>{(leagues.error as Error)?.message}</span>
              <button
                className="rounded bg-gray-800 px-3 py-1 text-white"
                onClick={() => leagues.refetch()}
              >
                Retry
              </button>
            </div>
          )}
          {leagues.data && (
            <ul className="divide-y text-sm">
              {leagues.data.items.map((it) => (
                <li key={it.team_id} className="flex items-center justify-between py-2">
                  <div>
                    <div className="font-medium">{it.name}</div>
                    <div className="text-gray-600 text-xs">Season {it.season}</div>
                  </div>
                  <Link className="text-blue-700 underline px-2 py-1 rounded focus-visible:ring-2 focus-visible:ring-offset-2" href={`/leagues/${it.league_id}`}>
                    Open
                  </Link>
                </li>
              ))}
              {leagues.data.items.length === 0 && (
                <li className="py-2">
                  <EmptyState
                    title="No leagues yet"
                    description="Create a league or paste a League ID below to jump into one."
                    action={<Link className="text-blue-700 underline" href="/leagues/create">Create a League</Link>}
                  />
                </li>
              )}
            </ul>
          )}
          <span className="text-xs text-gray-600">API: /me/leagues</span>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Go to a league by ID</CardTitle>
          </CardHeader>
          <div className="flex gap-2">
            <div className="flex-1">
              <label htmlFor="league-id-input" className="mb-1 block text-sm text-gray-700">League ID</label>
              <input
                id="league-id-input"
                value={leagueId}
                onChange={(e) => setLeagueId(e.target.value)}
                placeholder="League UUID"
                className="w-full rounded border px-3 py-2"
              />
            </div>
            <button
              className="rounded bg-gray-800 px-3 py-2 min-h-12 text-white disabled:opacity-50"
              disabled={!leagueId}
              onClick={() => router.push(`/leagues/${leagueId}`)}
            >
              Open
            </button>
          </div>
        </Card>

        <DevAuthToken />
      </div>
    </main>
  );
}
