import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface League {
  league_id: string;
  name: string;
  settings: {
    draft_type: string;
    scoring_type: string;
    roster_positions: string[];
    total_rosters: number;
  };
  roster_positions: string[];
  status: string;
  draft_id?: string;
  previous_league_id?: string;
  season: string;
  season_type: string;
  total_rosters: number;
  avatar?: string;
}

interface LeagueState {
  leagues: League[];
  selectedLeague: League | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setLeagues: (leagues: League[]) => void;
  setSelectedLeague: (league: League | null) => void;
  addLeague: (league: League) => void;
  updateLeague: (leagueId: string, updates: Partial<League>) => void;
  removeLeague: (leagueId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearState: () => void;
}

export const createLeagueStore = () => create<LeagueState>()(
  persist(
    (set, get) => ({
      leagues: [],
      selectedLeague: null,
      isLoading: false,
      error: null,

      setLeagues: (leagues) => set({ leagues }),

      setSelectedLeague: (league) => set({ selectedLeague: league }),

      addLeague: (league) => set((state) => ({
        leagues: [...state.leagues, league]
      })),

      updateLeague: (leagueId, updates) => set((state) => ({
        leagues: state.leagues.map(league =>
          league.league_id === leagueId ? { ...league, ...updates } : league
        ),
        selectedLeague: state.selectedLeague?.league_id === leagueId
          ? { ...state.selectedLeague, ...updates }
          : state.selectedLeague
      })),

      removeLeague: (leagueId) => set((state) => ({
        leagues: state.leagues.filter(league => league.league_id !== leagueId),
        selectedLeague: state.selectedLeague?.league_id === leagueId
          ? null
          : state.selectedLeague
      })),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      clearState: () => set({
        leagues: [],
        selectedLeague: null,
        isLoading: false,
        error: null
      })
    }),
    {
      name: 'league-store',
      // Only persist non-sensitive data
      partialize: (state) => ({
        leagues: state.leagues,
        selectedLeague: state.selectedLeague
      })
    }
  )
);

// Export singleton instance for easy usage
export const useLeagueStore = createLeagueStore();

// Helper functions for common operations
export const leagueStoreHelpers = {
  findLeagueById: (leagues: League[], leagueId: string) =>
    leagues.find(league => league.league_id === leagueId),

  getActiveLeagues: (leagues: League[]) =>
    leagues.filter(league => league.status === 'active'),

  getDraftingLeagues: (leagues: League[]) =>
    leagues.filter(league => league.status === 'drafting'),

  getLeaguesByStatus: (leagues: League[], status: string) =>
    leagues.filter(league => league.status === status),

  sortLeaguesByName: (leagues: League[]) =>
    [...leagues].sort((a, b) => a.name.localeCompare(b.name)),

  getLeagueRosterSize: (league: League) =>
    league.roster_positions?.length || league.settings?.roster_positions?.length || 0,

  isLeagueActive: (league: League) =>
    league.status === 'active',

  isLeagueDrafting: (league: League) =>
    league.status === 'drafting',

  canEditLeague: (league: League) =>
    ['pre_draft', 'drafting'].includes(league.status)
};