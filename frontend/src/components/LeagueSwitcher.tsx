"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getMyLeagues, queryKeys, MeLeagueItem } from "../services/api";

const KEY_LEAGUE = "uf_current_league_id";
const KEY_TEAM = "uf_current_team_id";

export default function LeagueSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.myLeagues(),
    queryFn: getMyLeagues,
  });

  const leagues = data?.items || [];
  const [leagueId, setLeagueId] = React.useState<string | undefined>(() => {
    try {
      return localStorage.getItem(KEY_LEAGUE) || undefined;
    } catch {
      return undefined;
    }
  });

  // When leagues load, ensure we have a valid selection
  React.useEffect(() => {
    if (!leagues.length) return;
    if (!leagueId || !leagues.find((l) => l.league_id === leagueId)) {
      const first = leagues[0];
      setLeagueId(first.league_id);
      try {
        localStorage.setItem(KEY_LEAGUE, first.league_id);
        localStorage.setItem(KEY_TEAM, first.team_id);
      } catch {}
    }
  }, [leagues, leagueId]);

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value;
    setLeagueId(id);
    const selected = leagues.find((l) => l.league_id === id);
    try {
      localStorage.setItem(KEY_LEAGUE, id);
      if (selected) localStorage.setItem(KEY_TEAM, selected.team_id);
    } catch {}
    // Navigate to league page if not already there
    if (!pathname?.startsWith(`/leagues/${id}`)) {
      router.push(`/leagues/${id}`);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="league-switcher" className="sr-only">
        Current League
      </label>
      <select
        id="league-switcher"
        value={leagueId || ""}
        onChange={onChange}
        disabled={isLoading || isError || leagues.length === 0}
        className="min-w-[180px] rounded-[var(--radius-sm)] border px-[var(--space-2)] py-[calc(var(--space-1))] text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)]"
        style={{
          background: "var(--color-surface)",
          color: "var(--color-text)",
          borderColor: "var(--border)",
        }}
        aria-label="Select league"
      >
        {isLoading ? (
          <option>Loading…</option>
        ) : isError ? (
          <option>Error loading leagues</option>
        ) : leagues.length === 0 ? (
          <option>No leagues</option>
        ) : (
          leagues.map((l: MeLeagueItem, index: number) => (
            <option key={`${l.league_id}-${index}`} value={l.league_id}>
              {l.name} · {l.season}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
