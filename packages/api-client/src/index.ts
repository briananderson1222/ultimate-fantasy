// API Client Package - Main Exports

// Core HTTP Client
export {
  type HttpClient,
  type HttpClientConfig,
  UniversalHttpClient,
  createHttpClient,
  httpClient,
  DEFAULT_HTTP_CONFIG,
  ApiError,
  isApiError,
  handleApiError,
} from "./client/http";

// Models - specific exports to avoid conflicts
export {
  ApiService,
  ApiServiceBuilder,
  ApiServiceSchema,
  type ApiServiceData,
} from "./models/ApiService";

export {
  Endpoint,
  EndpointSchema,
  type EndpointData,
  type HttpMethod,
} from "./models/Endpoint";

// Services
export * from "./services/leagues";
export * from "./services/scoreboard";
export * from "./services/waivers";
export * from "./services/lineups";

// Ultimate Fantasy API Types
export interface League {
  id: string;
  name: string;
  settings: LeagueSettings;
  status: "setup" | "drafting" | "active" | "completed";
  created_at: string;
  updated_at: string;
}

export interface LeagueSettings {
  max_teams: number;
  scoring_type: "standard" | "ppr" | "half_ppr";
  roster_size: number;
  playoff_teams: number;
  trade_deadline?: string;
  waiver_type: "rolling" | "faab";
}

export interface Player {
  id: string;
  external_id: string;
  name: string;
  position: string;
  team: string;
  injury_status: "healthy" | "questionable" | "doubtful" | "out" | "ir";
  projected_points: number;
  season_stats: Record<string, number>;
  game_stats: Record<string, number>;
}

export interface Team {
  id: string;
  league_id: string;
  user_id: string;
  name: string;
  wins: number;
  losses: number;
  ties: number;
  points_for: number;
  points_against: number;
  waiver_priority: number;
  roster: string[];
  budget: number;
}

export interface Draft {
  id: string;
  league_id: string;
  status: "pending" | "in_progress" | "completed";
  current_pick: number;
  picks: DraftPick[];
  timer_seconds: number;
  started_at?: string;
  completed_at?: string;
}

export interface DraftPick {
  pick_number: number;
  team_id: string;
  player_id: string;
  timestamp: string;
}

export interface Trade {
  id: string;
  league_id: string;
  proposing_team_id: string;
  receiving_team_id: string;
  proposed_players: string[];
  requested_players: string[];
  status: "pending" | "accepted" | "rejected" | "expired";
  evaluation_score: number;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface Lineup {
  id: string;
  team_id: string;
  week: number;
  players: LineupSlot[];
  projected_points: number;
  actual_points?: number;
  locked: boolean;
  version: number;
  updated_at: string;
}

export interface LineupSlot {
  position: string;
  player_id?: string;
  is_flex: boolean;
}

export interface WaiverBid {
  id: string;
  team_id: string;
  player_id: string;
  bid_amount: number;
  drop_player_id?: string;
  priority: number;
  status: "pending" | "successful" | "failed";
  processed_at?: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  verified: boolean;
  created_at: string;
  updated_at: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number;
  user: User;
}

// Request Types
export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
  first_name?: string;
  last_name?: string;
}

export interface CreateLeagueRequest {
  name: string;
  settings: LeagueSettings;
  invite_code?: string;
}

export interface PlayerSearchRequest {
  query?: string;
  position?: string;
  team?: string;
  available_only?: boolean;
  page?: number;
  limit?: number;
}

export interface ProposeTradeRequest {
  league_id: string;
  receiving_team_id: string;
  proposed_players: string[];
  requested_players: string[];
}

export interface TradeEvaluation {
  score: number;
  analysis: string;
  fairness:
    | "heavily_favors_team_a"
    | "favors_team_a"
    | "fair"
    | "favors_team_b"
    | "heavily_favors_team_b";
  recommendations: string[];
}

// Factory function to create configured HTTP client for Ultimate Fantasy
export function createUltimateFantasyClient(baseUrl?: string) {
  const httpModule = require("./client/http");
  return httpModule.createHttpClient({
    baseUrl: baseUrl || "/api/v1",
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
    enableTokenRefresh: true,
    refreshTokenEndpoint: "/auth/refresh",
    defaultHeaders: {
      Accept: "application/json",
    },
  });
}

// Default client instance
export const ultimateFantasyClient = createUltimateFantasyClient();
