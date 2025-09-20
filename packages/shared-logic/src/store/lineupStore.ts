import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storeEvents, STORE_EVENTS } from './storeEvents';

export interface LineupPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  opponent?: string;
  game_time?: string;
  projected_points: number;
  actual_points?: number;
  injury_status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'ir';
  is_locked: boolean;
  bye_week?: number;
}

export interface LineupSlot {
  position: string;
  player: LineupPlayer | null;
  is_flex: boolean;
  is_required: boolean;
  slot_index: number;
}

export interface Lineup {
  id: string;
  team_id: string;
  week: number;
  year: number;
  slots: LineupSlot[];
  projected_points: number;
  actual_points?: number;
  is_locked: boolean;
  is_valid: boolean;
  last_updated: string;
  version: number;
}

export interface LineupValidation {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  missing_positions: string[];
  bench_players: LineupPlayer[];
}

export interface LineupOptimization {
  suggested_lineup: LineupSlot[];
  projected_improvement: number;
  changes: Array<{
    slot_index: number;
    current_player: LineupPlayer | null;
    suggested_player: LineupPlayer;
    reason: string;
  }>;
}

interface LineupState {
  currentLineup: Lineup | null;
  availablePlayers: LineupPlayer[];
  benchPlayers: LineupPlayer[];
  currentWeek: number;
  validation: LineupValidation | null;
  optimization: LineupOptimization | null;
  isLoading: boolean;
  isSubmitting: boolean;
  isDirty: boolean;
  error: string | null;
  lastSaved: string | null;

  // Actions
  setCurrentLineup: (lineup: Lineup | null) => void;
  setAvailablePlayers: (players: LineupPlayer[]) => void;
  setBenchPlayers: (players: LineupPlayer[]) => void;
  setCurrentWeek: (week: number) => void;
  setValidation: (validation: LineupValidation | null) => void;
  setOptimization: (optimization: LineupOptimization | null) => void;

  // Lineup modification actions
  setPlayerInSlot: (slotIndex: number, player: LineupPlayer | null) => void;
  swapPlayers: (fromSlotIndex: number, toSlotIndex: number) => void;
  movePlayerToBench: (slotIndex: number) => void;
  movePlayerFromBench: (playerId: string, slotIndex: number) => void;
  clearSlot: (slotIndex: number) => void;
  autoFillLineup: () => void;
  optimizeLineup: () => void;

  // Lineup operations
  validateLineup: () => LineupValidation;
  saveLineup: () => Promise<void>;
  resetLineup: () => void;
  lockLineup: () => void;
  unlockLineup: () => void;

  // Utility actions
  setLoading: (loading: boolean) => void;
  setSubmitting: (submitting: boolean) => void;
  setDirty: (dirty: boolean) => void;
  setError: (error: string | null) => void;
  setLastSaved: (timestamp: string) => void;
  clearState: () => void;

  // Selectors
  getStartingPlayers: () => LineupPlayer[];
  getBenchPlayers: () => LineupPlayer[];
  getPlayerByPosition: (position: string) => LineupPlayer[];
  getAvailableSlots: (position: string) => LineupSlot[];
  canPlayerFitInSlot: (player: LineupPlayer, slot: LineupSlot) => boolean;
  getTotalProjectedPoints: () => number;
  getTotalActualPoints: () => number;
  hasRequiredPlayers: () => boolean;
  getLineupStrengths: () => string[];
  getLineupWeaknesses: () => string[];
}

const createDefaultLineup = (teamId: string, week: number): Lineup => ({
  id: `lineup-${teamId}-${week}`,
  team_id: teamId,
  week,
  year: new Date().getFullYear(),
  slots: [
    { position: 'QB', player: null, is_flex: false, is_required: true, slot_index: 0 },
    { position: 'RB', player: null, is_flex: false, is_required: true, slot_index: 1 },
    { position: 'RB', player: null, is_flex: false, is_required: true, slot_index: 2 },
    { position: 'WR', player: null, is_flex: false, is_required: true, slot_index: 3 },
    { position: 'WR', player: null, is_flex: false, is_required: true, slot_index: 4 },
    { position: 'TE', player: null, is_flex: false, is_required: true, slot_index: 5 },
    { position: 'FLEX', player: null, is_flex: true, is_required: true, slot_index: 6 },
    { position: 'K', player: null, is_flex: false, is_required: true, slot_index: 7 },
    { position: 'DST', player: null, is_flex: false, is_required: true, slot_index: 8 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 9 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 10 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 11 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 12 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 13 },
    { position: 'BENCH', player: null, is_flex: false, is_required: false, slot_index: 14 },
  ],
  projected_points: 0,
  is_locked: false,
  is_valid: false,
  last_updated: new Date().toISOString(),
  version: 1
});

export const createLineupStore = () => {
  const store = create<LineupState>()(
    persist(
      (set, get) => ({
        currentLineup: null,
        availablePlayers: [],
        benchPlayers: [],
        currentWeek: 1,
        validation: null,
        optimization: null,
        isLoading: false,
        isSubmitting: false,
        isDirty: false,
        error: null,
        lastSaved: null,

        setCurrentLineup: (lineup) => set({ currentLineup: lineup, isDirty: false }),

        setAvailablePlayers: (players) => set({ availablePlayers: players }),

        setBenchPlayers: (players) => set({ benchPlayers: players }),

        setCurrentWeek: (week) => set({ currentWeek: week }),

        setValidation: (validation) => set({ validation }),

        setOptimization: (optimization) => set({ optimization }),

        setPlayerInSlot: (slotIndex, player) => {
          const state = get();
          if (!state.currentLineup) return;

          const newLineup = { ...state.currentLineup };
          newLineup.slots = [...newLineup.slots];
          newLineup.slots[slotIndex] = { ...newLineup.slots[slotIndex], player };
          newLineup.last_updated = new Date().toISOString();
          newLineup.version += 1;

          set({
            currentLineup: newLineup,
            isDirty: true,
            validation: null // Clear validation when lineup changes
          });

          // Auto-validate after changes
          setTimeout(() => get().validateLineup(), 100);
        },

        swapPlayers: (fromSlotIndex, toSlotIndex) => {
          const state = get();
          if (!state.currentLineup) return;

          const newLineup = { ...state.currentLineup };
          newLineup.slots = [...newLineup.slots];

          const fromPlayer = newLineup.slots[fromSlotIndex].player;
          const toPlayer = newLineup.slots[toSlotIndex].player;

          newLineup.slots[fromSlotIndex] = { ...newLineup.slots[fromSlotIndex], player: toPlayer };
          newLineup.slots[toSlotIndex] = { ...newLineup.slots[toSlotIndex], player: fromPlayer };
          newLineup.last_updated = new Date().toISOString();
          newLineup.version += 1;

          set({
            currentLineup: newLineup,
            isDirty: true,
            validation: null
          });

          setTimeout(() => get().validateLineup(), 100);
        },

        movePlayerToBench: (slotIndex) => {
          const state = get();
          if (!state.currentLineup) return;

          const player = state.currentLineup.slots[slotIndex].player;
          if (!player) return;

          // Find first empty bench slot
          const benchSlotIndex = state.currentLineup.slots.findIndex(
            slot => slot.position === 'BENCH' && !slot.player
          );

          if (benchSlotIndex !== -1) {
            get().setPlayerInSlot(slotIndex, null);
            get().setPlayerInSlot(benchSlotIndex, player);
          }
        },

        movePlayerFromBench: (playerId, slotIndex) => {
          const state = get();
          if (!state.currentLineup) return;

          // Find player on bench
          const benchSlotIndex = state.currentLineup.slots.findIndex(
            slot => slot.player?.id === playerId
          );

          if (benchSlotIndex !== -1) {
            const player = state.currentLineup.slots[benchSlotIndex].player;
            get().setPlayerInSlot(benchSlotIndex, null);
            get().setPlayerInSlot(slotIndex, player);
          }
        },

        clearSlot: (slotIndex) => {
          get().setPlayerInSlot(slotIndex, null);
        },

        autoFillLineup: () => {
          const state = get();
          if (!state.currentLineup || !state.availablePlayers.length) return;

          const newLineup = { ...state.currentLineup };
          newLineup.slots = [...newLineup.slots];

          // Sort available players by projected points
          const sortedPlayers = [...state.availablePlayers].sort(
            (a, b) => b.projected_points - a.projected_points
          );

          // Fill required positions first
          newLineup.slots.forEach((slot, index) => {
            if (slot.is_required && !slot.player) {
              const availablePlayer = sortedPlayers.find(player =>
                get().canPlayerFitInSlot(player, slot) &&
                !newLineup.slots.some(s => s.player?.id === player.id)
              );

              if (availablePlayer) {
                newLineup.slots[index] = { ...slot, player: availablePlayer };
              }
            }
          });

          newLineup.last_updated = new Date().toISOString();
          newLineup.version += 1;

          set({
            currentLineup: newLineup,
            isDirty: true,
            validation: null
          });

          setTimeout(() => get().validateLineup(), 100);
        },

        optimizeLineup: () => {
          // This would integrate with the API client's optimization endpoint
          const state = get();
          if (!state.currentLineup) return;

          // For now, just trigger auto-fill as a basic optimization
          get().autoFillLineup();
        },

        validateLineup: () => {
          const state = get();
          if (!state.currentLineup) {
            return { is_valid: false, errors: ['No lineup set'], warnings: [], missing_positions: [], bench_players: [] };
          }

          const errors: string[] = [];
          const warnings: string[] = [];
          const missing_positions: string[] = [];
          const bench_players: LineupPlayer[] = [];

          // Check required positions
          state.currentLineup.slots.forEach(slot => {
            if (slot.is_required && !slot.player) {
              missing_positions.push(slot.position);
              errors.push(`Missing required ${slot.position} player`);
            }

            if (slot.player) {
              // Check for injured players
              if (slot.player.injury_status === 'out' || slot.player.injury_status === 'ir') {
                errors.push(`${slot.player.name} is ${slot.player.injury_status}`);
              }

              // Check for bye week
              if (slot.player.bye_week === state.currentWeek) {
                warnings.push(`${slot.player.name} is on bye week`);
              }

              // Collect bench players
              if (slot.position === 'BENCH' && slot.player) {
                bench_players.push(slot.player);
              }
            }
          });

          const validation: LineupValidation = {
            is_valid: errors.length === 0,
            errors,
            warnings,
            missing_positions,
            bench_players
          };

          set({ validation });
          return validation;
        },

        saveLineup: async () => {
          const state = get();
          if (!state.currentLineup || !state.isDirty) return;

          set({ isSubmitting: true, error: null });

          try {
            // This would call the API client to save the lineup
            // await ultimateFantasyClient.lineups.update(...)

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            set({
              isDirty: false,
              lastSaved: new Date().toISOString(),
              isSubmitting: false
            });

            storeEvents.emit(STORE_EVENTS.LINEUP_SAVED, state.currentLineup);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to save lineup',
              isSubmitting: false
            });
          }
        },

        resetLineup: () => {
          const state = get();
          if (!state.currentLineup) return;

          const resetLineup = createDefaultLineup(state.currentLineup.team_id, state.currentWeek);
          set({
            currentLineup: resetLineup,
            isDirty: true,
            validation: null
          });
        },

        lockLineup: () => {
          const state = get();
          if (!state.currentLineup) return;

          set({
            currentLineup: {
              ...state.currentLineup,
              is_locked: true,
              last_updated: new Date().toISOString()
            }
          });
        },

        unlockLineup: () => {
          const state = get();
          if (!state.currentLineup) return;

          set({
            currentLineup: {
              ...state.currentLineup,
              is_locked: false,
              last_updated: new Date().toISOString()
            }
          });
        },

        setLoading: (loading) => set({ isLoading: loading }),

        setSubmitting: (submitting) => set({ isSubmitting: submitting }),

        setDirty: (dirty) => set({ isDirty: dirty }),

        setError: (error) => set({ error }),

        setLastSaved: (timestamp) => set({ lastSaved: timestamp }),

        clearState: () => set({
          currentLineup: null,
          availablePlayers: [],
          benchPlayers: [],
          validation: null,
          optimization: null,
          isLoading: false,
          isSubmitting: false,
          isDirty: false,
          error: null,
          lastSaved: null
        }),

        // Selectors
        getStartingPlayers: () => {
          const state = get();
          if (!state.currentLineup) return [];

          return state.currentLineup.slots
            .filter(slot => slot.position !== 'BENCH' && slot.player)
            .map(slot => slot.player!)
            .filter(Boolean);
        },

        getBenchPlayers: () => {
          const state = get();
          if (!state.currentLineup) return [];

          return state.currentLineup.slots
            .filter(slot => slot.position === 'BENCH' && slot.player)
            .map(slot => slot.player!)
            .filter(Boolean);
        },

        getPlayerByPosition: (position) => {
          const state = get();
          if (!state.currentLineup) return [];

          return state.currentLineup.slots
            .filter(slot => slot.position === position && slot.player)
            .map(slot => slot.player!)
            .filter(Boolean);
        },

        getAvailableSlots: (position) => {
          const state = get();
          if (!state.currentLineup) return [];

          return state.currentLineup.slots.filter(slot =>
            !slot.player && (
              slot.position === position ||
              (slot.is_flex && ['RB', 'WR', 'TE'].includes(position))
            )
          );
        },

        canPlayerFitInSlot: (player, slot) => {
          if (slot.player) return false; // Slot is occupied

          if (slot.position === 'BENCH') return true; // Bench accepts any player

          if (slot.is_flex) {
            return ['RB', 'WR', 'TE'].includes(player.position);
          }

          return slot.position === player.position;
        },

        getTotalProjectedPoints: () => {
          const startingPlayers = get().getStartingPlayers();
          return startingPlayers.reduce((total, player) => total + player.projected_points, 0);
        },

        getTotalActualPoints: () => {
          const startingPlayers = get().getStartingPlayers();
          return startingPlayers.reduce((total, player) => total + (player.actual_points || 0), 0);
        },

        hasRequiredPlayers: () => {
          const state = get();
          if (!state.currentLineup) return false;

          return state.currentLineup.slots
            .filter(slot => slot.is_required)
            .every(slot => slot.player !== null);
        },

        getLineupStrengths: () => {
          const strengths: string[] = [];
          const players = get().getStartingPlayers();

          // Analyze by position
          const qbs = players.filter(p => p.position === 'QB');
          const rbs = players.filter(p => p.position === 'RB');
          const wrs = players.filter(p => p.position === 'WR');
          const tes = players.filter(p => p.position === 'TE');

          if (qbs.some(p => p.projected_points > 20)) {
            strengths.push('Strong QB play');
          }

          if (rbs.length >= 2 && rbs.every(p => p.projected_points > 15)) {
            strengths.push('Deep RB depth');
          }

          if (wrs.length >= 2 && wrs.every(p => p.projected_points > 12)) {
            strengths.push('Reliable WR corps');
          }

          return strengths;
        },

        getLineupWeaknesses: () => {
          const weaknesses: string[] = [];
          const validation = get().validation;

          if (validation?.errors.length) {
            weaknesses.push(...validation.errors);
          }

          if (validation?.warnings.length) {
            weaknesses.push(...validation.warnings);
          }

          return weaknesses;
        }
      }),
      {
        name: 'lineup-store',
        // Persist lineup state but not loading states
        partialize: (state) => ({
          currentLineup: state.currentLineup,
          currentWeek: state.currentWeek,
          isDirty: state.isDirty,
          lastSaved: state.lastSaved
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
export const useLineupStore = createLineupStore();

// Helper functions for lineup operations
export const lineupStoreHelpers = {
  createEmptyLineup: (teamId: string, week: number) => createDefaultLineup(teamId, week),

  calculateProjectedTotal: (slots: LineupSlot[]) => {
    return slots
      .filter(slot => slot.position !== 'BENCH' && slot.player)
      .reduce((total, slot) => total + (slot.player?.projected_points || 0), 0);
  },

  getOptimalLineupOrder: (players: LineupPlayer[]) => {
    return [...players].sort((a, b) => b.projected_points - a.projected_points);
  },

  findBestFit: (player: LineupPlayer, slots: LineupSlot[]) => {
    // Find the best slot for a player
    const availableSlots = slots.filter(slot => !slot.player);

    // Prefer exact position match
    const exactMatch = availableSlots.find(slot => slot.position === player.position);
    if (exactMatch) return exactMatch;

    // Then flex positions
    const flexMatch = availableSlots.find(slot =>
      slot.is_flex && ['RB', 'WR', 'TE'].includes(player.position)
    );
    if (flexMatch) return flexMatch;

    // Finally bench
    return availableSlots.find(slot => slot.position === 'BENCH');
  },

  getPositionDepth: (players: LineupPlayer[], position: string) => {
    return players.filter(p => p.position === position).length;
  },

  isLineupLocked: (lineup: Lineup) => {
    return lineup.is_locked || lineup.slots.some(slot =>
      slot.player?.is_locked
    );
  },

  getLineupScore: (lineup: Lineup) => {
    if (lineup.actual_points !== undefined) return lineup.actual_points;
    return lineup.projected_points;
  },

  compareLineups: (lineup1: Lineup, lineup2: Lineup) => {
    const score1 = lineupStoreHelpers.getLineupScore(lineup1);
    const score2 = lineupStoreHelpers.getLineupScore(lineup2);
    return score2 - score1; // Higher score first
  }
};