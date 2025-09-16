import { ApiService } from '../models/ApiService';

// Types extracted from frontend
export interface LeagueCreate {
  name: string;
  sport: string;
  league_type: string;
  season: string;
}

export interface LeagueResponse {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  invite_link?: string | null;
}

export interface JoinResponse {
  team_id: string;
  league_id: string;
  user_id: string;
  team_name: string;
}

export interface RuleUpdate {
  name: string;
  value: Record<string, unknown>;
}

export interface RuleOut {
  rule_id: string;
  league_id: string;
  name: string;
  value: Record<string, unknown>;
}

export interface LeaguePublic {
  league_id: string;
  name: string;
  sport: string;
  league_type: string;
  season: string;
  member_count: number;
  max_members: number;
}

export interface LeagueBrandingOut {
  league_id: string;
  primary_color?: string;
  secondary_color?: string;
  logo_url?: string;
  banner_url?: string;
}

export interface LeagueBrandingIn {
  primary_color?: string;
  secondary_color?: string;
  logo_url?: string;
  banner_url?: string;
}

export interface MeLeaguesResponse {
  items: Array<{
    league_id: string;
    name: string;
    sport: string;
    league_type: string;
    season: string;
    role: string;
    team_id: string;
  }>;
}

export interface MembersResponse {
  members: Array<{
    user_id: string;
    team_id: string;
    team_name: string;
    role: string;
    joined_at: string;
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

// LeaguesService class
export class LeaguesService {
  private httpClient: HttpClient;
  private baseUrl: string;

  constructor(httpClient: HttpClient, baseUrl: string = '') {
    this.httpClient = httpClient;
    this.baseUrl = baseUrl;
  }

  // API Methods extracted from frontend
  async createLeague(data: LeagueCreate): Promise<LeagueResponse> {
    return this.httpClient.post<LeagueResponse>('/leagues', data);
  }

  async joinLeague(leagueId: string): Promise<JoinResponse> {
    return this.httpClient.post<JoinResponse>(`/leagues/${leagueId}/join`);
  }

  async updateLeagueSettings(leagueId: string, data: RuleUpdate): Promise<RuleOut> {
    return this.httpClient.patch<RuleOut>(`/leagues/${leagueId}/settings`, data);
  }

  async getPublicLeague(leagueId: string): Promise<LeaguePublic> {
    return this.httpClient.get<LeaguePublic>(`/leagues/${leagueId}/public`);
  }

  async getLeagueBranding(leagueId: string): Promise<LeagueBrandingOut> {
    return this.httpClient.get<LeagueBrandingOut>(`/leagues/${leagueId}/branding`);
  }

  async updateLeagueBranding(leagueId: string, data: LeagueBrandingIn): Promise<LeagueBrandingOut> {
    return this.httpClient.patch<LeagueBrandingOut>(`/leagues/${leagueId}/branding`, data);
  }

  async getMyLeagues(): Promise<MeLeaguesResponse> {
    return this.httpClient.get<MeLeaguesResponse>('/leagues/me');
  }

  async getLeagueMembers(leagueId: string): Promise<MembersResponse> {
    return this.httpClient.get<MembersResponse>(`/leagues/${leagueId}/members`);
  }

  // Utility methods
  setAuthToken(token: string): void {
    this.httpClient.setAuthToken(token);
  }

  clearAuthToken(): void {
    this.httpClient.clearAuthToken();
  }

  // Static factory method
  static create(httpClient: HttpClient, baseUrl?: string): LeaguesService {
    return new LeaguesService(httpClient, baseUrl);
  }

  // Get service definition for API contracts
  static getServiceDefinition(): ApiService {
    return ApiService.create('LeaguesService', '/api')
      .post('/leagues', {
        name: 'string',
        sport: 'string',
        league_type: 'string',
        season: 'string'
      }, {
        league_id: 'string',
        name: 'string',
        sport: 'string',
        league_type: 'string',
        season: 'string',
        invite_link: 'string | null'
      }, true)
      .post('/leagues/{leagueId}/join', undefined, {
        team_id: 'string',
        league_id: 'string',
        user_id: 'string',
        team_name: 'string'
      }, true)
      .patch('/leagues/{leagueId}/settings', {
        name: 'string',
        value: 'Record<string, unknown>'
      }, {
        rule_id: 'string',
        league_id: 'string',
        name: 'string',
        value: 'Record<string, unknown>'
      }, true)
      .get('/leagues/{leagueId}/public')
      .get('/leagues/{leagueId}/branding', true)
      .patch('/leagues/{leagueId}/branding', {
        primary_color: 'string',
        secondary_color: 'string',
        logo_url: 'string',
        banner_url: 'string'
      }, undefined, true)
      .get('/leagues/me', true)
      .get('/leagues/{leagueId}/members', true)
      .build();
  }
}