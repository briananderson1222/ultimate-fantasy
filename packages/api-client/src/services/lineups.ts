import { ApiService } from '../models/ApiService';

// Types extracted from frontend
export interface LineupPlayer {
  player_id: string;
  position: string;
}

export interface LineupRequest {
  team_id: string;
  game_day: string;
  players: LineupPlayer[];
}

export interface LineupResponse {
  team_id: string;
  game_day: string;
  players: LineupPlayer[];
  version?: number | null;
}

export interface LineupListItem {
  lineup_id: string;
  team_id: string;
  game_day: string;
  players: LineupPlayer[];
  created_at: string;
}

export interface LineupListResponse {
  items: LineupListItem[];
}

export interface LineupListParams {
  team_id: string;
  game_day?: string;
  limit?: number;
  offset?: number;
}

export interface OptimalLineupRequest {
  team_id: string;
  game_day: string;
  exclude_players?: string[];
}

export interface OptimalLineupResponse {
  team_id: string;
  game_day: string;
  lineup: LineupPlayer[];
  projected_points: number;
  confidence_score: number;
}

export interface LineupAnalysis {
  team_id: string;
  game_day: string;
  total_projected_points: number;
  position_breakdown: Record<string, {
    filled: boolean;
    player_id?: string;
    projected_points?: number;
    alternatives?: Array<{
      player_id: string;
      projected_points: number;
    }>;
  }>;
  bench_strength: number;
  recommendations: string[];
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

// LineupsService class
export class LineupsService {
  private httpClient: HttpClient;
  private baseUrl: string;

  constructor(httpClient: HttpClient, baseUrl: string = '') {
    this.httpClient = httpClient;
    this.baseUrl = baseUrl;
  }

  // API Methods extracted from frontend
  async setLineup(data: LineupRequest): Promise<LineupResponse> {
    return this.httpClient.post<LineupResponse>('/lineups', data);
  }

  async updateLineup(data: LineupRequest): Promise<LineupResponse> {
    return this.setLineup(data); // Same endpoint for create/update
  }

  async getLineup(teamId: string, gameDay: string): Promise<LineupResponse> {
    return this.httpClient.get<LineupResponse>(`/lineups/${teamId}/${gameDay}`);
  }

  async listLineups(params: LineupListParams): Promise<LineupListResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('team_id', params.team_id);

    if (params.game_day) searchParams.set('game_day', params.game_day);
    if (params.limit) searchParams.set('limit', params.limit.toString());
    if (params.offset) searchParams.set('offset', params.offset.toString());

    return this.httpClient.get<LineupListResponse>(`/lineups?${searchParams.toString()}`);
  }

  async deleteLineup(teamId: string, gameDay: string): Promise<void> {
    return this.httpClient.delete<void>(`/lineups/${teamId}/${gameDay}`);
  }

  async getOptimalLineup(data: OptimalLineupRequest): Promise<OptimalLineupResponse> {
    return this.httpClient.post<OptimalLineupResponse>('/lineups/optimal', data);
  }

  async analyzeLineup(teamId: string, gameDay: string): Promise<LineupAnalysis> {
    return this.httpClient.get<LineupAnalysis>(`/lineups/${teamId}/${gameDay}/analysis`);
  }

  async copyLineup(fromTeamId: string, fromGameDay: string, toTeamId: string, toGameDay: string): Promise<LineupResponse> {
    return this.httpClient.post<LineupResponse>('/lineups/copy', {
      from_team_id: fromTeamId,
      from_game_day: fromGameDay,
      to_team_id: toTeamId,
      to_game_day: toGameDay
    });
  }

  // Utility methods
  setAuthToken(token: string): void {
    this.httpClient.setAuthToken(token);
  }

  clearAuthToken(): void {
    this.httpClient.clearAuthToken();
  }

  // Helper methods for lineup management
  validateLineup(lineup: LineupPlayer[], requiredPositions: string[]): boolean {
    const filledPositions = lineup.map(player => player.position);
    return requiredPositions.every(pos => filledPositions.includes(pos));
  }

  getStartingLineup(lineup: LineupPlayer[], benchPositions: string[] = ['BN']): LineupPlayer[] {
    return lineup.filter(player => !benchPositions.includes(player.position));
  }

  getBenchPlayers(lineup: LineupPlayer[], benchPositions: string[] = ['BN']): LineupPlayer[] {
    return lineup.filter(player => benchPositions.includes(player.position));
  }

  getPlayersByPosition(lineup: LineupPlayer[], position: string): LineupPlayer[] {
    return lineup.filter(player => player.position === position);
  }

  movePlayerToPosition(lineup: LineupPlayer[], playerId: string, newPosition: string): LineupPlayer[] {
    return lineup.map(player =>
      player.player_id === playerId
        ? { ...player, position: newPosition }
        : player
    );
  }

  swapPlayerPositions(lineup: LineupPlayer[], player1Id: string, player2Id: string): LineupPlayer[] {
    const player1 = lineup.find(p => p.player_id === player1Id);
    const player2 = lineup.find(p => p.player_id === player2Id);

    if (!player1 || !player2) {
      throw new Error('One or both players not found in lineup');
    }

    return lineup.map(player => {
      if (player.player_id === player1Id) {
        return { ...player, position: player2.position };
      }
      if (player.player_id === player2Id) {
        return { ...player, position: player1.position };
      }
      return player;
    });
  }

  // Static factory method
  static create(httpClient: HttpClient, baseUrl?: string): LineupsService {
    return new LineupsService(httpClient, baseUrl);
  }

  // Get service definition for API contracts
  static getServiceDefinition(): ApiService {
    return ApiService.create('LineupsService', '/api')
      .post('/lineups', {
        team_id: 'string',
        game_day: 'string',
        players: 'LineupPlayer[]'
      }, {
        team_id: 'string',
        game_day: 'string',
        players: 'LineupPlayer[]',
        version: 'number'
      }, true)
      .get('/lineups/{teamId}/{gameDay}', true)
      .get('/lineups', true)
      .delete('/lineups/{teamId}/{gameDay}', true)
      .post('/lineups/optimal', {
        team_id: 'string',
        game_day: 'string',
        exclude_players: 'string[]'
      }, undefined, true)
      .get('/lineups/{teamId}/{gameDay}/analysis', true)
      .post('/lineups/copy', {
        from_team_id: 'string',
        from_game_day: 'string',
        to_team_id: 'string',
        to_game_day: 'string'
      }, undefined, true)
      .build();
  }
}