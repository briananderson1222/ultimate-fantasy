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
// Read API types
export type MeLeagueItem = {
  league_id: string;
  name: string;
  season: string;
  team_id: string;
};
export type MeLeaguesResponse = { items: MeLeagueItem[] };

export type MemberItem = { team_id: string; user_id: string; team_name: string };
export type MembersResponse = { items: MemberItem[] };

export type WaiverListItem = {
  waiver_id: string;
  league_id: string;
  team_id: string;
  player_id: string;
  bid: number;
  status: string;
};
export type WaiverListResponse = { items: WaiverListItem[] };

export type LeagueBranding = {
  // An optional map of CSS variable overrides like { "--color-primary": "#123456" }
  theme?: Record<string, string>;
  // Optional display name/logo overrides that the UI may use in the future
  name?: string;
  logo_url?: string | null;
};
export type LeagueBrandingOut = LeagueBranding & { league_id: string };

export type LeaguePublic = {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  branding?: LeagueBranding;
};

export type JoinResponse = {
  team_id: string;
  league_id: string;
  user_id: string;
  team_name: string;
};

export type ScoreboardItem = { team_id: string; total_points: number; lineup_count?: number };
export type ScoreboardResponse = { league_id: string; items: ScoreboardItem[] };

// Preferences API
export type PreferencesPayload = {
  theme: "light" | "dark" | "custom";
  density: "comfortable" | "compact";
  locale: string;
  layouts?: Record<string, unknown> | null;
};
export type PreferencesResponse = PreferencesPayload & { user_id: string };

function authHeaders(): Record<string, string> {
  try {
    const token = typeof window !== "undefined" ? window.localStorage.getItem("uf_token") : null;
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {}
  return {};
}

// Low-level fetchers
export async function createLeague(data: LeagueCreate): Promise<LeagueResponse> {
  return await apiFetch<LeagueResponse>(`/leagues`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: JSON.stringify(data),
  });
}

export async function joinLeague(leagueId: string): Promise<JoinResponse> {
  return await apiFetch<JoinResponse>(`/leagues/${leagueId}/join`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
}

export async function updateLeagueSettings(
  leagueId: string,
  data: RuleUpdate
): Promise<RuleOut> {
  return await apiFetch<RuleOut>(`/leagues/${leagueId}/settings`, {
    method: "PATCH",
    headers: { ...authHeaders() },
    body: JSON.stringify(data),
  });
}

export async function setLineup(data: LineupRequest): Promise<LineupResponse> {
  return await apiFetch<LineupResponse>(`/lineups`, {
    method: "PUT",
    headers: { ...authHeaders() },
    body: JSON.stringify(data),
  });
}

export async function getScoreboard(leagueId: string): Promise<ScoreboardResponse> {
  return await apiFetch<ScoreboardResponse>(`/leagues/${leagueId}/scoreboard`);
}

export async function placeWaiverBid(
  data: WaiverBidRequest
): Promise<WaiverBidResponse> {
  return await apiFetch<WaiverBidResponse>(`/waivers/bids`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: JSON.stringify(data),
  });
}

export async function getPublicLeague(leagueId: string): Promise<LeaguePublic> {
  return await apiFetch<LeaguePublic>(`/leagues/${leagueId}/public`);
}

export async function getLeagueBranding(leagueId: string): Promise<LeagueBrandingOut> {
  return await apiFetch<LeagueBrandingOut>(`/leagues/${leagueId}/branding`);
}

export async function updateLeagueBranding(
  leagueId: string,
  payload: LeagueBranding
): Promise<LeagueBrandingOut> {
  return await apiFetch<LeagueBrandingOut>(`/leagues/${leagueId}/branding`, {
    method: "PUT",
    headers: { ...authHeaders() },
    body: JSON.stringify(payload),
  });
}

// Preferences endpoints
export async function getPreferences(): Promise<PreferencesResponse> {
  return await apiFetch<PreferencesResponse>(`/me/preferences`, {
    headers: { ...authHeaders() },
  });
}

export async function updatePreferences(
  payload: PreferencesPayload
): Promise<PreferencesResponse> {
  return await apiFetch<PreferencesResponse>(`/me/preferences`, {
    method: "PUT",
    headers: { ...authHeaders() },
    body: JSON.stringify(payload),
  });
}
// New read endpoints
export async function getMyLeagues(): Promise<MeLeaguesResponse> {
  return await apiFetch<MeLeaguesResponse>(`/me/leagues`, {
    headers: { ...authHeaders() },
  });
}

export async function getLeagueMembers(leagueId: string): Promise<MembersResponse> {
  return await apiFetch<MembersResponse>(`/leagues/${leagueId}/members`);
}

export async function listWaivers(params: {
  league_id: string;
  team_id?: string;
  limit?: number;
  offset?: number;
}): Promise<WaiverListResponse> {
  const p = new URLSearchParams();
  p.set("league_id", params.league_id);
  if (params.team_id) p.set("team_id", params.team_id);
  p.set("limit", String(params.limit ?? 50));
  p.set("offset", String(params.offset ?? 0));
  return await apiFetch<WaiverListResponse>(`/waivers?${p.toString()}`);
}

export type LineupListItem = { lineup_id: string; team_id: string; game_day: string; players: LineupPlayer[]; version: number };
export type LineupListResponse = { items: LineupListItem[] };

export async function listLineups(params: {
  team_id: string;
  game_day?: string;
  limit?: number;
  offset?: number;
}): Promise<LineupListResponse> {
  const p = new URLSearchParams();
  p.set("team_id", params.team_id);
  if (params.game_day) p.set("game_day", params.game_day);
  p.set("limit", String(params.limit ?? 50));
  p.set("offset", String(params.offset ?? 0));
  return await apiFetch<LineupListResponse>(`/lineups?${p.toString()}`);
}

// Query keys
export const queryKeys = {
  league: (id: string) => ["league", id] as const,
  scoreboard: (id: string) => ["scoreboard", id] as const,
  myLeagues: () => ["myLeagues"] as const,
  leagueMembers: (id: string) => ["leagueMembers", id] as const,
  waivers: (args: { league_id: string; team_id?: string; limit?: number; offset?: number }) =>
    ["waivers", args] as const,
  lineups: (args: { team_id: string; game_day?: string; limit?: number; offset?: number }) =>
    ["lineups", args] as const,
};

// React Query helpers
export function useCreateLeague(
  options?: UseMutationOptions<LeagueResponse, Error, LeagueCreate>
) {
  return useMutation<LeagueResponse, Error, LeagueCreate>({
    mutationFn: (data) => createLeague(data),
    ...options,
  });
}

export function useJoinLeague(
  leagueId: string,
  options?: UseMutationOptions<JoinResponse, Error, void>
) {
  return useMutation<JoinResponse, Error, void>({
    mutationFn: () => joinLeague(leagueId),
    ...options,
  });
}

export function useUpdateLeagueSettings(
  leagueId: string,
  options?: UseMutationOptions<RuleOut, Error, RuleUpdate>
) {
  return useMutation<RuleOut, Error, RuleUpdate>({
    mutationFn: (data) => updateLeagueSettings(leagueId, data),
    ...options,
  });
}

export function useSetLineup(
  options?: UseMutationOptions<LineupResponse, Error, LineupRequest>
) {
  return useMutation<LineupResponse, Error, LineupRequest>({
    mutationFn: (data) => setLineup(data),
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
  options?: UseMutationOptions<WaiverBidResponse, Error, WaiverBidRequest>
) {
  return useMutation<WaiverBidResponse, Error, WaiverBidRequest>({
    mutationFn: (data) => placeWaiverBid(data),
    ...options,
  });
}
