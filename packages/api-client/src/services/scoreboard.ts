import { ApiService } from '../models/ApiService';

// Types extracted from frontend
export interface ScoreboardItem {
  team_id: string;
  total_points: number;
  lineup_count?: number;
}

export interface ScoreboardResponse {
  league_id: string;
  items: ScoreboardItem[];
}

export interface MatchupTeam {
  team_id: string;
  team_name: string;
  total_points: number;
  projected_points?: number;
}

export interface Matchup {
  matchup_id: string;
  week: number;
  team1: MatchupTeam;
  team2: MatchupTeam;
  status: 'pending' | 'active' | 'completed';
}

export interface MatchupsResponse {
  league_id: string;
  week: number;
  matchups: Matchup[];
}

export interface WeeklyScores {
  league_id: string;
  week: number;
  scores: Array<{
    team_id: string;
    team_name: string;
    points: number;
    rank: number;
  }>;
}

// HTTP Client interface for platform abstraction
export interface HttpClient {
  get<T>(path: string, options?: RequestInit): Promise<T>;
  post<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  put<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  patch<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  delete<T>(path: string, options?: RequestInit): Promise<T>;
  setAuthToken(token: string): void;
  clearAuthToken(): void;
}

// ScoreboardService class
export class ScoreboardService {
  private httpClient: HttpClient;
  private baseUrl: string;

  constructor(httpClient: HttpClient, baseUrl: string = '') {
    this.httpClient = httpClient;
    this.baseUrl = baseUrl;
  }

  // API Methods extracted from frontend
  async getScoreboard(leagueId: string): Promise<ScoreboardResponse> {
    return this.httpClient.get<ScoreboardResponse>(`/leagues/${leagueId}/scoreboard`);
  }

  async getMatchups(leagueId: string, week?: number): Promise<MatchupsResponse> {
    const path = week
      ? `/leagues/${leagueId}/matchups?week=${week}`
      : `/leagues/${leagueId}/matchups`;
    return this.httpClient.get<MatchupsResponse>(path);
  }

  async getWeeklyScores(leagueId: string, week: number): Promise<WeeklyScores> {
    return this.httpClient.get<WeeklyScores>(`/leagues/${leagueId}/scores?week=${week}`);
  }

  async getCurrentWeekScores(leagueId: string): Promise<WeeklyScores> {
    return this.httpClient.get<WeeklyScores>(`/leagues/${leagueId}/scores/current`);
  }

  // Utility methods
  setAuthToken(token: string): void {
    this.httpClient.setAuthToken(token);
  }

  clearAuthToken(): void {
    this.httpClient.clearAuthToken();
  }

  // Helper methods for data processing
  getTopScorer(scoreboard: ScoreboardResponse): ScoreboardItem | null {
    if (scoreboard.items.length === 0) return null;
    return scoreboard.items.reduce((top, current) =>
      current.total_points > top.total_points ? current : top
    );
  }

  getRankings(scoreboard: ScoreboardResponse): ScoreboardItem[] {
    return [...scoreboard.items].sort((a, b) => b.total_points - a.total_points);
  }

  getTeamRank(scoreboard: ScoreboardResponse, teamId: string): number {
    const rankings = this.getRankings(scoreboard);
    const index = rankings.findIndex(item => item.team_id === teamId);
    return index !== -1 ? index + 1 : -1;
  }

  // Static factory method
  static create(httpClient: HttpClient, baseUrl?: string): ScoreboardService {
    return new ScoreboardService(httpClient, baseUrl);
  }

  // Get service definition for API contracts
  static getServiceDefinition(): ApiService {
    return ApiService.create('ScoreboardService', '/api')
      .get('/leagues/{leagueId}/scoreboard', true)
      .get('/leagues/{leagueId}/matchups', true)
      .get('/leagues/{leagueId}/scores', true)
      .get('/leagues/{leagueId}/scores/current', true)
      .build();
  }
}