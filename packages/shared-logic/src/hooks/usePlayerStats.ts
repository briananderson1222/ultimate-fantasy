import { useState, useEffect, useCallback, useMemo } from 'react';

export interface PlayerStats {
  player_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  team: string;
  position: string;
  stats: {
    [key: string]: number;
  };
  fantasy_points: number;
  fantasy_points_ppr: number;
  week: number;
  season: string;
  season_type: 'regular' | 'playoff';
}

export interface PlayerInfo {
  player_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  team: string;
  position: string;
  height: string;
  weight: string;
  college: string;
  years_exp: number;
  age: number;
  injury_status?: string;
  injury_notes?: string;
}

export interface PlayerStatsHookOptions {
  week?: number;
  season?: string;
  season_type?: 'regular' | 'playoff';
  position?: string;
  team?: string;
  autoFetch?: boolean;
  refetchInterval?: number;
  onError?: (error: Error) => void;
  onSuccess?: (stats: PlayerStats[]) => void;
}

export interface PlayerStatsHookReturn {
  stats: PlayerStats[];
  playerInfo: Record<string, PlayerInfo>;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  getPlayerStats: (playerId: string) => PlayerStats | null;
  getPlayerInfo: (playerId: string) => PlayerInfo | null;
  filterByPosition: (position: string) => PlayerStats[];
  filterByTeam: (team: string) => PlayerStats[];
  sortByFantasyPoints: (ppr?: boolean) => PlayerStats[];
  getTopPerformers: (limit?: number, ppr?: boolean) => PlayerStats[];
}

// Mock API functions - in real implementation these would call actual APIs
const fetchPlayerStatsFromAPI = async (options: PlayerStatsHookOptions = {}): Promise<PlayerStats[]> => {
  await new Promise(resolve => setTimeout(resolve, 800));

  // Mock player stats data
  const mockStats: PlayerStats[] = [
    {
      player_id: '1',
      full_name: 'Josh Allen',
      first_name: 'Josh',
      last_name: 'Allen',
      team: 'BUF',
      position: 'QB',
      stats: {
        passing_yards: 285,
        passing_tds: 2,
        interceptions: 1,
        rushing_yards: 45,
        rushing_tds: 1,
        completions: 18,
        attempts: 25
      },
      fantasy_points: 24.5,
      fantasy_points_ppr: 24.5,
      week: options.week || 1,
      season: options.season || '2025',
      season_type: options.season_type || 'regular'
    },
    {
      player_id: '2',
      full_name: 'Christian McCaffrey',
      first_name: 'Christian',
      last_name: 'McCaffrey',
      team: 'SF',
      position: 'RB',
      stats: {
        rushing_yards: 120,
        rushing_tds: 1,
        receptions: 6,
        receiving_yards: 45,
        receiving_tds: 0,
        carries: 18
      },
      fantasy_points: 21.5,
      fantasy_points_ppr: 24.5,
      week: options.week || 1,
      season: options.season || '2025',
      season_type: options.season_type || 'regular'
    },
    {
      player_id: '3',
      full_name: 'Tyreek Hill',
      first_name: 'Tyreek',
      last_name: 'Hill',
      team: 'MIA',
      position: 'WR',
      stats: {
        receptions: 8,
        receiving_yards: 110,
        receiving_tds: 1,
        targets: 12,
        air_yards: 135
      },
      fantasy_points: 23.0,
      fantasy_points_ppr: 27.0,
      week: options.week || 1,
      season: options.season || '2025',
      season_type: options.season_type || 'regular'
    },
    {
      player_id: '4',
      full_name: 'Travis Kelce',
      first_name: 'Travis',
      last_name: 'Kelce',
      team: 'KC',
      position: 'TE',
      stats: {
        receptions: 5,
        receiving_yards: 65,
        receiving_tds: 1,
        targets: 7,
        air_yards: 72
      },
      fantasy_points: 18.5,
      fantasy_points_ppr: 23.5,
      week: options.week || 1,
      season: options.season || '2025',
      season_type: options.season_type || 'regular'
    }
  ];

  // Apply filters
  let filteredStats = mockStats;

  if (options.position) {
    filteredStats = filteredStats.filter(stat => stat.position === options.position);
  }

  if (options.team) {
    filteredStats = filteredStats.filter(stat => stat.team === options.team);
  }

  return filteredStats;
};

const fetchPlayerInfoFromAPI = async (playerIds: string[]): Promise<Record<string, PlayerInfo>> => {
  await new Promise(resolve => setTimeout(resolve, 500));

  // Mock player info data
  const mockPlayerInfo: Record<string, PlayerInfo> = {
    '1': {
      player_id: '1',
      full_name: 'Josh Allen',
      first_name: 'Josh',
      last_name: 'Allen',
      team: 'BUF',
      position: 'QB',
      height: '6\'5"',
      weight: '237',
      college: 'Wyoming',
      years_exp: 7,
      age: 28
    },
    '2': {
      player_id: '2',
      full_name: 'Christian McCaffrey',
      first_name: 'Christian',
      last_name: 'McCaffrey',
      team: 'SF',
      position: 'RB',
      height: '5\'11"',
      weight: '205',
      college: 'Stanford',
      years_exp: 8,
      age: 28
    },
    '3': {
      player_id: '3',
      full_name: 'Tyreek Hill',
      first_name: 'Tyreek',
      last_name: 'Hill',
      team: 'MIA',
      position: 'WR',
      height: '5\'10"',
      weight: '185',
      college: 'West Alabama',
      years_exp: 9,
      age: 30
    },
    '4': {
      player_id: '4',
      full_name: 'Travis Kelce',
      first_name: 'Travis',
      last_name: 'Kelce',
      team: 'KC',
      position: 'TE',
      height: '6\'5"',
      weight: '250',
      college: 'Cincinnati',
      years_exp: 12,
      age: 35
    }
  };

  // Return only requested player info
  const result: Record<string, PlayerInfo> = {};
  playerIds.forEach(id => {
    if (mockPlayerInfo[id]) {
      result[id] = mockPlayerInfo[id];
    }
  });

  return result;
};

export const usePlayerStats = (options: PlayerStatsHookOptions = {}): PlayerStatsHookReturn => {
  const {
    autoFetch = true,
    refetchInterval,
    onError,
    onSuccess
  } = options;

  const [stats, setStats] = useState<PlayerStats[]>([]);
  const [playerInfo, setPlayerInfo] = useState<Record<string, PlayerInfo>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const fetchedStats = await fetchPlayerStatsFromAPI(options);
      setStats(fetchedStats);

      // Fetch player info for all players in stats
      const playerIds = fetchedStats.map(stat => stat.player_id);
      if (playerIds.length > 0) {
        const fetchedPlayerInfo = await fetchPlayerInfoFromAPI(playerIds);
        setPlayerInfo(prev => ({ ...prev, ...fetchedPlayerInfo }));
      }

      onSuccess?.(fetchedStats);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch player stats');
      setError(error.message);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [options, onSuccess, onError]);

  const getPlayerStats = useCallback((playerId: string): PlayerStats | null => {
    return stats.find(stat => stat.player_id === playerId) || null;
  }, [stats]);

  const getPlayerInfo = useCallback((playerId: string): PlayerInfo | null => {
    return playerInfo[playerId] || null;
  }, [playerInfo]);

  const filterByPosition = useCallback((position: string): PlayerStats[] => {
    return stats.filter(stat => stat.position === position);
  }, [stats]);

  const filterByTeam = useCallback((team: string): PlayerStats[] => {
    return stats.filter(stat => stat.team === team);
  }, [stats]);

  const sortByFantasyPoints = useCallback((ppr = false): PlayerStats[] => {
    return [...stats].sort((a, b) => {
      const pointsA = ppr ? a.fantasy_points_ppr : a.fantasy_points;
      const pointsB = ppr ? b.fantasy_points_ppr : b.fantasy_points;
      return pointsB - pointsA;
    });
  }, [stats]);

  const getTopPerformers = useCallback((limit = 10, ppr = false): PlayerStats[] => {
    return sortByFantasyPoints(ppr).slice(0, limit);
  }, [sortByFantasyPoints]);

  // Memoized calculations
  const positionGroups = useMemo(() => {
    const groups: Record<string, PlayerStats[]> = {};
    stats.forEach(stat => {
      if (!groups[stat.position]) {
        groups[stat.position] = [];
      }
      groups[stat.position].push(stat);
    });
    return groups;
  }, [stats]);

  const teamGroups = useMemo(() => {
    const groups: Record<string, PlayerStats[]> = {};
    stats.forEach(stat => {
      if (!groups[stat.team]) {
        groups[stat.team] = [];
      }
      groups[stat.team].push(stat);
    });
    return groups;
  }, [stats]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchStats();
    }
  }, [autoFetch, fetchStats]);

  // Set up refetch interval
  useEffect(() => {
    if (!refetchInterval) return;

    const interval = setInterval(() => {
      if (!isLoading) {
        fetchStats();
      }
    }, refetchInterval);

    return () => clearInterval(interval);
  }, [refetchInterval, isLoading, fetchStats]);

  return {
    stats,
    playerInfo,
    isLoading,
    error,
    refetch: fetchStats,
    getPlayerStats,
    getPlayerInfo,
    filterByPosition,
    filterByTeam,
    sortByFantasyPoints,
    getTopPerformers
  };
};

// Helper hook for a specific player
export const usePlayer = (playerId: string) => {
  const { getPlayerStats, getPlayerInfo, isLoading, error } = usePlayerStats({ autoFetch: false });

  const playerStats = getPlayerStats(playerId);
  const playerInfo = getPlayerInfo(playerId);

  return {
    stats: playerStats,
    info: playerInfo,
    isLoading,
    error,
    hasData: !!playerStats || !!playerInfo
  };
};

// Helper hook for position-based data
export const usePositionStats = (position: string) => {
  const { filterByPosition, sortByFantasyPoints, isLoading, error } = usePlayerStats({
    position,
    autoFetch: true
  });

  const positionStats = filterByPosition(position);
  const topPerformers = sortByFantasyPoints(true).slice(0, 5);

  return {
    stats: positionStats,
    topPerformers,
    isLoading,
    error,
    count: positionStats.length
  };
};