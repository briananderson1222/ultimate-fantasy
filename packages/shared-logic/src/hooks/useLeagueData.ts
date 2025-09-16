import { useState, useEffect, useCallback } from 'react';
import { useLeagueStore, League } from '../store/leagueStore';

export interface LeagueDataHookOptions {
  autoFetch?: boolean;
  refetchInterval?: number;
  onError?: (error: Error) => void;
  onSuccess?: (leagues: League[]) => void;
}

export interface LeagueDataHookReturn {
  leagues: League[];
  selectedLeague: League | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  selectLeague: (leagueId: string | null) => void;
  updateLeague: (leagueId: string, updates: Partial<League>) => void;
  addLeague: (league: League) => void;
  removeLeague: (leagueId: string) => void;
}

// Mock API function - in real implementation this would call actual API
const fetchLeaguesFromAPI = async (): Promise<League[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Return mock data
  return [
    {
      league_id: '1',
      name: 'Championship League',
      settings: {
        draft_type: 'snake',
        scoring_type: 'standard',
        roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'D/ST', 'K'],
        total_rosters: 12
      },
      roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'D/ST', 'K'],
      status: 'active',
      season: '2025',
      season_type: 'regular',
      total_rosters: 12,
      avatar: '/avatars/league1.png'
    },
    {
      league_id: '2',
      name: 'Friends & Family',
      settings: {
        draft_type: 'auction',
        scoring_type: 'ppr',
        roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'D/ST', 'K'],
        total_rosters: 10
      },
      roster_positions: ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'D/ST', 'K'],
      status: 'drafting',
      season: '2025',
      season_type: 'regular',
      total_rosters: 10,
      draft_id: 'draft_123'
    }
  ];
};

export const useLeagueData = (options: LeagueDataHookOptions = {}): LeagueDataHookReturn => {
  const {
    autoFetch = true,
    refetchInterval,
    onError,
    onSuccess
  } = options;

  const {
    leagues,
    selectedLeague,
    isLoading,
    error,
    setLeagues,
    setSelectedLeague,
    addLeague: addLeagueToStore,
    updateLeague: updateLeagueInStore,
    removeLeague: removeLeagueFromStore,
    setLoading,
    setError
  } = useLeagueStore();

  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  const fetchLeagues = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const fetchedLeagues = await fetchLeaguesFromAPI();
      setLeagues(fetchedLeagues);
      setLastFetch(new Date());

      onSuccess?.(fetchedLeagues);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch leagues');
      setError(error.message);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [setLeagues, setLoading, setError, onSuccess, onError]);

  const selectLeague = useCallback((leagueId: string | null) => {
    if (leagueId === null) {
      setSelectedLeague(null);
      return;
    }

    const league = leagues.find(l => l.league_id === leagueId);
    if (league) {
      setSelectedLeague(league);
    }
  }, [leagues, setSelectedLeague]);

  const updateLeague = useCallback((leagueId: string, updates: Partial<League>) => {
    updateLeagueInStore(leagueId, updates);
  }, [updateLeagueInStore]);

  const addLeague = useCallback((league: League) => {
    addLeagueToStore(league);
  }, [addLeagueToStore]);

  const removeLeague = useCallback((leagueId: string) => {
    removeLeagueFromStore(leagueId);
  }, [removeLeagueFromStore]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch && leagues.length === 0 && !isLoading) {
      fetchLeagues();
    }
  }, [autoFetch, leagues.length, isLoading, fetchLeagues]);

  // Set up refetch interval
  useEffect(() => {
    if (!refetchInterval) return;

    const interval = setInterval(() => {
      if (!isLoading) {
        fetchLeagues();
      }
    }, refetchInterval);

    return () => clearInterval(interval);
  }, [refetchInterval, isLoading, fetchLeagues]);

  return {
    leagues,
    selectedLeague,
    isLoading,
    error,
    refetch: fetchLeagues,
    selectLeague,
    updateLeague,
    addLeague,
    removeLeague
  };
};

// Helper hook for a specific league
export const useLeague = (leagueId: string | null) => {
  const { leagues, selectedLeague, selectLeague, updateLeague } = useLeagueData({ autoFetch: false });

  const league = leagueId ? leagues.find(l => l.league_id === leagueId) || null : null;

  useEffect(() => {
    if (leagueId && league && (!selectedLeague || selectedLeague.league_id !== leagueId)) {
      selectLeague(leagueId);
    }
  }, [leagueId, league, selectedLeague, selectLeague]);

  return {
    league,
    isSelected: selectedLeague?.league_id === leagueId,
    updateLeague: leagueId ? (updates: Partial<League>) => updateLeague(leagueId, updates) : undefined
  };
};

// Helper hook for league filtering and sorting
export const useLeagueFilters = () => {
  const { leagues } = useLeagueData({ autoFetch: false });

  const getLeaguesByStatus = useCallback((status: string) => {
    return leagues.filter(league => league.status === status);
  }, [leagues]);

  const getActiveLeagues = useCallback(() => {
    return getLeaguesByStatus('active');
  }, [getLeaguesByStatus]);

  const getDraftingLeagues = useCallback(() => {
    return getLeaguesByStatus('drafting');
  }, [getLeaguesByStatus]);

  const searchLeagues = useCallback((query: string) => {
    if (!query.trim()) return leagues;

    const lowerQuery = query.toLowerCase();
    return leagues.filter(league =>
      league.name.toLowerCase().includes(lowerQuery) ||
      league.league_id.includes(lowerQuery)
    );
  }, [leagues]);

  const sortLeagues = useCallback((
    sortBy: 'name' | 'status' | 'total_rosters' | 'season',
    direction: 'asc' | 'desc' = 'asc'
  ) => {
    return [...leagues].sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        case 'total_rosters':
          comparison = a.total_rosters - b.total_rosters;
          break;
        case 'season':
          comparison = a.season.localeCompare(b.season);
          break;
        default:
          return 0;
      }

      return direction === 'asc' ? comparison : -comparison;
    });
  }, [leagues]);

  return {
    leagues,
    getLeaguesByStatus,
    getActiveLeagues,
    getDraftingLeagues,
    searchLeagues,
    sortLeagues
  };
};