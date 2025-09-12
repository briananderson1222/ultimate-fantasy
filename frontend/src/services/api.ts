"use client";

import { apiFetch } from "./client";
import {
  UseMutationOptions,
  UseQueryOptions,
  useMutation,
  useQuery,
} from "@tanstack/react-query";

// Types matching backend contracts/openapi.yml
export type LeagueCreate = {
  name: string;
  sport: string;
  league_type: string;
  season: string;
};

export type LeagueResponse = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  invite_link?: string | null;
};

export type RuleUpdate = { name: string; value: Record<string, unknown> };
export type RuleOut = {
  rule_id: string;
  league_id: string;
  name: string;
  value: Record<string, unknown>;
};

export type LineupPlayer = { player_id: string; position: string };
export type LineupRequest = { team_id: string; game_day: string; players: LineupPlayer[] };
export type LineupResponse = { team_id: string; game_day: string; players: LineupPlayer[]; version?: number | null };

export type WaiverBidRequest = {
  league_id: string;
  team_id: string;
  player_id: string;
  bid: number;
};
export type WaiverBidResponse = WaiverBidRequest & {
  waiver_id: string;
  status: string;
};

export type LeaguePublic = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
};

export type JoinResponse = {
  team_id: string;
  league_id: string;
  user_id: string;
  team_name: string;
};

export type ScoreboardItem = { team_id: string; total_points: number; lineup_count?: number };
export type ScoreboardResponse = { league_id: string; items: ScoreboardItem[] };

function authHeaders(): Record<string, string> {
  try {
    const token = typeof window !== "undefined" ? window.localStorage.getItem("uf_token") : null;
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {}
  return {};
}

// Low-level fetchers
export async function createLeague(data: LeagueCreate, userId?: string): Promise<LeagueResponse> {
  return await apiFetch<LeagueResponse>(`/leagues`, {
    method: "POST",
    headers: { ...authHeaders(), ...(userId ? { "x-user-id": userId } : {}) },
    body: JSON.stringify(data),
  });
}

export async function joinLeague(leagueId: string, userId?: string): Promise<JoinResponse> {
  return await apiFetch<JoinResponse>(`/leagues/${leagueId}/join`, {
    method: "POST",
    headers: { ...authHeaders(), ...(userId ? { "x-user-id": userId } : {}) },
  });
}

export async function updateLeagueSettings(
  leagueId: string,
  data: RuleUpdate,
  userId?: string
): Promise<RuleOut> {
  return await apiFetch<RuleOut>(`/leagues/${leagueId}/settings`, {
    method: "PATCH",
    headers: { ...authHeaders(), ...(userId ? { "x-user-id": userId } : {}) },
    body: JSON.stringify(data),
  });
}

export async function setLineup(data: LineupRequest, userId?: string): Promise<LineupResponse> {
  return await apiFetch<LineupResponse>(`/lineups`, {
    method: "PUT",
    headers: { ...authHeaders(), ...(userId ? { "x-user-id": userId } : {}) },
    body: JSON.stringify(data),
  });
}

export async function getScoreboard(leagueId: string): Promise<ScoreboardResponse> {
  return await apiFetch<ScoreboardResponse>(`/leagues/${leagueId}/scoreboard`);
}

export async function placeWaiverBid(
  data: WaiverBidRequest,
  userId?: string
): Promise<WaiverBidResponse> {
  return await apiFetch<WaiverBidResponse>(`/waivers/bids`, {
    method: "POST",
    headers: { ...authHeaders(), ...(userId ? { "x-user-id": userId } : {}) },
    body: JSON.stringify(data),
  });
}

export async function getPublicLeague(leagueId: string): Promise<LeaguePublic> {
  return await apiFetch<LeaguePublic>(`/leagues/${leagueId}/public`);
}

// Query keys
export const queryKeys = {
  league: (id: string) => ["league", id] as const,
  scoreboard: (id: string) => ["scoreboard", id] as const,
};

// React Query helpers
export function useCreateLeague(
  options?: UseMutationOptions<LeagueResponse, Error, { data: LeagueCreate; userId: string }>
) {
  return useMutation<LeagueResponse, Error, { data: LeagueCreate; userId: string }>({
    mutationFn: ({ data, userId }) => createLeague(data, userId),
    ...options,
  });
}

export function useJoinLeague(
  leagueId: string,
  options?: UseMutationOptions<JoinResponse, Error, { userId: string }>
) {
  return useMutation<JoinResponse, Error, { userId: string }>({
    mutationFn: ({ userId }) => joinLeague(leagueId, userId),
    ...options,
  });
}

export function useUpdateLeagueSettings(
  leagueId: string,
  options?: UseMutationOptions<RuleOut, Error, { data: RuleUpdate; userId: string }>
) {
  return useMutation<RuleOut, Error, { data: RuleUpdate; userId: string }>({
    mutationFn: ({ data, userId }) => updateLeagueSettings(leagueId, data, userId),
    ...options,
  });
}

export function useSetLineup(
  options?: UseMutationOptions<LineupResponse, Error, { data: LineupRequest; userId: string }>
) {
  return useMutation<LineupResponse, Error, { data: LineupRequest; userId: string }>({
    mutationFn: ({ data, userId }) => setLineup(data, userId),
    ...options,
  });
}

export function usePublicLeague(
  leagueId: string | undefined,
  options?: UseQueryOptions<LeaguePublic, Error, LeaguePublic, ReturnType<typeof queryKeys.league>>
) {
  return useQuery<LeaguePublic, Error, LeaguePublic, ReturnType<typeof queryKeys.league>>({
    queryKey: queryKeys.league(leagueId || ""),
    queryFn: () => {
      if (!leagueId) throw new Error("leagueId is required");
      return getPublicLeague(leagueId);
    },
    enabled: !!leagueId,
    ...options,
  });
}

export function useScoreboard(
  leagueId: string | undefined,
  options?: UseQueryOptions<ScoreboardResponse, Error, ScoreboardResponse, ReturnType<typeof queryKeys.scoreboard>>
) {
  return useQuery<ScoreboardResponse, Error, ScoreboardResponse, ReturnType<typeof queryKeys.scoreboard>>({
    queryKey: queryKeys.scoreboard(leagueId || ""),
    queryFn: () => {
      if (!leagueId) throw new Error("leagueId is required");
      return getScoreboard(leagueId);
    },
    enabled: !!leagueId,
    ...options,
  });
}

export function usePlaceWaiverBid(
  options?: UseMutationOptions<WaiverBidResponse, Error, { data: WaiverBidRequest; userId: string }>
) {
  return useMutation<WaiverBidResponse, Error, { data: WaiverBidRequest; userId: string }>({
    mutationFn: ({ data, userId }) => placeWaiverBid(data, userId),
    ...options,
  });
}
