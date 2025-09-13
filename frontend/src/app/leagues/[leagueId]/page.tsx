"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { API_BASE } from "../../../services/client";
import { getPublicLeague, joinLeague } from "../../../services/api";
import DevAuthToken from "../../../components/DevAuthToken";

type LeaguePublic = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
};

type JoinResponse = {
  team_id: string;
  league_id: string;
  user_id: string;
  team_name: string;
};

export default function LeaguePublicPage() {
  const params = useParams<{ leagueId: string }>();
  const leagueId = params?.leagueId;

  const info = useQuery({
    queryKey: ["league", leagueId],
    queryFn: async () => {
      if (!leagueId) throw new Error("missing league id");
      return await getPublicLeague(leagueId);
    },
    enabled: !!leagueId,
  });

  const join = useMutation({
    mutationFn: async () => {
      if (!leagueId) throw new Error("missing league id");
      return await joinLeague(leagueId);
    },
  });

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">League</h1>
          <Link className="text-blue-700 underline" href="/leagues">
            Back
          </Link>
        </div>

        {info.isLoading && <p>Loading...</p>}
        {info.isError && (
          <p className="text-sm text-red-600">{(info.error as Error)?.message}</p>
        )}
        {info.data && (
          <div className="space-y-1 rounded border p-4">
            <div className="text-lg font-medium">{info.data.name}</div>
            <div className="text-gray-600 text-sm">
              {info.data.sport} • {info.data.league_type} • {info.data.season}
            </div>
          </div>
        )}

        <div className="rounded border p-4 space-y-3">
          <h2 className="font-medium">Join this league</h2>
          <p className="text-xs text-gray-500">Uses Authorization: Bearer from localStorage key <code>uf_token</code>.</p>
          <div className="flex items-center gap-2">
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
              disabled={join.isPending}
              onClick={() => join.mutate()}
            >
              {join.isPending ? "Joining..." : "Join"}
            </button>
            <span className="text-xs text-gray-500">API: {API_BASE || "/"} /leagues/{leagueId}/join</span>
          </div>
          {join.isError && (
            <p className="text-sm text-red-600">{(join.error as Error)?.message}</p>
          )}
          {join.data && (
            <div className="rounded bg-green-50 p-3 text-green-800">
              <p className="font-medium">Joined as {join.data.team_name}</p>
              <p className="text-sm">Team ID: {join.data.team_id}</p>
            </div>
          )}
        </div>

        <DevAuthToken />
      </div>
    </main>
  );
}
