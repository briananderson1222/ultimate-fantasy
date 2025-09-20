import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storeEvents, STORE_EVENTS } from './storeEvents';

export interface TradePlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  trade_value: number;
  injury_status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'ir';
  bye_week?: number;
  recent_performance: number[];
  season_stats?: Record<string, number>;
}

export interface TradeProposal {
  id: string;
  league_id: string;
  proposing_team_id: string;
  receiving_team_id: string;
  proposed_players: TradePlayer[];
  requested_players: TradePlayer[];
  status: 'pending' | 'accepted' | 'rejected' | 'expired' | 'cancelled';
  evaluation: TradeEvaluation | null;
  message?: string;
  expires_at: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

export interface TradeEvaluation {
  overall_score: number;
  fairness: 'heavily_favors_team_a' | 'favors_team_a' | 'fair' | 'favors_team_b' | 'heavily_favors_team_b';
  team_a_value: number;
  team_b_value: number;
  value_difference: number;
  analysis: {
    summary: string;
    team_a_gains: string[];
    team_a_losses: string[];
    team_b_gains: string[];
    team_b_losses: string[];
    recommendations: string[];
  };
  position_impact: Record<string, {
    team_a_change: number;
    team_b_change: number;
  }>;
  risk_factors: string[];
  confidence: number;
}

export interface TradeFilters {
  status: string;
  team: string;
  position: string;
  date_range: 'all' | 'week' | 'month';
  sort_by: 'date' | 'value' | 'fairness';
  sort_order: 'asc' | 'desc';
}

export interface TradeNotification {
  id: string;
  type: 'proposal_received' | 'proposal_accepted' | 'proposal_rejected' | 'proposal_expired';
  trade_id: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface TradingState {
  // Active trade being constructed
  currentTrade: {
    proposing_team_id: string;
    receiving_team_id: string;
    proposed_players: TradePlayer[];
    requested_players: TradePlayer[];
    message: string;
  } | null;

  // Trade data
  allTrades: TradeProposal[];
  sentTrades: TradeProposal[];
  receivedTrades: TradeProposal[];
  availablePlayers: TradePlayer[];
  teamRosters: Record<string, TradePlayer[]>;

  // UI state
  filters: TradeFilters;
  selectedTrade: TradeProposal | null;
  notifications: TradeNotification[];
  isLoading: boolean;
  isEvaluating: boolean;
  isSubmitting: boolean;
  error: string | null;

  // Current evaluation
  currentEvaluation: TradeEvaluation | null;

  // Actions - Trade Construction
  initializeTrade: (proposingTeamId: string, receivingTeamId: string) => void;
  addProposedPlayer: (player: TradePlayer) => void;
  removeProposedPlayer: (playerId: string) => void;
  addRequestedPlayer: (player: TradePlayer) => void;
  removeRequestedPlayer: (playerId: string) => void;
  setTradeMessage: (message: string) => void;
  clearCurrentTrade: () => void;

  // Actions - Trade Management
  setAllTrades: (trades: TradeProposal[]) => void;
  setSentTrades: (trades: TradeProposal[]) => void;
  setReceivedTrades: (trades: TradeProposal[]) => void;
  addTrade: (trade: TradeProposal) => void;
  updateTrade: (tradeId: string, updates: Partial<TradeProposal>) => void;
  removeTrade: (tradeId: string) => void;

  // Actions - Player Management
  setAvailablePlayers: (players: TradePlayer[]) => void;
  setTeamRosters: (rosters: Record<string, TradePlayer[]>) => void;
  updatePlayerValue: (playerId: string, newValue: number) => void;

  // Actions - Trade Operations
  proposeTrade: () => Promise<void>;
  acceptTrade: (tradeId: string) => Promise<void>;
  rejectTrade: (tradeId: string, reason?: string) => Promise<void>;
  cancelTrade: (tradeId: string) => Promise<void>;
  evaluateTrade: () => Promise<void>;

  // Actions - UI State
  setFilters: (filters: Partial<TradeFilters>) => void;
  setSelectedTrade: (trade: TradeProposal | null) => void;
  setNotifications: (notifications: TradeNotification[]) => void;
  addNotification: (notification: Omit<TradeNotification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (notificationId: string) => void;
  clearNotifications: () => void;

  // Actions - Loading States
  setLoading: (loading: boolean) => void;
  setEvaluating: (evaluating: boolean) => void;
  setSubmitting: (submitting: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentEvaluation: (evaluation: TradeEvaluation | null) => void;
  clearState: () => void;

  // Selectors
  getTradesByStatus: (status: string) => TradeProposal[];
  getFilteredTrades: () => TradeProposal[];
  getTeamPlayers: (teamId: string) => TradePlayer[];
  getTradablePlayersForTeam: (teamId: string) => TradePlayer[];
  getRecentTrades: (limit?: number) => TradeProposal[];
  getPendingTradesCount: () => number;
  getUnreadNotificationsCount: () => number;
  isTradeValid: () => boolean;
  getCurrentTradeValue: () => { proposed: number; requested: number };
}

const defaultFilters: TradeFilters = {
  status: 'all',
  team: 'all',
  position: 'all',
  date_range: 'all',
  sort_by: 'date',
  sort_order: 'desc'
};

export const createTradingStore = () => {
  const store = create<TradingState>()(
    persist(
      (set, get) => ({
        currentTrade: null,
        allTrades: [],
        sentTrades: [],
        receivedTrades: [],
        availablePlayers: [],
        teamRosters: {},
        filters: defaultFilters,
        selectedTrade: null,
        notifications: [],
        isLoading: false,
        isEvaluating: false,
        isSubmitting: false,
        error: null,
        currentEvaluation: null,

        initializeTrade: (proposingTeamId, receivingTeamId) => set({
          currentTrade: {
            proposing_team_id: proposingTeamId,
            receiving_team_id: receivingTeamId,
            proposed_players: [],
            requested_players: [],
            message: ''
          },
          currentEvaluation: null,
          error: null
        }),

        addProposedPlayer: (player) => {
          const state = get();
          if (!state.currentTrade) return;

          const updatedTrade = {
            ...state.currentTrade,
            proposed_players: [...state.currentTrade.proposed_players, player]
          };

          set({ currentTrade: updatedTrade, currentEvaluation: null });
        },

        removeProposedPlayer: (playerId) => {
          const state = get();
          if (!state.currentTrade) return;

          const updatedTrade = {
            ...state.currentTrade,
            proposed_players: state.currentTrade.proposed_players.filter(p => p.id !== playerId)
          };

          set({ currentTrade: updatedTrade, currentEvaluation: null });
        },

        addRequestedPlayer: (player) => {
          const state = get();
          if (!state.currentTrade) return;

          const updatedTrade = {
            ...state.currentTrade,
            requested_players: [...state.currentTrade.requested_players, player]
          };

          set({ currentTrade: updatedTrade, currentEvaluation: null });
        },

        removeRequestedPlayer: (playerId) => {
          const state = get();
          if (!state.currentTrade) return;

          const updatedTrade = {
            ...state.currentTrade,
            requested_players: state.currentTrade.requested_players.filter(p => p.id !== playerId)
          };

          set({ currentTrade: updatedTrade, currentEvaluation: null });
        },

        setTradeMessage: (message) => {
          const state = get();
          if (!state.currentTrade) return;

          set({
            currentTrade: { ...state.currentTrade, message }
          });
        },

        clearCurrentTrade: () => set({
          currentTrade: null,
          currentEvaluation: null
        }),

        setAllTrades: (trades) => set({ allTrades: trades }),

        setSentTrades: (trades) => set({ sentTrades: trades }),

        setReceivedTrades: (trades) => set({ receivedTrades: trades }),

        addTrade: (trade) => set((state) => ({
          allTrades: [...state.allTrades, trade]
        })),

        updateTrade: (tradeId, updates) => set((state) => ({
          allTrades: state.allTrades.map(trade =>
            trade.id === tradeId ? { ...trade, ...updates } : trade
          ),
          sentTrades: state.sentTrades.map(trade =>
            trade.id === tradeId ? { ...trade, ...updates } : trade
          ),
          receivedTrades: state.receivedTrades.map(trade =>
            trade.id === tradeId ? { ...trade, ...updates } : trade
          )
        })),

        removeTrade: (tradeId) => set((state) => ({
          allTrades: state.allTrades.filter(trade => trade.id !== tradeId),
          sentTrades: state.sentTrades.filter(trade => trade.id !== tradeId),
          receivedTrades: state.receivedTrades.filter(trade => trade.id !== tradeId)
        })),

        setAvailablePlayers: (players) => set({ availablePlayers: players }),

        setTeamRosters: (rosters) => set({ teamRosters: rosters }),

        updatePlayerValue: (playerId, newValue) => set((state) => ({
          availablePlayers: state.availablePlayers.map(player =>
            player.id === playerId ? { ...player, trade_value: newValue } : player
          ),
          teamRosters: Object.keys(state.teamRosters).reduce((acc, teamId) => {
            acc[teamId] = state.teamRosters[teamId].map(player =>
              player.id === playerId ? { ...player, trade_value: newValue } : player
            );
            return acc;
          }, {} as Record<string, TradePlayer[]>)
        })),

        proposeTrade: async () => {
          const state = get();
          if (!state.currentTrade || !get().isTradeValid()) return;

          set({ isSubmitting: true, error: null });

          try {
            // This would call the API client to propose the trade
            // const newTrade = await ultimateFantasyClient.trades.propose(state.currentTrade);

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            const newTrade: TradeProposal = {
              id: `trade-${Date.now()}`,
              league_id: 'current-league',
              ...state.currentTrade,
              status: 'pending',
              evaluation: state.currentEvaluation,
              expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            };

            get().addTrade(newTrade);
            get().clearCurrentTrade();

            set({ isSubmitting: false });

            storeEvents.emit(STORE_EVENTS.TRADE_PROPOSED, newTrade);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to propose trade',
              isSubmitting: false
            });
          }
        },

        acceptTrade: async (tradeId) => {
          set({ isSubmitting: true, error: null });

          try {
            // await ultimateFantasyClient.trades.respond(tradeId, 'accept');
            await new Promise(resolve => setTimeout(resolve, 1000));

            get().updateTrade(tradeId, {
              status: 'accepted',
              processed_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            });

            set({ isSubmitting: false });

            storeEvents.emit(STORE_EVENTS.TRADE_ACCEPTED, tradeId);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to accept trade',
              isSubmitting: false
            });
          }
        },

        rejectTrade: async (tradeId, reason) => {
          set({ isSubmitting: true, error: null });

          try {
            // await ultimateFantasyClient.trades.respond(tradeId, 'reject');
            await new Promise(resolve => setTimeout(resolve, 1000));

            get().updateTrade(tradeId, {
              status: 'rejected',
              processed_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            });

            set({ isSubmitting: false });

            storeEvents.emit(STORE_EVENTS.TRADE_REJECTED, tradeId);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to reject trade',
              isSubmitting: false
            });
          }
        },

        cancelTrade: async (tradeId) => {
          set({ isSubmitting: true, error: null });

          try {
            // await ultimateFantasyClient.trades.cancel(tradeId);
            await new Promise(resolve => setTimeout(resolve, 1000));

            get().updateTrade(tradeId, {
              status: 'cancelled',
              updated_at: new Date().toISOString()
            });

            set({ isSubmitting: false });

            storeEvents.emit(STORE_EVENTS.TRADE_CANCELLED, tradeId);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to cancel trade',
              isSubmitting: false
            });
          }
        },

        evaluateTrade: async () => {
          const state = get();
          if (!state.currentTrade || !get().isTradeValid()) return;

          set({ isEvaluating: true, error: null });

          try {
            // This would call the API client to evaluate the trade
            // const evaluation = await ultimateFantasyClient.trades.evaluate(state.currentTrade);

            // Simulate API call with mock evaluation
            await new Promise(resolve => setTimeout(resolve, 2000));

            const proposedValue = state.currentTrade.proposed_players.reduce(
              (sum, player) => sum + player.trade_value, 0
            );
            const requestedValue = state.currentTrade.requested_players.reduce(
              (sum, player) => sum + player.trade_value, 0
            );

            const valueDifference = Math.abs(proposedValue - requestedValue);
            const fairnessThreshold = Math.max(proposedValue, requestedValue) * 0.1;

            let fairness: TradeEvaluation['fairness'] = 'fair';
            if (valueDifference > fairnessThreshold) {
              if (proposedValue > requestedValue) {
                fairness = valueDifference > fairnessThreshold * 2 ? 'heavily_favors_team_b' : 'favors_team_b';
              } else {
                fairness = valueDifference > fairnessThreshold * 2 ? 'heavily_favors_team_a' : 'favors_team_a';
              }
            }

            const evaluation: TradeEvaluation = {
              overall_score: Math.max(0, 100 - (valueDifference / Math.max(proposedValue, requestedValue)) * 100),
              fairness,
              team_a_value: proposedValue,
              team_b_value: requestedValue,
              value_difference: valueDifference,
              analysis: {
                summary: fairness === 'fair' ? 'This trade appears to be fair for both teams.' : 'This trade may favor one team over the other.',
                team_a_gains: ['Acquiring players with different skill sets'],
                team_a_losses: ['Giving up current roster depth'],
                team_b_gains: ['Receiving proven talent'],
                team_b_losses: ['Losing current production'],
                recommendations: fairness === 'fair' ? ['Consider the trade'] : ['Evaluate if additional compensation is needed']
              },
              position_impact: {},
              risk_factors: state.currentTrade.proposed_players.some(p => p.injury_status !== 'healthy') ? ['Injury concerns'] : [],
              confidence: 0.85
            };

            set({ currentEvaluation: evaluation, isEvaluating: false });

            storeEvents.emit(STORE_EVENTS.TRADE_EVALUATED, evaluation);
          } catch (error) {
            set({
              error: error instanceof Error ? error.message : 'Failed to evaluate trade',
              isEvaluating: false
            });
          }
        },

        setFilters: (filters) => set((state) => ({
          filters: { ...state.filters, ...filters }
        })),

        setSelectedTrade: (trade) => set({ selectedTrade: trade }),

        setNotifications: (notifications) => set({ notifications }),

        addNotification: (notification) => {
          const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
          set((state) => ({
            notifications: [...state.notifications, {
              ...notification,
              id,
              timestamp: new Date().toISOString(),
              read: false
            }]
          }));
        },

        markNotificationRead: (notificationId) => set((state) => ({
          notifications: state.notifications.map(notif =>
            notif.id === notificationId ? { ...notif, read: true } : notif
          )
        })),

        clearNotifications: () => set({ notifications: [] }),

        setLoading: (loading) => set({ isLoading: loading }),

        setEvaluating: (evaluating) => set({ isEvaluating: evaluating }),

        setSubmitting: (submitting) => set({ isSubmitting: submitting }),

        setError: (error) => set({ error }),

        setCurrentEvaluation: (evaluation) => set({ currentEvaluation: evaluation }),

        clearState: () => set({
          currentTrade: null,
          allTrades: [],
          sentTrades: [],
          receivedTrades: [],
          availablePlayers: [],
          teamRosters: {},
          filters: defaultFilters,
          selectedTrade: null,
          notifications: [],
          isLoading: false,
          isEvaluating: false,
          isSubmitting: false,
          error: null,
          currentEvaluation: null
        }),

        // Selectors
        getTradesByStatus: (status) => {
          const state = get();
          if (status === 'all') return state.allTrades;
          return state.allTrades.filter(trade => trade.status === status);
        },

        getFilteredTrades: () => {
          const state = get();
          let trades = state.allTrades;

          if (state.filters.status !== 'all') {
            trades = trades.filter(trade => trade.status === state.filters.status);
          }

          if (state.filters.team !== 'all') {
            trades = trades.filter(trade =>
              trade.proposing_team_id === state.filters.team ||
              trade.receiving_team_id === state.filters.team
            );
          }

          if (state.filters.position !== 'all') {
            trades = trades.filter(trade =>
              trade.proposed_players.some(p => p.position === state.filters.position) ||
              trade.requested_players.some(p => p.position === state.filters.position)
            );
          }

          // Sort trades
          trades.sort((a, b) => {
            const order = state.filters.sort_order === 'asc' ? 1 : -1;

            switch (state.filters.sort_by) {
              case 'date':
                return (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()) * order;
              case 'value':
                const aValue = (a.evaluation?.team_a_value || 0) + (a.evaluation?.team_b_value || 0);
                const bValue = (b.evaluation?.team_a_value || 0) + (b.evaluation?.team_b_value || 0);
                return (aValue - bValue) * order;
              case 'fairness':
                const aScore = a.evaluation?.overall_score || 0;
                const bScore = b.evaluation?.overall_score || 0;
                return (aScore - bScore) * order;
              default:
                return 0;
            }
          });

          return trades;
        },

        getTeamPlayers: (teamId) => {
          const state = get();
          return state.teamRosters[teamId] || [];
        },

        getTradablePlayersForTeam: (teamId) => {
          const players = get().getTeamPlayers(teamId);
          return players.filter(player => player.injury_status !== 'ir'); // Can't trade IR players
        },

        getRecentTrades: (limit = 10) => {
          const state = get();
          return state.allTrades
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, limit);
        },

        getPendingTradesCount: () => {
          const state = get();
          return state.allTrades.filter(trade => trade.status === 'pending').length;
        },

        getUnreadNotificationsCount: () => {
          const state = get();
          return state.notifications.filter(notif => !notif.read).length;
        },

        isTradeValid: () => {
          const state = get();
          if (!state.currentTrade) return false;

          return (
            state.currentTrade.proposed_players.length > 0 &&
            state.currentTrade.requested_players.length > 0 &&
            state.currentTrade.proposing_team_id !== state.currentTrade.receiving_team_id
          );
        },

        getCurrentTradeValue: () => {
          const state = get();
          if (!state.currentTrade) return { proposed: 0, requested: 0 };

          const proposedValue = state.currentTrade.proposed_players.reduce(
            (sum, player) => sum + player.trade_value, 0
          );
          const requestedValue = state.currentTrade.requested_players.reduce(
            (sum, player) => sum + player.trade_value, 0
          );

          return { proposed: proposedValue, requested: requestedValue };
        }
      }),
      {
        name: 'trading-store',
        // Persist trade history and filters, but not transient state
        partialize: (state) => ({
          allTrades: state.allTrades,
          filters: state.filters,
          notifications: state.notifications.slice(-20) // Keep last 20 notifications
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
export const useTradingStore = createTradingStore();

// Add trade events to store events
export const TRADE_EVENTS = {
  ...STORE_EVENTS,
  TRADE_PROPOSED: 'trade:proposed',
  TRADE_ACCEPTED: 'trade:accepted',
  TRADE_REJECTED: 'trade:rejected',
  TRADE_CANCELLED: 'trade:cancelled',
  TRADE_EVALUATED: 'trade:evaluated'
} as const;

// Helper functions for trading operations
export const tradingStoreHelpers = {
  calculatePlayerValue: (player: TradePlayer) => {
    // Simple value calculation based on projected points and recent performance
    const recentAvg = player.recent_performance.length > 0
      ? player.recent_performance.reduce((a, b) => a + b, 0) / player.recent_performance.length
      : player.projected_points;

    return (player.projected_points * 0.7) + (recentAvg * 0.3);
  },

  getFairnessColor: (fairness: TradeEvaluation['fairness']) => {
    switch (fairness) {
      case 'fair': return '#059669'; // green
      case 'favors_team_a':
      case 'favors_team_b': return '#f59e0b'; // yellow
      case 'heavily_favors_team_a':
      case 'heavily_favors_team_b': return '#ef4444'; // red
      default: return '#64748b'; // gray
    }
  },

  getFairnessLabel: (fairness: TradeEvaluation['fairness']) => {
    return {
      'fair': 'Fair Trade',
      'favors_team_a': 'Slightly Favors Team A',
      'favors_team_b': 'Slightly Favors Team B',
      'heavily_favors_team_a': 'Heavily Favors Team A',
      'heavily_favors_team_b': 'Heavily Favors Team B'
    }[fairness] || 'Unknown';
  },

  isTradeExpired: (trade: TradeProposal) => {
    return new Date() > new Date(trade.expires_at);
  },

  canAcceptTrade: (trade: TradeProposal, currentUserId: string) => {
    return (
      trade.status === 'pending' &&
      !tradingStoreHelpers.isTradeExpired(trade) &&
      trade.receiving_team_id === currentUserId
    );
  },

  canCancelTrade: (trade: TradeProposal, currentUserId: string) => {
    return (
      trade.status === 'pending' &&
      trade.proposing_team_id === currentUserId
    );
  },

  getTradeStatusColor: (status: TradeProposal['status']) => {
    switch (status) {
      case 'pending': return '#f59e0b'; // yellow
      case 'accepted': return '#059669'; // green
      case 'rejected': return '#ef4444'; // red
      case 'expired': return '#94a3b8'; // gray
      case 'cancelled': return '#64748b'; // dark gray
      default: return '#64748b';
    }
  },

  formatTradeValue: (value: number) => {
    return `$${value.toFixed(1)}M`;
  },

  getPositionColor: (position: string) => {
    const colors = {
      'QB': '#3b82f6', // blue
      'RB': '#059669', // green
      'WR': '#dc2626', // red
      'TE': '#7c3aed', // purple
      'K': '#f59e0b', // yellow
      'DST': '#64748b' // gray
    };
    return colors[position as keyof typeof colors] || '#64748b';
  }
};