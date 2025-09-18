import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storeEvents, STORE_EVENTS } from './storeEvents';

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
  currentLeague: League | null; // Alias for selectedLeague to match tests
  isLoading: boolean;
  error: string | null;

  // Actions
  setLeagues: (leagues: League[]) => void;
  setSelectedLeague: (league: League | null) => void;
  setCurrentLeague: (league: League | null) => void; // Alias for setSelectedLeague
  addLeague: (league: League) => void;
  updateLeague: (leagueId: string, updates: Partial<League>) => void;
  removeLeague: (leagueId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearState: () => void;

  // Selectors expected by tests
  selectCurrentLeague: () => League | null;
  selectLeagueById: (id: string) => League | null;
}

export const createLeagueStore = () => {
  const store = create<LeagueState>()(
    persist(
      (set, get) => ({
      leagues: [],
      selectedLeague: null,
      currentLeague: null,
      isLoading: false,
      error: null,

      setLeagues: (leagues) => set({ leagues }),

      setSelectedLeague: (league) => set({ selectedLeague: league, currentLeague: league }),
      setCurrentLeague: (league) => set({ selectedLeague: league, currentLeague: league }),

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
        currentLeague: null,
        isLoading: false,
        error: null
      }),

      // Selectors
      selectCurrentLeague: () => get().selectedLeague,
      selectLeagueById: (id: string) => get().leagues.find(league => league.league_id === id) || null
      }),
      {
        name: 'league-store',
        // Only persist non-sensitive data
        partialize: (state) => ({
          leagues: state.leagues,
          selectedLeague: state.selectedLeague,
          currentLeague: state.currentLeague
        })
      }
    )
  );

  // Set up inter-store communication
  storeEvents.on(STORE_EVENTS.USER_LOGIN, () => {
    // When user logs in, trigger league data refresh
    store.getState().setLoading(true);
  });

  return store;
};

// Export singleton instance for easy usage
export const useLeagueStore = createLeagueStore();

// Mock React Query hook for testing
export const useLeaguesQuery = () => ({
  data: [],
  isLoading: false,
  error: null,
  refetch: () => Promise.resolve()
});

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