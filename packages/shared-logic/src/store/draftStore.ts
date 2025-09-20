import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storeEvents, STORE_EVENTS } from './storeEvents';

export interface Player {
  id: string;
  external_id: string;
  name: string;
  position: string;
  team: string;
  rank: number;
  projected_points: number;
  injury_status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'ir';
  bye_week?: number;
  season_stats?: Record<string, number>;
}

export interface DraftPick {
  pick_number: number;
  team_id: string;
  player_id: string;
  player: Player;
  timestamp: string;
  is_auto_pick: boolean;
}

export interface DraftTeam {
  id: string;
  name: string;
  user_id: string;
  pick_order: number;
  roster: Player[];
  projected_total: number;
}

export interface Draft {
  id: string;
  league_id: string;
  status: 'pending' | 'in_progress' | 'paused' | 'completed';
  current_pick: number;
  current_team_id: string;
  total_picks: number;
  picks: DraftPick[];
  teams: DraftTeam[];
  timer_seconds: number;
  time_remaining: number;
  pick_time_limit: number;
  snake_draft: boolean;
  auto_pick_enabled: boolean;
  started_at?: string;
  completed_at?: string;
}

export interface DraftFilters {
  position: string;
  team: string;
  injury_status: string;
  search: string;
  available_only: boolean;
}

interface DraftState {
  draft: Draft | null;
  availablePlayers: Player[];
  draftedPlayers: Player[];
  filters: DraftFilters;
  playerRankings: Player[];
  myTeam: DraftTeam | null;
  isLoading: boolean;
  error: string | null;
  timerActive: boolean;
  currentPickPlayer: Player | null;

  // Actions
  setDraft: (draft: Draft | null) => void;
  setAvailablePlayers: (players: Player[]) => void;
  setDraftedPlayers: (players: Player[]) => void;
  setFilters: (filters: Partial<DraftFilters>) => void;
  setPlayerRankings: (players: Player[]) => void;
  setMyTeam: (team: DraftTeam | null) => void;

  // Draft actions
  makeDraftPick: (playerId: string, teamId: string) => void;
  addDraftPick: (pick: DraftPick) => void;
  updateDraftStatus: (status: Draft['status']) => void;
  setCurrentPick: (pickNumber: number, teamId: string) => void;
  updateTimer: (timeRemaining: number) => void;
  setTimerActive: (active: boolean) => void;
  setCurrentPickPlayer: (player: Player | null) => void;

  // Player actions
  movePlayerToDrafted: (player: Player) => void;
  updatePlayerRanking: (playerId: string, newRank: number) => void;
  togglePlayerWatchlist: (playerId: string) => void;

  // Utility actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearState: () => void;

  // Selectors
  getAvailablePlayersByPosition: (position: string) => Player[];
  getFilteredPlayers: () => Player[];
  getTeamByPickOrder: (pickOrder: number) => DraftTeam | null;
  isMyTurn: () => boolean;
  getNextPickTeam: () => DraftTeam | null;
  getCurrentRound: () => number;
  getPicksInCurrentRound: () => DraftPick[];
  getTeamRoster: (teamId: string) => Player[];
  getPositionCounts: (teamId: string) => Record<string, number>;
}

const defaultFilters: DraftFilters = {
  position: 'ALL',
  team: 'ALL',
  injury_status: 'ALL',
  search: '',
  available_only: true
};

export const createDraftStore = () => {
  const store = create<DraftState>()(
    persist(
      (set, get) => ({
        draft: null,
        availablePlayers: [],
        draftedPlayers: [],
        filters: defaultFilters,
        playerRankings: [],
        myTeam: null,
        isLoading: false,
        error: null,
        timerActive: false,
        currentPickPlayer: null,

        setDraft: (draft) => set({ draft }),

        setAvailablePlayers: (players) => set({ availablePlayers: players }),

        setDraftedPlayers: (players) => set({ draftedPlayers: players }),

        setFilters: (filters) => set((state) => ({
          filters: { ...state.filters, ...filters }
        })),

        setPlayerRankings: (players) => set({ playerRankings: players }),

        setMyTeam: (team) => set({ myTeam: team }),

        makeDraftPick: (playerId, teamId) => {
          const state = get();
          if (!state.draft) return;

          const player = state.availablePlayers.find(p => p.id === playerId);
          if (!player) return;

          const pick: DraftPick = {
            pick_number: state.draft.current_pick,
            team_id: teamId,
            player_id: playerId,
            player,
            timestamp: new Date().toISOString(),
            is_auto_pick: false
          };

          set((state) => ({
            draft: state.draft ? {
              ...state.draft,
              picks: [...state.draft.picks, pick],
              current_pick: state.draft.current_pick + 1
            } : null,
            availablePlayers: state.availablePlayers.filter(p => p.id !== playerId),
            draftedPlayers: [...state.draftedPlayers, player]
          }));

          // Emit event for other components
          storeEvents.emit(STORE_EVENTS.DRAFT_PICK_MADE, pick);
        },

        addDraftPick: (pick) => set((state) => ({
          draft: state.draft ? {
            ...state.draft,
            picks: [...state.draft.picks, pick]
          } : null,
          availablePlayers: state.availablePlayers.filter(p => p.id !== pick.player_id),
          draftedPlayers: [...state.draftedPlayers, pick.player]
        })),

        updateDraftStatus: (status) => set((state) => ({
          draft: state.draft ? { ...state.draft, status } : null
        })),

        setCurrentPick: (pickNumber, teamId) => set((state) => ({
          draft: state.draft ? {
            ...state.draft,
            current_pick: pickNumber,
            current_team_id: teamId
          } : null
        })),

        updateTimer: (timeRemaining) => set((state) => ({
          draft: state.draft ? { ...state.draft, time_remaining: timeRemaining } : null
        })),

        setTimerActive: (active) => set({ timerActive: active }),

        setCurrentPickPlayer: (player) => set({ currentPickPlayer: player }),

        movePlayerToDrafted: (player) => set((state) => ({
          availablePlayers: state.availablePlayers.filter(p => p.id !== player.id),
          draftedPlayers: [...state.draftedPlayers, player]
        })),

        updatePlayerRanking: (playerId, newRank) => set((state) => ({
          playerRankings: state.playerRankings.map(player =>
            player.id === playerId ? { ...player, rank: newRank } : player
          )
        })),

        togglePlayerWatchlist: (playerId) => {
          // Implementation would depend on watchlist structure
          console.log('Toggle watchlist for player:', playerId);
        },

        setLoading: (loading) => set({ isLoading: loading }),

        setError: (error) => set({ error }),

        clearState: () => set({
          draft: null,
          availablePlayers: [],
          draftedPlayers: [],
          filters: defaultFilters,
          playerRankings: [],
          myTeam: null,
          isLoading: false,
          error: null,
          timerActive: false,
          currentPickPlayer: null
        }),

        // Selectors
        getAvailablePlayersByPosition: (position) => {
          const state = get();
          return state.availablePlayers.filter(player =>
            position === 'ALL' || player.position === position
          );
        },

        getFilteredPlayers: () => {
          const state = get();
          const { filters, availablePlayers } = state;

          return availablePlayers.filter(player => {
            if (filters.position !== 'ALL' && player.position !== filters.position) return false;
            if (filters.team !== 'ALL' && player.team !== filters.team) return false;
            if (filters.injury_status !== 'ALL' && player.injury_status !== filters.injury_status) return false;
            if (filters.search && !player.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
            return true;
          });
        },

        getTeamByPickOrder: (pickOrder) => {
          const state = get();
          return state.draft?.teams.find(team => team.pick_order === pickOrder) || null;
        },

        isMyTurn: () => {
          const state = get();
          return state.draft?.current_team_id === state.myTeam?.id;
        },

        getNextPickTeam: () => {
          const state = get();
          if (!state.draft) return null;

          const nextPick = state.draft.current_pick + 1;
          const totalTeams = state.draft.teams.length;
          const round = Math.ceil(nextPick / totalTeams);

          let pickOrder: number;
          if (state.draft.snake_draft && round % 2 === 0) {
            // Reverse order for even rounds in snake draft
            pickOrder = totalTeams - ((nextPick - 1) % totalTeams);
          } else {
            pickOrder = ((nextPick - 1) % totalTeams) + 1;
          }

          return state.draft.teams.find(team => team.pick_order === pickOrder) || null;
        },

        getCurrentRound: () => {
          const state = get();
          if (!state.draft) return 1;
          return Math.ceil(state.draft.current_pick / state.draft.teams.length);
        },

        getPicksInCurrentRound: () => {
          const state = get();
          if (!state.draft) return [];

          const currentRound = get().getCurrentRound();
          const teamsCount = state.draft.teams.length;
          const roundStartPick = (currentRound - 1) * teamsCount + 1;
          const roundEndPick = currentRound * teamsCount;

          return state.draft.picks.filter(pick =>
            pick.pick_number >= roundStartPick && pick.pick_number <= roundEndPick
          );
        },

        getTeamRoster: (teamId) => {
          const state = get();
          if (!state.draft) return [];

          return state.draft.picks
            .filter(pick => pick.team_id === teamId)
            .map(pick => pick.player);
        },

        getPositionCounts: (teamId) => {
          const roster = get().getTeamRoster(teamId);
          const counts: Record<string, number> = {};

          roster.forEach(player => {
            counts[player.position] = (counts[player.position] || 0) + 1;
          });

          return counts;
        }
      }),
      {
        name: 'draft-store',
        // Only persist essential data, not real-time state
        partialize: (state) => ({
          filters: state.filters,
          myTeam: state.myTeam
        })
      }
    )
  );

  // Set up inter-store communication
  storeEvents.on(STORE_EVENTS.USER_LOGIN, () => {
    store.getState().clearState();
  });

  return store;
};

// Export singleton instance
export const useDraftStore = createDraftStore();

// Helper functions for draft operations
export const draftStoreHelpers = {
  calculateDraftProgress: (draft: Draft) => {
    if (!draft) return 0;
    return (draft.picks.length / draft.total_picks) * 100;
  },

  getTimeRemaining: (draft: Draft) => {
    if (!draft || draft.status !== 'in_progress') return 0;
    return Math.max(0, draft.time_remaining);
  },

  formatTimeRemaining: (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  },

  isPickExpired: (draft: Draft) => {
    return draft.time_remaining <= 0 && draft.status === 'in_progress';
  },

  getPlayersByPosition: (players: Player[], position: string) => {
    return players.filter(player => player.position === position);
  },

  sortPlayersByRank: (players: Player[]) => {
    return [...players].sort((a, b) => a.rank - b.rank);
  },

  sortPlayersByProjection: (players: Player[]) => {
    return [...players].sort((a, b) => b.projected_points - a.projected_points);
  },

  getTopAvailableByPosition: (players: Player[], position: string, limit = 5) => {
    return draftStoreHelpers
      .getPlayersByPosition(players, position)
      .slice(0, limit);
  },

  calculateTeamStrength: (roster: Player[]) => {
    return roster.reduce((total, player) => total + player.projected_points, 0);
  },

  getPositionNeeds: (roster: Player[]) => {
    const positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST'];
    const counts = roster.reduce((acc, player) => {
      acc[player.position] = (acc[player.position] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return positions.filter(pos => (counts[pos] || 0) < 2); // Basic position need logic
  },

  isDraftComplete: (draft: Draft) => {
    return draft.status === 'completed' || draft.picks.length >= draft.total_picks;
  },

  getAveragePickTime: (picks: DraftPick[]) => {
    if (picks.length <= 1) return 0;

    let totalTime = 0;
    for (let i = 1; i < picks.length; i++) {
      const prevTime = new Date(picks[i - 1].timestamp).getTime();
      const currTime = new Date(picks[i].timestamp).getTime();
      totalTime += currTime - prevTime;
    }

    return totalTime / (picks.length - 1) / 1000; // Return in seconds
  }
};