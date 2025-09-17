"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { API_BASE } from "../../services/client";
import { placeWaiverBid, listWaivers } from "../../services/api";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { useToast } from "../../components/ui/toast";
import { Skeleton } from "../../components/ui/skeleton";
import { Card, CardHeader, CardTitle } from "../../components/ui/card";
import { EmptyState } from "../../components/ui/empty-state";
import { PageHeader } from "../../components/ui/page-header";
import { Badge } from "../../components/ui/badge";
import {
  CircleDollarSign,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import { usePreferences } from "../../lib/preferences";

export default function WaiversPage() {
  const { preferences, setLayouts } = usePreferences();
  const [leagueId, setLeagueId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [playerId, setPlayerId] = useState("");
  const [bid, setBid] = useState<number>(0);
  const [limit, setLimit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "won" | "lost" | "expired">(
    "all",
  );
  const [sortKey, setSortKey] = useState<"bid" | "status">("bid");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const toast = useToast();
  const qc = useQueryClient();

  const listArgs = useMemo(
    () => ({ league_id: leagueId, team_id: teamId || undefined, limit, offset }),
    [leagueId, teamId, limit, offset],
  );
  const waivers = useQuery({
    queryKey: ["waivers", listArgs],
    queryFn: () => listWaivers(listArgs),
    enabled: !!leagueId,
  });

  const placeBid = useMutation({
    mutationFn: async () =>
      placeWaiverBid({ league_id: leagueId, team_id: teamId, player_id: playerId, bid }),
    onSuccess: () => {
      toast.show({ title: "Bid placed", description: `Bid ${bid}` });
      qc.invalidateQueries({ queryKey: ["waivers", listArgs] });
    },
    onError: (err: any) =>
      toast.show({ title: "Bid failed", description: String(err?.message || err) }),
  });

  const disabled = !leagueId || !teamId || !playerId || bid < 0 || placeBid.isPending;

  // Load saved preferences for waivers view
  const prefLoaded = useRef(false);
  useEffect(() => {
    if (prefLoaded.current) return;
    prefLoaded.current = true;
    const saved = (preferences.layouts as any)?.waivers as
      | {
          leagueId?: string;
          teamId?: string;
          limit?: number;
          statusFilter?: string;
          sortKey?: string;
          sortDir?: string;
        }
      | undefined;
    if (saved) {
      if (saved.leagueId) setLeagueId(saved.leagueId);
      if (saved.teamId) setTeamId(saved.teamId);
      if (typeof saved.limit === "number") setLimit(Math.min(100, Math.max(1, saved.limit)));
      if (
        saved.statusFilter &&
        ["all", "pending", "won", "lost", "expired"].includes(saved.statusFilter)
      )
        setStatusFilter(saved.statusFilter as any);
      if (saved.sortKey && ["bid", "status"].includes(saved.sortKey))
        setSortKey(saved.sortKey as any);
      if (saved.sortDir && ["asc", "desc"].includes(saved.sortDir))
        setSortDir(saved.sortDir as any);
    }
  }, [preferences.layouts]);

  // Persist view preferences (debounced)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const nextLayouts = {
        ...(preferences.layouts || {}),
        waivers: { leagueId, teamId, limit, statusFilter, sortKey, sortDir },
      } as Record<string, unknown>;
      setLayouts(nextLayouts);
    }, 500);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [leagueId, teamId, limit, statusFilter, sortKey, sortDir, preferences.layouts, setLayouts]);

  return (
    <main className="min-h-screen p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader title="Waivers" />
        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Place a Bid</CardTitle>
          </CardHeader>
          <p className="text-xs text-gray-600">
            Uses Authorization: Bearer from localStorage key <code>uf_token</code>.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="League ID"
              value={leagueId}
              onChange={(e) => setLeagueId(e.target.value)}
            />
            <Input label="Team ID" value={teamId} onChange={(e) => setTeamId(e.target.value)} />
            <Input
              label="Player ID"
              value={playerId}
              onChange={(e) => setPlayerId(e.target.value)}
            />
            <Input
              label="Bid"
              type="number"
              value={String(bid)}
              onChange={(e) => setBid(Number(e.target.value))}
            />
          </div>
          <div className="flex items-center gap-2">
            <Button
              disabled={disabled}
              onClick={() => placeBid.mutate()}
              loading={placeBid.isPending}
              leftIcon={<CircleDollarSign className="h-4 w-4" aria-hidden />}
            >
              Place Bid
            </Button>
            <span className="text-xs text-gray-600">API: {API_BASE || "/"} /waivers/bids</span>
          </div>
        </Card>

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Recent Bids</CardTitle>
          </CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="grid grid-cols-2 gap-2 sm:flex sm:items-center sm:gap-3 text-sm">
              <label className="text-gray-600" htmlFor="waivers-limit">
                Limit
              </label>
              <input
                id="waivers-limit"
                className="w-24 rounded border px-2 py-1"
                type="number"
                value={limit}
                min={1}
                max={100}
                onChange={(e) => setLimit(Math.min(100, Math.max(1, Number(e.target.value))))}
              />

              <label className="text-gray-600" htmlFor="waivers-offset">
                Offset
              </label>
              <input
                id="waivers-offset"
                className="w-28 rounded border px-2 py-1"
                type="number"
                value={offset}
                min={0}
                onChange={(e) => setOffset(Math.max(0, Number(e.target.value)))}
              />

              <label className="text-gray-600" htmlFor="waivers-status">
                Status
              </label>
              <select
                id="waivers-status"
                className="w-28 rounded border px-2 py-1"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
              >
                <option value="all">All</option>
                <option value="pending">Pending</option>
                <option value="won">Won</option>
                <option value="lost">Lost</option>
                <option value="expired">Expired</option>
              </select>

              <label className="text-gray-600" htmlFor="waivers-sort-key">
                Sort
              </label>
              <select
                id="waivers-sort-key"
                className="w-28 rounded border px-2 py-1"
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value as any)}
              >
                <option value="bid">Bid</option>
                <option value="status">Status</option>
              </select>

              <label className="text-gray-600" htmlFor="waivers-sort-dir">
                Direction
              </label>
              <select
                id="waivers-sort-dir"
                className="w-28 rounded border px-2 py-1"
                value={sortDir}
                onChange={(e) => setSortDir(e.target.value as any)}
              >
                <option value="desc">Desc</option>
                <option value="asc">Asc</option>
              </select>
            </div>
          </div>
          {!leagueId && <p className="text-sm text-gray-600">Enter a League ID to view bids.</p>}
          {waivers.isLoading && <Skeleton className="h-16 w-full" />}
          {waivers.isError && (
            <p className="text-sm text-red-600">{(waivers.error as Error)?.message}</p>
          )}
          {waivers.data && (
            <>
              {waivers.data.items.length > 0 && (
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {(() => {
                    const counts = waivers.data!.items.reduce(
                      (acc, it) => {
                        acc.all += 1;
                        acc[it.status as keyof typeof acc] =
                          (acc[it.status as keyof typeof acc] || 0) + 1;
                        return acc;
                      },
                      { all: 0, pending: 0, won: 0, lost: 0, expired: 0 } as Record<string, number>,
                    );
                    const tiles: Array<{ label: string; value: number; color: string }> = [
                      { label: "Pending", value: counts.pending, color: "#2563eb" },
                      { label: "Won", value: counts.won, color: "#16a34a" },
                      { label: "Lost", value: counts.lost, color: "#dc2626" },
                      { label: "Expired", value: counts.expired, color: "#6b7280" },
                    ];
                    return tiles.map((t) => (
                      <div
                        key={t.label}
                        className="surface rounded-[var(--radius-md)] p-3 text-center border-l-4"
                        style={{ borderLeftColor: t.color }}
                      >
                        <div className="text-xs text-[var(--color-muted)]">{t.label}</div>
                        <div className="text-lg font-semibold">{t.value}</div>
                      </div>
                    ));
                  })()}
                </div>
              )}
              {(() => {
                const filtered = waivers.data!.items.filter((w) =>
                  statusFilter === "all" ? true : w.status === statusFilter,
                );
                const sorted = filtered.slice().sort((a, b) => {
                  if (sortKey === "bid") {
                    const cmp = (a.bid ?? 0) - (b.bid ?? 0);
                    return sortDir === "asc" ? cmp : -cmp;
                  } else {
                    const cmp = String(a.status).localeCompare(String(b.status));
                    return sortDir === "asc" ? cmp : -cmp;
                  }
                });
                return (
                  <ul className="text-sm">
                    {sorted.map((w) => {
                      const color =
                        w.status === "won"
                          ? "#16a34a"
                          : w.status === "lost" || w.status === "expired"
                            ? "#6b7280"
                            : "#2563eb";
                      const Icon =
                        w.status === "won"
                          ? CheckCircle2
                          : w.status === "lost" || w.status === "expired"
                            ? XCircle
                            : Clock;
                      return (
                        <li key={w.waiver_id} className="py-2">
                          <div
                            className="surface rounded-[var(--radius-md)] p-3 border-l-4"
                            style={{ borderLeftColor: color }}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex min-w-0 items-center gap-2">
                                <CircleDollarSign className="h-4 w-4 text-gray-500" aria-hidden />
                                <div className="min-w-0">
                                  <div className="truncate font-medium">Bid {w.bid}</div>
                                  <div className="text-xs text-gray-600 truncate">
                                    Team {String(w.team_id).slice(0, 8)} • Player{" "}
                                    {String(w.player_id).slice(0, 8)}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <Icon className="h-4 w-4" style={{ color }} aria-hidden />
                                <Badge
                                  variant={
                                    w.status === "won"
                                      ? "success"
                                      : w.status === "lost" || w.status === "expired"
                                        ? "secondary"
                                        : "default"
                                  }
                                >
                                  {w.status}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </li>
                      );
                    })}
                    {sorted.length === 0 && (
                      <li className="py-2">
                        <EmptyState
                          title="No bids match filters"
                          description="Try adjusting filters or pagination."
                        />
                      </li>
                    )}
                  </ul>
                );
              })()}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="ghost"
                  disabled={offset <= 0}
                  onClick={() => setOffset((o) => Math.max(0, o - limit))}
                >
                  <span className="inline-flex items-center gap-1">
                    <ChevronLeft className="h-4 w-4" aria-hidden /> Prev
                  </span>
                </Button>
                <Button variant="ghost" onClick={() => setOffset((o) => o + limit)}>
                  <span className="inline-flex items-center gap-1">
                    Next <ChevronRight className="h-4 w-4" aria-hidden />
                  </span>
                </Button>
              </div>
            </>
          )}
          <span className="text-xs text-gray-600">
            API: /waivers?league_id=...&team_id=...&limit&offset
          </span>
        </Card>
      </div>
    </main>
  );
}
