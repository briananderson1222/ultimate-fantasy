"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { API_BASE } from "../../../services/client";
import { getPublicLeague, joinLeague, getScoreboard, getLeagueMembers } from "../../../services/api";
import DevAuthToken from "../../../components/DevAuthToken";
import { Skeleton } from "../../../components/ui/skeleton";
import { Tabs } from "../../../components/ui/tabs";
import { useState, useRef } from "react";
import { Modal } from "../../../components/ui/modal";
import { Button } from "../../../components/ui/button";
import { useToast } from "../../../components/ui/toast";
import { Card, CardHeader, CardTitle } from "../../../components/ui/card";
import { EmptyState } from "../../../components/ui/empty-state";
import { Badge } from "../../../components/ui/badge";
import { PageHeader } from "../../../components/ui/page-header";
import { UserPlus, X, Check, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { LeagueBranding } from "../../../components/LeagueBranding";
import OnboardingTour from "../../../components/OnboardingTour";

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
  const [tab, setTab] = useState<string>("overview");

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
    onSuccess: (data) => {
      toast.show({ title: "Joined league", description: data.team_name });
      setOpen(false);
    },
    onError: (err: any) => toast.show({ title: "Join failed", description: String(err?.message || err) }),
  });

  const scoreboard = useQuery({
    queryKey: ["scoreboard", leagueId],
    queryFn: async () => {
      if (!leagueId) throw new Error("missing league id");
      return await getScoreboard(leagueId);
    },
    enabled: !!leagueId,
    refetchInterval: 10_000,
  });
  const members = useQuery({
    queryKey: ["leagueMembers", leagueId],
    queryFn: async () => {
      if (!leagueId) throw new Error("missing league id");
      return await getLeagueMembers(leagueId);
    },
    enabled: !!leagueId,
  });
  const [open, setOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const toast = useToast();
  const prevPointsRef = useRef<Map<string, number>>(new Map());

  return (
    <main className="min-h-screen p-6">
      <LeagueBranding themeVars={info.data?.branding?.theme}>
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader
          title="League"
          actions={
            <div className="flex items-center gap-2">
              <Link className="text-blue-700 underline px-2 py-1 rounded focus-visible:ring-2 focus-visible:ring-offset-2" href="/leagues">Back</Link>
              <Link className="text-blue-700 underline px-2 py-1 rounded focus-visible:ring-2 focus-visible:ring-offset-2" href={`/leagues/${leagueId}/settings`}>Settings</Link>
              <Button variant="ghost" onClick={() => setTourOpen(true)}>Start tour</Button>
            </div>
          }
        />

        {info.isLoading && <Skeleton className="h-16 w-full" />}
        {info.isError && (
          <p className="text-sm text-red-600">{(info.error as Error)?.message}</p>
        )}
        {info.data && (
          <Card>
            <div className="text-lg font-medium mb-1">{info.data.branding?.name || info.data.name}</div>
            <div className="text-gray-600 text-sm mb-3">
              {info.data.sport} • {info.data.league_type} • {info.data.season}
            </div>
            <div
              id="league-tabs"
              className="sticky top-0 z-10 border-b bg-[var(--color-surface)]/95 backdrop-blur"
              style={{ borderColor: 'var(--border)' }}
            >
            <Tabs
              tabs={[
                { value: "overview", label: "Overview" },
                { value: "scoreboard", label: "Scoreboard" },
                { value: "members", label: "Managers" },
              ]}
              value={tab}
              onChange={setTab}
            />
            </div>
            {tab === "overview" && (
              <div className="text-sm text-gray-800">Welcome to the league. Use the actions below to join and participate.</div>
            )}
            {tab === "scoreboard" && (
              <div className="space-y-2">
                {scoreboard.isLoading && <Skeleton className="h-10 w-full" />}
                {scoreboard.isError && (
                  <p className="text-sm text-red-600">{(scoreboard.error as Error)?.message}</p>
                )}
                {scoreboard.data && scoreboard.data.items && (
                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                    {(() => {
                      const items = scoreboard.data!.items;
                      const current = new Map<string, number>();
                      for (const it of items) current.set(String(it.team_id), it.total_points ?? 0);
                      const top = items.length ? Math.max(...items.map((i) => i.total_points ?? 0)) : 0;
                      return items.map((it, idx) => {
                        const id = String(it.team_id);
                        const pts = it.total_points ?? 0;
                        const prev = prevPointsRef.current.get(id) ?? 0;
                        const delta = pts - prev;
                        const hue = (() => {
                          let h = 0;
                          for (let i = 0; i < id.length; i++) h = (h + id.charCodeAt(i) * 17) % 360;
                          return h;
                        })();
                        const TrendIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
                        const trendColor = delta > 0 ? "text-green-600" : delta < 0 ? "text-red-600" : "text-gray-500";
                        return (
                          <div key={idx} className="surface rounded-[var(--radius-md)] p-3">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div
                                  className="flex h-10 w-10 items-center justify-center rounded-full text-white shadow"
                                  style={{
                                    background: `linear-gradient(135deg, hsl(${hue} 70% 35%), hsl(${(hue + 30) % 360} 70% 45%))`,
                                  }}
                                  aria-hidden
                                >
                                  <span className="text-sm font-semibold">{String(id).slice(0, 2).toUpperCase()}</span>
                                </div>
                                <div>
                                  <div className="text-sm font-medium">Team {id.slice(0, 8)}</div>
                                  <div className="text-xs text-[var(--color-muted)]">
                                    {top > 0 && pts === top ? <Badge variant="success">Leader</Badge> : null}
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-lg font-semibold">{pts}</div>
                                <div className={`flex items-center justify-end gap-1 text-xs ${trendColor}`} aria-live="polite">
                                  <TrendIcon className="h-3.5 w-3.5" aria-hidden />
                                  <span>{delta === 0 ? "—" : delta > 0 ? `+${delta}` : `${delta}`}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      });
                    })()}
                    {scoreboard.data.items.length === 0 && (
                      <div className="sm:col-span-2 md:col-span-3">
                        <EmptyState title="No scores yet" description="Lineups will appear here once games are played." />
                      </div>
                    )}
                    {(() => {
                      // Update prev points after rendering tiles
                      const items = scoreboard.data!.items;
                      items.forEach((it) => prevPointsRef.current.set(String(it.team_id), it.total_points ?? 0));
                      return null;
                    })()}
                  </div>
                )}
              </div>
            )}
            {tab === "members" && (
              <div className="space-y-2">
                {members.isLoading && <Skeleton className="h-10 w-full" />}
                {members.isError && (
                  <p className="text-sm text-red-600">{(members.error as Error)?.message}</p>
                )}
                {members.data && (
                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                    {members.data.items.map((m) => {
                      const uid = String(m.user_id);
                      const team = String(m.team_id);
                      const short = uid.slice(0, 8);
                      let h = 0;
                      for (let i = 0; i < team.length; i++) h = (h + team.charCodeAt(i) * 17) % 360;
                      return (
                        <div key={m.team_id} className="surface rounded-[var(--radius-md)] p-3">
                          <div className="flex items-center gap-3">
                            <div
                              className="flex h-10 w-10 items-center justify-center rounded-full text-white shadow"
                              style={{ background: `linear-gradient(135deg, hsl(${h} 70% 35%), hsl(${(h + 30) % 360} 70% 45%))` }}
                              aria-hidden
                            >
                              <span className="text-sm font-semibold">{(m.team_name || 'T').slice(0, 2).toUpperCase()}</span>
                            </div>
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium">{m.team_name}</div>
                              <div className="text-xs text-[var(--color-muted)]">{short}</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    {members.data.items.length === 0 && (
                      <div className="sm:col-span-2 md:col-span-3">
                        <EmptyState title="No managers yet" description="Be the first to join this league." />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </Card>
        )}

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Join this league</CardTitle>
          </CardHeader>
          <p className="text-xs text-gray-600">Uses Authorization: Bearer from localStorage key <code>uf_token</code>.</p>
          <div className="flex items-center gap-2">
            <Button data-tour="join-button" onClick={() => setOpen(true)} disabled={join.isPending} leftIcon={<UserPlus className="h-4 w-4" aria-hidden />}>
              Join
            </Button>
            <span className="text-xs text-gray-600">API: {API_BASE || "/"} /leagues/{leagueId}/join</span>
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
          <Modal open={open} onClose={() => setOpen(false)} title="Join League">
            <p className="text-sm text-gray-700 mb-3">Confirm you want to join this league.</p>
            <div className="flex items-center justify-end gap-2">
              <Button variant="ghost" onClick={() => setOpen(false)} leftIcon={<X className="h-4 w-4" aria-hidden />}>Cancel</Button>
              <Button onClick={() => join.mutate()} disabled={join.isPending} loading={join.isPending} leftIcon={<Check className="h-4 w-4" aria-hidden /> }>
                Confirm Join
              </Button>
            </div>
          </Modal>
        </Card>

        <Card className="space-y-3">
          <CardHeader>
            <CardTitle>Scoreboard</CardTitle>
          </CardHeader>
          {scoreboard.isLoading && <Skeleton className="h-10 w-full" />}
          {scoreboard.isError && (
            <p className="text-sm text-red-600">{(scoreboard.error as Error)?.message}</p>
          )}
          {scoreboard.data && scoreboard.data.items && (
            <ul className="text-sm text-gray-800">
              {(() => {
                const items = scoreboard.data!.items;
                const top = items.length ? Math.max(...items.map((i) => i.total_points ?? 0)) : 0;
                return items.map((it, idx) => (
                  <li key={idx} className="flex items-center justify-between border-b py-1 hover:bg-gray-50">
                    <span className="text-gray-600">Team {String(it.team_id).slice(0, 8)}</span>
                    <span className="flex items-center gap-2">
                      {top > 0 && (it.total_points ?? 0) === top && <Badge variant="success">Leader</Badge>}
                      <span className="font-medium">{it.total_points ?? 0}</span>
                    </span>
                  </li>
                ));
              })()}
              {scoreboard.data.items.length === 0 && (
                <li className="py-2">
                  <EmptyState title="No scores yet" description="Come back after lineups are scored." />
                </li>
              )}
            </ul>
          )}
        </Card>

        <DevAuthToken />
        <OnboardingTour
          id="league-public"
          steps={[
            { selector: '[data-tour="join-button"]', title: 'Join the league', content: 'Join to participate in matchups and scoring.' },
            { selector: '#league-tabs', title: 'Explore tabs', content: 'Overview, Scoreboard, and Managers tabs show league info.' },
          ]}
          open={tourOpen}
          onClose={() => setTourOpen(false)}
        />
      </div>
      </LeagueBranding>
    </main>
  );
}
