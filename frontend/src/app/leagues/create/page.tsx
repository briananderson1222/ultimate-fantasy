"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";
import { API_BASE, apiFetch } from "../../../services/client";

type LeagueCreate = {
  name: string;
  sport: string;
  league_type: string;
  season: string;
};

type LeagueResponse = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  invite_link?: string | null;
};

export default function CreateLeaguePage() {
  const [userId, setUserId] = useState("");
  const [form, setForm] = useState<LeagueCreate>({
    name: "My League",
    sport: "nba",
    league_type: "redraft",
    season: new Date().getFullYear().toString(),
  });

  const defaultUser = useMemo(
    () => (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : ""),
    []
  );

  const createLeague = useMutation({
    mutationFn: async ({ data, user }: { data: LeagueCreate; user: string }) => {
      return await apiFetch<LeagueResponse>(`/leagues`, {
        method: "POST",
        headers: {
          "x-user-id": user,
        },
        body: JSON.stringify(data),
      });
    },
  });

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <h1 className="text-2xl font-semibold">Create League</h1>

        <div className="rounded-md border p-4 space-y-4">
          <div className="space-y-1">
            <label className="block text-sm text-gray-700">User ID (UUID)</label>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder={defaultUser || "00000000-0000-0000-0000-000000000001"}
              className="w-full rounded border px-3 py-2"
            />
            <p className="text-xs text-gray-500">Required header for authenticated actions.</p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-gray-700">Name</label>
              <input
                className="w-full rounded border px-3 py-2"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">Sport</label>
              <input
                className="w-full rounded border px-3 py-2"
                value={form.sport}
                onChange={(e) => setForm({ ...form, sport: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">League Type</label>
              <input
                className="w-full rounded border px-3 py-2"
                value={form.league_type}
                onChange={(e) => setForm({ ...form, league_type: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">Season</label>
              <input
                className="w-full rounded border px-3 py-2"
                value={form.season}
                onChange={(e) => setForm({ ...form, season: e.target.value })}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
              disabled={createLeague.isPending || !userId}
              onClick={() => createLeague.mutate({ data: form, user: userId })}
            >
              {createLeague.isPending ? "Creating..." : "Create"}
            </button>
            <span className="text-xs text-gray-500">API: {API_BASE || "/"} /leagues</span>
          </div>

          {createLeague.isError && (
            <p className="text-sm text-red-600">{(createLeague.error as Error)?.message}</p>
          )}

          {createLeague.data && (
            <div className="rounded bg-green-50 p-3 text-green-800">
              <p className="font-medium">League Created</p>
              <p className="text-sm">ID: {createLeague.data.league_id}</p>
              <div className="mt-2 flex gap-2">
                <Link
                  className="underline text-blue-700"
                  href={`/leagues/${createLeague.data.league_id}`}
                >
                  View Public Page
                </Link>
                {createLeague.data.invite_link && <span>{createLeague.data.invite_link}</span>}
              </div>
            </div>
          )}
        </div>

        <Link className="text-blue-700 underline" href="/leagues">Back to Leagues</Link>
      </div>
    </main>
  );
}
