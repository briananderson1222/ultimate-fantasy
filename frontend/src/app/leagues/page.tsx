"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import DevAuthToken from "../../components/DevAuthToken";

export default function LeaguesListPage() {
  const router = useRouter();
  const [leagueId, setLeagueId] = useState("");

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <h1 className="text-2xl font-semibold">Leagues</h1>
        <p className="text-gray-600">
          A simple hub page. Listing leagues is not defined in the API yet.
        </p>

        <div className="space-x-3">
          <Link
            className="rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
            href="/leagues/create"
          >
            Create League
          </Link>
        </div>

        <div className="rounded-md border p-4">
          <h2 className="mb-2 font-medium">Go to a league by ID</h2>
          <div className="flex gap-2">
            <input
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
              placeholder="League UUID"
              className="w-full rounded border px-3 py-2"
            />
            <button
              className="rounded bg-gray-800 px-3 py-2 text-white disabled:opacity-50"
              disabled={!leagueId}
              onClick={() => router.push(`/leagues/${leagueId}`)}
            >
              Open
            </button>
          </div>
        </div>

        <DevAuthToken />
      </div>
    </main>
  );
}
