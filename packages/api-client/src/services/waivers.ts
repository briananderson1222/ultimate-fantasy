import { ApiService } from '../models/ApiService';

// Types extracted from frontend
export interface WaiverBidRequest {
  league_id: string;
  team_id: string;
  player_id: string;
  bid: number;
}

export interface WaiverBidResponse extends WaiverBidRequest {
  waiver_id: string;
  status: string;
}

export interface WaiverListItem {
  waiver_id: string;
  league_id: string;
  team_id: string;
  player_id: string;
  bid: number;
  status: string;
  created_at: string;
}

export interface WaiverListResponse {
  items: WaiverListItem[];
}

export interface WaiverListParams {
  league_id: string;
  team_id?: string;
  limit?: number;
  offset?: number;
}

export interface WaiverClaimParams {
  league_id: string;
  team_id: string;
  add_player_id: string;
  drop_player_id?: string;
  priority: number;
}

export interface WaiverClaimResponse {
  claim_id: string;
  league_id: string;
  team_id: string;
  add_player_id: string;
  drop_player_id?: string;
  priority: number;
  status: 'pending' | 'processed' | 'failed';
  created_at: string;
}

export interface WaiverProcessingResult {
  league_id: string;
  processed_at: string;
  claims_processed: number;
  successful_claims: string[];
  failed_claims: Array<{
    claim_id: string;
    reason: string;
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

// WaiversService class
export class WaiversService {
  private httpClient: HttpClient;
  private baseUrl: string;

  constructor(httpClient: HttpClient, baseUrl: string = '') {
    this.httpClient = httpClient;
    this.baseUrl = baseUrl;
  }

  // API Methods extracted from frontend
  async placeWaiverBid(data: WaiverBidRequest): Promise<WaiverBidResponse> {
    return this.httpClient.post<WaiverBidResponse>('/waivers/bids', data);
  }

  async listWaivers(params: WaiverListParams): Promise<WaiverListResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('league_id', params.league_id);

    if (params.team_id) searchParams.set('team_id', params.team_id);
    if (params.limit) searchParams.set('limit', params.limit.toString());
    if (params.offset) searchParams.set('offset', params.offset.toString());

    return this.httpClient.get<WaiverListResponse>(`/waivers?${searchParams.toString()}`);
  }

  async getWaivers(leagueId: string, teamId?: string): Promise<WaiverListResponse> {
    return this.listWaivers({ league_id: leagueId, team_id: teamId });
  }

  async submitWaiverClaim(data: WaiverClaimParams): Promise<WaiverClaimResponse> {
    return this.httpClient.post<WaiverClaimResponse>('/waivers/claims', data);
  }

  async cancelWaiverClaim(claimId: string): Promise<void> {
    return this.httpClient.delete<void>(`/waivers/claims/${claimId}`);
  }

  async getWaiverClaim(claimId: string): Promise<WaiverClaimResponse> {
    return this.httpClient.get<WaiverClaimResponse>(`/waivers/claims/${claimId}`);
  }

  async getTeamWaiverClaims(leagueId: string, teamId: string): Promise<WaiverClaimResponse[]> {
    return this.httpClient.get<WaiverClaimResponse[]>(`/waivers/claims?league_id=${leagueId}&team_id=${teamId}`);
  }

  async processWaivers(leagueId: string): Promise<WaiverProcessingResult> {
    return this.httpClient.post<WaiverProcessingResult>(`/leagues/${leagueId}/waivers/process`);
  }

  // Utility methods
  setAuthToken(token: string): void {
    this.httpClient.setAuthToken(token);
  }

  clearAuthToken(): void {
    this.httpClient.clearAuthToken();
  }

  // Helper methods for waiver management
  getActiveClaims(claims: WaiverClaimResponse[]): WaiverClaimResponse[] {
    return claims.filter(claim => claim.status === 'pending');
  }

  getClaimsByPriority(claims: WaiverClaimResponse[]): WaiverClaimResponse[] {
    return [...claims].sort((a, b) => a.priority - b.priority);
  }

  hasActiveClaimForPlayer(claims: WaiverClaimResponse[], playerId: string): boolean {
    return claims.some(claim =>
      claim.add_player_id === playerId && claim.status === 'pending'
    );
  }

  calculateTotalBids(waivers: WaiverListResponse): number {
    return waivers.items.reduce((total, waiver) => total + waiver.bid, 0);
  }

  // Static factory method
  static create(httpClient: HttpClient, baseUrl?: string): WaiversService {
    return new WaiversService(httpClient, baseUrl);
  }

  // Get service definition for API contracts
  static getServiceDefinition(): ApiService {
    return ApiService.create('WaiversService', '/api')
      .post('/waivers/bids', {
        league_id: 'string',
        team_id: 'string',
        player_id: 'string',
        bid: 'number'
      }, {
        waiver_id: 'string',
        league_id: 'string',
        team_id: 'string',
        player_id: 'string',
        bid: 'number',
        status: 'string'
      }, true)
      .get('/waivers', true)
      .post('/waivers/claims', {
        league_id: 'string',
        team_id: 'string',
        add_player_id: 'string',
        drop_player_id: 'string',
        priority: 'number'
      }, undefined, true)
      .delete('/waivers/claims/{claimId}', true)
      .get('/waivers/claims/{claimId}', true)
      .get('/waivers/claims', true)
      .post('/leagues/{leagueId}/waivers/process', undefined, undefined, true)
      .build();
  }
}