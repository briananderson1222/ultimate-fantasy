"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, useRef, useCallback } from "react";
import { API_BASE } from "../../services/client";
import { setLineup as apiSetLineup, listLineups } from "../../services/api";
import { Skeleton } from "../../components/ui/skeleton";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { z } from "zod";
import { useToast } from "../../components/ui/toast";
import { Plus, Save, Copy, GripVertical, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";
import OnboardingTour from "../../components/OnboardingTour";

type LineupPlayer = { player_id: string; position: string; projected_points?: number };
type LineupRequest = { team_id: string; game_day: string; players: LineupPlayer[] };
type LineupResponse = {
  team_id: string;
  game_day: string;
  players: LineupPlayer[];
  version?: number | null;
};

// Position constraints for different sports
const POSITION_CONFIGS = {
  NBA: {
    required: [
      { position: "PG", min: 1, max: 2, label: "Point Guard" },
      { position: "SG", min: 1, max: 2, label: "Shooting Guard" },
      { position: "SF", min: 1, max: 2, label: "Small Forward" },
      { position: "PF", min: 1, max: 2, label: "Power Forward" },
      { position: "C", min: 1, max: 2, label: "Center" },
      { position: "UTIL", min: 1, max: 3, label: "Utility" },
    ],
    total: { min: 8, max: 10 }
  },
  NFL: {
    required: [
      { position: "QB", min: 1, max: 1, label: "Quarterback" },
      { position: "RB", min: 2, max: 3, label: "Running Back" },
      { position: "WR", min: 3, max: 4, label: "Wide Receiver" },
      { position: "TE", min: 1, max: 2, label: "Tight End" },
      { position: "FLEX", min: 1, max: 2, label: "Flex" },
      { position: "K", min: 1, max: 1, label: "Kicker" },
      { position: "DST", min: 1, max: 1, label: "Defense" },
    ],
    total: { min: 9, max: 9 }
  }
};

type DragItem = {
  index: number;
  type: string;
};

export default function LineupPage() {
  const queryClient = useQueryClient();
  const [teamId, setTeamId] = useState("");
  const [gameDay, setGameDay] = useState<string>(new Date().toISOString().slice(0, 10));
  const [sport, setSport] = useState<keyof typeof POSITION_CONFIGS>("NBA");
  const [players, setPlayers] = useState<LineupPlayer[]>([{ player_id: "", position: "", projected_points: 0 }]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [lastSavedKey, setLastSavedKey] = useState<string | null>(null);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [optimizeMode, setOptimizeMode] = useState(false);
  const toast = useToast();
  const [tourOpen, setTourOpen] = useState(false);
  const dragOverIndex = useRef<number | null>(null);

  // Position validation
  const positionConfig = POSITION_CONFIGS[sport];
  const positionValidation = useMemo(() => {
    const counts: Record<string, number> = {};
    players.forEach(p => {
      if (p.position) {
        counts[p.position] = (counts[p.position] || 0) + 1;
      }
    });

    const violations: string[] = [];
    positionConfig.required.forEach(req => {
      const count = counts[req.position] || 0;
      if (count < req.min) {
        violations.push(`Need at least ${req.min} ${req.label}${req.min > 1 ? 's' : ''} (have ${count})`);
      }
      if (count > req.max) {
        violations.push(`Too many ${req.label}s: ${count}/${req.max}`);
      }
    });

    const total = players.filter(p => p.position && p.player_id).length;
    if (total < positionConfig.total.min) {
      violations.push(`Need at least ${positionConfig.total.min} players (have ${total})`);
    }
    if (total > positionConfig.total.max) {
      violations.push(`Too many players: ${total}/${positionConfig.total.max}`);
    }

    return { counts, violations, isValid: violations.length === 0 };
  }, [players, positionConfig]);

  // Drag and drop handlers
  const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', '');
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    dragOverIndex.current = index;
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    dragOverIndex.current = null;
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    const dragIndex = draggedIndex;

    if (dragIndex === null || dragIndex === dropIndex) return;

    setPlayers(prev => {
      const newPlayers = [...prev];
      const [draggedPlayer] = newPlayers.splice(dragIndex, 1);
      newPlayers.splice(dropIndex, 0, draggedPlayer);
      return newPlayers;
    });

    setDraggedIndex(null);
    dragOverIndex.current = null;
  }, [draggedIndex]);

  // Auto-optimize lineup based on projected points
  const optimizeLineup = useCallback(() => {
    const sortedPlayers = [...players].sort((a, b) => (b.projected_points || 0) - (a.projected_points || 0));
    setPlayers(sortedPlayers);
    toast.show({ title: "Lineup optimized", description: "Players sorted by projected points" });
  }, [players, toast]);

  const setLineup = useMutation({
    mutationFn: async (payload: LineupRequest) => {
      return await apiSetLineup(payload);
    },
    // Optimistic update: update the cached list of lineups for this team/day
    onMutate: async (payload: LineupRequest) => {
      const key = [
        "lineups",
        { team_id: payload.team_id, game_day: payload.game_day || undefined, limit: 50, offset: 0 },
      ];
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<any>(key);
      const optimisticItem = {
        lineup_id: `optimistic-${Date.now()}`,
        team_id: payload.team_id,
        game_day: payload.game_day,
        players: payload.players,
        version: (previous?.items?.[0]?.version ?? 0) + 1,
      };
      if (previous && Array.isArray(previous.items)) {
        queryClient.setQueryData(key, { items: [optimisticItem, ...previous.items] });
      } else {
        queryClient.setQueryData(key, { items: [optimisticItem] });
      }
      return { key, previous } as { key: unknown[]; previous: any };
    },
    onError: (_err, _vars, context) => {
      if (context?.key) queryClient.setQueryData(context.key as any, context.previous);
    },
    onSettled: (_data, _error, _vars, context) => {
      if (context?.key) queryClient.invalidateQueries({ queryKey: context.key as any });
    },
  });

  const updatePlayer = (idx: number, field: keyof LineupPlayer, value: string | number) => {
    setPlayers((prev) => prev.map((p, i) => (i === idx ? { ...p, [field]: value } : p)));
  };

  const addPlayer = () => setPlayers((prev) => [...prev, { player_id: "", position: "", projected_points: 0 }]);
  const removePlayer = (idx: number) => setPlayers((prev) => prev.filter((_, i) => i !== idx));

  const keyFor = (t: string, d: string, ps: LineupPlayer[]) =>
    `${t}|${d}|` + ps.map((p) => `${p.player_id}:${p.position}`).join(",");

  const schema = z.object({
    team_id: z.string().min(1, "Team ID is required"),
    game_day: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Game day must be YYYY-MM-DD"),
    players: z
      .array(
        z.object({
          player_id: z.string().min(1, "Player ID is required"),
          position: z.string().min(1, "Position is required"),
        }),
      )
      .min(1, "At least one player is required"),
  });

  const submit = () => {
    const parsed = schema.safeParse({ team_id: teamId, game_day: gameDay, players });
    if (!parsed.success) {
      const es: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const path = issue.path.join(".");
        es[path] = issue.message;
      }
      setErrors(es);
      return;
    }
    setErrors({});
    const payload: LineupRequest = parsed.data;
    setLineup.mutate(payload, {
      onSuccess: (data) => {
        setLastSavedKey(keyFor(teamId, gameDay, players));
        toast.show({ title: "Lineup saved", description: `${data.game_day}` });
      },
      onError: (err: any) => {
        toast.show({ title: "Failed to save", description: String(err?.message || err) });
      },
    });
  };

  const lineups = useQuery({
    queryKey: [
      "lineups",
      { team_id: teamId, game_day: gameDay || undefined, limit: 50, offset: 0 },
    ],
    queryFn: () =>
      listLineups({ team_id: teamId, game_day: gameDay || undefined, limit: 50, offset: 0 }),
    enabled: !!teamId,
  });

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title="Set Lineup" />

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Lineup Builder
              <div className="flex items-center gap-2">
                {!positionValidation.isValid && (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={optimizeLineup}
                  leftIcon={<TrendingUp className="h-4 w-4" />}
                >
                  Optimize
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <p className="text-xs text-gray-600">
            Uses Authorization: Bearer from localStorage key <code>uf_token</code>.
          </p>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm text-gray-700">Sport</label>
              <select
                value={sport}
                onChange={(e) => setSport(e.target.value as keyof typeof POSITION_CONFIGS)}
                className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
              >
                <option value="NBA">NBA Basketball</option>
                <option value="NFL">NFL Football</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">Team ID (UUID)</label>
              <input
                id="team-id-input"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
                placeholder="team uuid"
                className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                aria-invalid={errors.team_id ? true : undefined}
                aria-describedby={errors.team_id ? "team-id-error" : undefined}
              />
              {errors.team_id && (
                <p id="team-id-error" className="text-xs text-red-600">
                  {errors.team_id}
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-700">Game Day</label>
              <input
                type="date"
                value={gameDay}
                onChange={(e) => setGameDay(e.target.value)}
                className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                aria-invalid={errors.game_day ? true : undefined}
                aria-describedby={errors.game_day ? "game-day-error" : undefined}
              />
              {errors.game_day && (
                <p id="game-day-error" className="text-xs text-red-600">
                  {errors.game_day}
                </p>
              )}
            </div>
          </div>

          {/* Position Requirements */}
          <div className="bg-gray-50 rounded-lg p-3">
            <h3 className="text-sm font-medium mb-2">Position Requirements ({sport})</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {positionConfig.required.map(req => {
                const count = positionValidation.counts[req.position] || 0;
                const isValid = count >= req.min && count <= req.max;
                return (
                  <div key={req.position} className={`flex items-center justify-between p-2 rounded ${
                    isValid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    <span>{req.position}</span>
                    <span>{count}/{req.min}-{req.max}</span>
                  </div>
                );
              })}
            </div>
            {positionValidation.violations.length > 0 && (
              <div className="mt-2">
                <ul className="text-xs text-red-600 space-y-1">
                  {positionValidation.violations.map((violation, i) => (
                    <li key={i} className="flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {violation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Players (Drag to reorder)</h2>
              <button
                className="inline-flex items-center gap-2 rounded bg-[var(--color-surface)] border border-[var(--border)] px-3 py-1 text-[var(--color-text)] hover:bg-[var(--color-elevated)]"
                onClick={addPlayer}
              >
                <Plus className="h-4 w-4" aria-hidden />
                <span>Add Player</span>
              </button>
            </div>
            {players.map((p, idx) => (
              <div
                key={idx}
                className={`flex gap-2 p-3 rounded-lg border transition-all ${
                  draggedIndex === idx
                    ? 'bg-blue-50 border-blue-200 shadow-lg scale-105'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
                draggable
                onDragStart={(e) => handleDragStart(e, idx)}
                onDragOver={(e) => handleDragOver(e, idx)}
                onDragEnd={handleDragEnd}
                onDrop={(e) => handleDrop(e, idx)}
              >
                <div className="flex items-center cursor-move">
                  <GripVertical className="h-5 w-5 text-gray-400" />
                </div>

                <div className="flex-1">
                  <label htmlFor={`player-${idx}-id`} className="sr-only">
                    Player ID {idx + 1}
                  </label>
                  <input
                    id={`player-${idx}-id`}
                    value={p.player_id}
                    onChange={(e) => updatePlayer(idx, "player_id", e.target.value)}
                    placeholder="player uuid"
                    className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                    aria-invalid={errors[`players.${idx}.player_id`] ? true : undefined}
                    aria-describedby={
                      errors[`players.${idx}.player_id`]
                        ? `players-${idx}-player-id-error`
                        : undefined
                    }
                  />
                </div>

                <div className="w-32">
                  <label htmlFor={`player-${idx}-pos`} className="sr-only">
                    Position {idx + 1}
                  </label>
                  <select
                    id={`player-${idx}-pos`}
                    value={p.position}
                    onChange={(e) => updatePlayer(idx, "position", e.target.value)}
                    className="w-full rounded border px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                    aria-invalid={errors[`players.${idx}.position`] ? true : undefined}
                    aria-describedby={
                      errors[`players.${idx}.position`]
                        ? `players-${idx}-position-error`
                        : undefined
                    }
                  >
                    <option value="">Select...</option>
                    {positionConfig.required.map(req => (
                      <option key={req.position} value={req.position}>
                        {req.position} - {req.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="w-24">
                  <label htmlFor={`player-${idx}-points`} className="sr-only">
                    Projected Points {idx + 1}
                  </label>
                  <input
                    id={`player-${idx}-points`}
                    type="number"
                    step="0.1"
                    value={p.projected_points || 0}
                    onChange={(e) => updatePlayer(idx, "projected_points", parseFloat(e.target.value) || 0)}
                    placeholder="0.0"
                    className="w-full rounded border px-3 py-2 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                  />
                  <div className="text-xs text-gray-500 text-center mt-1">Points</div>
                </div>

                <div className="flex items-center">
                  {p.position ? (
                    <Badge variant="secondary">{p.position.toUpperCase()}</Badge>
                  ) : (
                    <Badge variant="secondary">POS</Badge>
                  )}
                </div>

                <button
                  className="rounded bg-red-100 border border-red-300 px-3 py-2 text-red-700 hover:bg-red-200 transition-colors"
                  onClick={() => removePlayer(idx)}
                  aria-label={`Remove player ${idx + 1}`}
                >
                  Remove
                </button>
              </div>
            ))}
            {players.map((p, idx) => (
              <div key={`errs-${idx}`} className="-mt-1 mb-1 grid grid-cols-2 gap-2 text-xs">
                <div className="text-red-600" id={`players-${idx}-player-id-error`}>
                  {errors[`players.${idx}.player_id`]}
                </div>
                <div className="text-red-600" id={`players-${idx}-position-error`}>
                  {errors[`players.${idx}.position`]}
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Button
              disabled={!teamId || setLineup.isPending || !positionValidation.isValid}
              loading={setLineup.isPending}
              onClick={submit}
              data-tour="save-lineup"
              leftIcon={<Save className="h-4 w-4" aria-hidden />}
            >
              Save Lineup
            </Button>
            {!positionValidation.isValid && (
              <span className="text-xs text-red-600">Fix position violations to save</span>
            )}
            <Button
              variant="secondary"
              onClick={async () => {
                if (!teamId) {
                  setErrors((e) => ({ ...e, team_id: "Team ID is required" }));
                  return;
                }
                const d = new Date(gameDay);
                d.setDate(d.getDate() - 1);
                const y = d.toISOString().slice(0, 10);
                try {
                  const res = await listLineups({
                    team_id: teamId,
                    game_day: y,
                    limit: 1,
                    offset: 0,
                  });
                  const latest = res.items[0];
                  if (latest) {
                    setPlayers(latest.players);
                    toast.show({ title: "Copied lineup", description: y });
                  } else {
                    toast.show({ title: "No lineup to copy", description: y });
                  }
                } catch (err: any) {
                  toast.show({ title: "Copy failed", description: String(err?.message || err) });
                }
              }}
            >
              <span className="inline-flex items-center gap-2">
                <Copy className="h-4 w-4" aria-hidden />
                Copy Yesterday
              </span>
            </Button>
            <span className="text-xs text-gray-600">API: {API_BASE || "/"} /lineups</span>
          </div>
          {setLineup.isError && (
            <p className="text-sm text-red-600">{(setLineup.error as Error)?.message}</p>
          )}
          <div className="flex items-center gap-2">
            {lastSavedKey === keyFor(teamId, gameDay, players) && (
              <span className="text-xs text-green-700" aria-live="polite">
                Saved
              </span>
            )}
          </div>
        </Card>
        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Existing Lineups</CardTitle>
          </CardHeader>
          {!teamId && <p className="text-sm text-gray-600">Enter a Team ID to view lineups.</p>}
          {lineups.isLoading && <Skeleton className="h-16 w-full" />}
          {lineups.isError && (
            <p className="text-sm text-red-600">{(lineups.error as Error)?.message}</p>
          )}
          {lineups.data && (
            <ul className="text-sm divide-y">
              {lineups.data.items.map((it) => (
                <li key={it.lineup_id} className="py-2 flex items-center justify-between">
                  <div>
                    <div className="font-medium">
                      {it.game_day} (v{it.version})
                    </div>
                    <div className="text-xs text-gray-600">Players: {it.players.length}</div>
                  </div>
                </li>
              ))}
              {lineups.data.items.length === 0 && (
                <li className="py-2">
                  <EmptyState
                    title="No lineups found"
                    description="Save a lineup and it will appear here."
                  />
                </li>
              )}
            </ul>
          )}
          <span className="text-xs text-gray-600">API: /lineups?team_id=...&game_day=...</span>
        </Card>
      </div>
      <div className="fixed bottom-4 right-4">
        <button
          className="rounded bg-[var(--color-surface)] border border-[var(--border)] px-3 py-1 text-sm text-[var(--color-text)] hover:bg-[var(--color-elevated)]"
          onClick={() => setTourOpen(true)}
        >
          Start tour
        </button>
      </div>
      <OnboardingTour
        id="lineup"
        steps={[
          {
            selector: "#team-id-input",
            title: "Team ID",
            content: "Enter your Team UUID to fetch and save lineups.",
          },
          {
            selector: '[data-tour="save-lineup"]',
            title: "Save your lineup",
            content: "Click Save to persist changes and see Saved indicator.",
          },
        ]}
        open={tourOpen}
        onClose={() => setTourOpen(false)}
      />
    </main>
  );
}
