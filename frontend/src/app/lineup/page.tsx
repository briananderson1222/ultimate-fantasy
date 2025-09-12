"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { API_BASE, apiFetch } from "../../services/client";

type LineupPlayer = { player_id: string; position: string };
type LineupRequest = { team_id: string; game_day: string; players: LineupPlayer[] };
type LineupResponse = { team_id: string; game_day: string; players: LineupPlayer[]; version?: number | null };

export default function LineupPage() {
  const [userId, setUserId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [gameDay, setGameDay] = useState<string>(new Date().toISOString().slice(0, 10));
  const [players, setPlayers] = useState<LineupPlayer[]>([
    { player_id: "", position: "" },
  ]);

  const setLineup = useMutation({
    mutationFn: async (payload: LineupRequest) => {
      return await apiFetch<LineupResponse>(`/lineups`, {
        method: "PUT",
        headers: { "x-user-id": userId },
        body: JSON.stringify(payload),
      });
    },
  });

  const updatePlayer = (idx: number, field: keyof LineupPlayer, value: string) => {
    setPlayers((prev) => prev.map((p, i) => (i === idx ? { ...p, [field]: value } : p)));
  };

  const addPlayer = () => setPlayers((prev) => [...prev, { player_id: "", position: "" }]);
  const removePlayer = (idx: number) => setPlayers((prev) => prev.filter((_, i) => i !== idx));

  const submit = () => {
    const payload: LineupRequest = { team_id: teamId, game_day: gameDay, players };
    setLineup.mutate(payload);
  };

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <h1 className="text-2xl font-semibold">Set Lineup</h1>

        <div className="rounded border p-4 space-y-3">
          <div>
            <label className="mb-1 block text-sm text-gray-700">User ID (UUID)</label>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="00000000-0000-0000-0000-000000000001"
              className="w-full rounded border px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-700">Team ID (UUID)</label>
            <input
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              placeholder="team uuid"
              className="w-full rounded border px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-700">Game Day</label>
            <input
              type="date"
              value={gameDay}
              onChange={(e) => setGameDay(e.target.value)}
              className="w-full rounded border px-3 py-2"
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Players</h2>
              <button className="rounded bg-gray-200 px-3 py-1" onClick={addPlayer}>
                Add Player
              </button>
            </div>
            {players.map((p, idx) => (
              <div key={idx} className="flex gap-2">
                <input
                  value={p.player_id}
                  onChange={(e) => updatePlayer(idx, "player_id", e.target.value)}
                  placeholder="player uuid"
                  className="flex-1 rounded border px-3 py-2"
                />
                <input
                  value={p.position}
                  onChange={(e) => updatePlayer(idx, "position", e.target.value)}
                  placeholder="position (e.g., PG)"
                  className="w-40 rounded border px-3 py-2"
                />
                <button
                  className="rounded bg-red-100 px-3 py-2 text-red-700"
                  onClick={() => removePlayer(idx)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
              disabled={!userId || !teamId || setLineup.isPending}
              onClick={submit}
            >
              {setLineup.isPending ? "Saving..." : "Save Lineup"}
            </button>
            <span className="text-xs text-gray-500">API: {API_BASE || "/"} /lineups</span>
          </div>
          {setLineup.isError && (
            <p className="text-sm text-red-600">{(setLineup.error as Error)?.message}</p>
          )}
          {setLineup.data && (
            <div className="rounded bg-green-50 p-3 text-green-800">
              <p className="font-medium">Lineup Saved (version {setLineup.data.version ?? "n/a"})</p>
              <p className="text-sm">
                Team {setLineup.data.team_id} for {setLineup.data.game_day}
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
