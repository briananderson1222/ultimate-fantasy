// Utility functions for Ultimate Fantasy platform

export interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  injury_status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'ir';
  bye_week?: number;
  trade_value?: number;
  recent_performance?: number[];
}

export interface TeamStats {
  wins: number;
  losses: number;
  ties: number;
  points_for: number;
  points_against: number;
  win_percentage: number;
  average_points: number;
}

// Player utilities
export const sortPlayersByPosition = (players: Player[]): Record<string, Player[]> => {
  return players.reduce((acc, player) => {
    if (!acc[player.position]) {
      acc[player.position] = [];
    }
    acc[player.position].push(player);
    return acc;
  }, {} as Record<string, Player[]>);
};

export const getPlayersByPosition = (players: Player[], position: string): Player[] => {
  return players.filter(player => player.position === position);
};

export const sortPlayersByProjection = (players: Player[], descending = true): Player[] => {
  return [...players].sort((a, b) => {
    const diff = a.projected_points - b.projected_points;
    return descending ? -diff : diff;
  });
};

export const sortPlayersByValue = (players: Player[], descending = true): Player[] => {
  return [...players].sort((a, b) => {
    const aValue = a.trade_value || 0;
    const bValue = b.trade_value || 0;
    const diff = aValue - bValue;
    return descending ? -diff : diff;
  });
};

export const getHealthyPlayers = (players: Player[]): Player[] => {
  return players.filter(player => player.injury_status === 'healthy');
};

export const getInjuredPlayers = (players: Player[]): Player[] => {
  return players.filter(player =>
    ['questionable', 'doubtful', 'out', 'ir'].includes(player.injury_status)
  );
};

export const getPlayersOnBye = (players: Player[], week: number): Player[] => {
  return players.filter(player => player.bye_week === week);
};

export const getAvailablePlayers = (players: Player[], week: number): Player[] => {
  return players.filter(player =>
    player.injury_status === 'healthy' && player.bye_week !== week
  );
};

export const calculatePlayerTrend = (player: Player): 'up' | 'down' | 'steady' => {
  if (!player.recent_performance || player.recent_performance.length < 2) {
    return 'steady';
  }

  const recent = player.recent_performance.slice(-3);
  const average = recent.reduce((sum, points) => sum + points, 0) / recent.length;

  if (average > player.projected_points * 1.1) return 'up';
  if (average < player.projected_points * 0.9) return 'down';
  return 'steady';
};

// Scoring utilities
export const calculateStandardPoints = (stats: Record<string, number>): number => {
  const scoring = {
    passing_yards: 0.04,    // 1 point per 25 yards
    passing_tds: 4,         // 4 points per TD
    passing_ints: -2,       // -2 points per INT
    rushing_yards: 0.1,     // 1 point per 10 yards
    rushing_tds: 6,         // 6 points per TD
    receiving_yards: 0.1,   // 1 point per 10 yards
    receiving_tds: 6,       // 6 points per TD
    receptions: 0,          // 0 points in standard
    fumbles_lost: -2,       // -2 points per fumble
    two_point_conversions: 2 // 2 points per 2PC
  };

  return Object.entries(stats).reduce((total, [stat, value]) => {
    return total + (scoring[stat as keyof typeof scoring] || 0) * value;
  }, 0);
};

export const calculatePPRPoints = (stats: Record<string, number>): number => {
  const standardPoints = calculateStandardPoints(stats);
  const receptionPoints = (stats.receptions || 0) * 1; // 1 point per reception
  return standardPoints + receptionPoints;
};

export const calculateHalfPPRPoints = (stats: Record<string, number>): number => {
  const standardPoints = calculateStandardPoints(stats);
  const receptionPoints = (stats.receptions || 0) * 0.5; // 0.5 points per reception
  return standardPoints + receptionPoints;
};

// Team utilities
export const calculateTeamStats = (
  wins: number,
  losses: number,
  ties: number,
  pointsFor: number,
  pointsAgainst: number
): TeamStats => {
  const totalGames = wins + losses + ties;
  const winPercentage = totalGames > 0 ? (wins + ties * 0.5) / totalGames : 0;
  const averagePoints = totalGames > 0 ? pointsFor / totalGames : 0;

  return {
    wins,
    losses,
    ties,
    points_for: pointsFor,
    points_against: pointsAgainst,
    win_percentage: winPercentage,
    average_points: averagePoints
  };
};

export const calculatePlayoffChances = (
  currentRecord: TeamStats,
  gamesRemaining: number,
  totalTeams: number,
  playoffSpots: number
): number => {
  // Simplified playoff probability calculation
  const currentWinPct = currentRecord.win_percentage;
  const projectedWins = currentRecord.wins + (gamesRemaining * currentWinPct);
  const totalGames = currentRecord.wins + currentRecord.losses + currentRecord.ties + gamesRemaining;
  const projectedWinPct = projectedWins / totalGames;

  // Basic heuristic: need to be in top half for playoffs
  const cutoffPct = playoffSpots / totalTeams;

  if (projectedWinPct >= 0.7) return 0.9;
  if (projectedWinPct >= 0.6) return 0.7;
  if (projectedWinPct >= 0.5) return Math.max(0.1, cutoffPct);
  return Math.max(0.01, cutoffPct * 0.5);
};

// Draft utilities
export const calculateDraftValue = (
  player: Player,
  position: string,
  positionScarcity: number
): number => {
  const baseValue = player.projected_points;
  const scarcityMultiplier = 1 + (positionScarcity / 100);
  const injuryDiscount = player.injury_status === 'healthy' ? 1 : 0.8;

  return baseValue * scarcityMultiplier * injuryDiscount;
};

export const getOptimalDraftOrder = (
  availablePlayers: Player[],
  teamNeeds: Record<string, number>
): Player[] => {
  return availablePlayers
    .map(player => ({
      ...player,
      value: calculateDraftValue(player, player.position, teamNeeds[player.position] || 0)
    }))
    .sort((a, b) => b.value - a.value);
};

export const getDraftRecommendations = (
  availablePlayers: Player[],
  currentRoster: Player[],
  totalRosterSpots: number
): Player[] => {
  const positionCounts = currentRoster.reduce((counts, player) => {
    counts[player.position] = (counts[player.position] || 0) + 1;
    return counts;
  }, {} as Record<string, number>);

  const positionNeeds = {
    QB: Math.max(0, 2 - (positionCounts.QB || 0)),
    RB: Math.max(0, 4 - (positionCounts.RB || 0)),
    WR: Math.max(0, 4 - (positionCounts.WR || 0)),
    TE: Math.max(0, 2 - (positionCounts.TE || 0)),
    K: Math.max(0, 1 - (positionCounts.K || 0)),
    DST: Math.max(0, 1 - (positionCounts.DST || 0))
  };

  return getOptimalDraftOrder(availablePlayers, positionNeeds).slice(0, 10);
};

// Lineup utilities
export const getLineupScore = (lineup: any[]): number => {
  return lineup
    .filter(slot => slot.position !== 'BENCH' && slot.player)
    .reduce((total, slot) => total + (slot.player.projected_points || 0), 0);
};

export const optimizeLineup = (
  availablePlayers: Player[],
  lineupSlots: any[]
): any[] => {
  const optimizedLineup = [...lineupSlots];

  // Sort players by projected points
  const sortedPlayers = sortPlayersByProjection(availablePlayers);

  // Fill each position with the best available player
  optimizedLineup.forEach((slot, index) => {
    if (slot.position === 'BENCH') return;

    const eligiblePlayers = sortedPlayers.filter(player => {
      // Check if player can fit in this slot
      if (slot.position === 'FLEX') {
        return ['RB', 'WR', 'TE'].includes(player.position);
      }
      return player.position === slot.position;
    });

    if (eligiblePlayers.length > 0) {
      optimizedLineup[index] = { ...slot, player: eligiblePlayers[0] };
    }
  });

  return optimizedLineup;
};

// Trade utilities
export const calculateTradeValue = (players: Player[]): number => {
  return players.reduce((total, player) => total + (player.trade_value || 0), 0);
};

export const evaluateTradeBalance = (
  teamAPlayers: Player[],
  teamBPlayers: Player[]
): {
  teamAValue: number;
  teamBValue: number;
  difference: number;
  fairness: 'fair' | 'favors_a' | 'favors_b' | 'heavily_favors_a' | 'heavily_favors_b';
} => {
  const teamAValue = calculateTradeValue(teamAPlayers);
  const teamBValue = calculateTradeValue(teamBPlayers);
  const difference = Math.abs(teamAValue - teamBValue);
  const maxValue = Math.max(teamAValue, teamBValue);

  let fairness: 'fair' | 'favors_a' | 'favors_b' | 'heavily_favors_a' | 'heavily_favors_b';

  if (difference / maxValue < 0.1) {
    fairness = 'fair';
  } else if (difference / maxValue < 0.25) {
    fairness = teamAValue > teamBValue ? 'favors_a' : 'favors_b';
  } else {
    fairness = teamAValue > teamBValue ? 'heavily_favors_a' : 'heavily_favors_b';
  }

  return {
    teamAValue,
    teamBValue,
    difference,
    fairness
  };
};

// Waiver utilities
export const calculateWaiverPriority = (
  currentRecord: TeamStats,
  totalTeams: number,
  reverseOrder = true
): number => {
  const standings = Math.floor(currentRecord.win_percentage * totalTeams);
  return reverseOrder ? totalTeams - standings : standings;
};

export const calculateFAABRecommendation = (
  player: Player,
  remainingBudget: number,
  weekNumber: number,
  totalWeeks: number
): number => {
  const seasonProgress = weekNumber / totalWeeks;
  const playerValue = player.projected_points;
  const urgencyMultiplier = seasonProgress > 0.7 ? 1.5 : 1.0; // Spend more late in season

  const recommendedBid = Math.min(
    remainingBudget * 0.15, // Don't spend more than 15% of budget on one player
    playerValue * 2 * urgencyMultiplier
  );

  return Math.max(1, Math.floor(recommendedBid));
};

// Utility functions
export const formatPoints = (points: number): string => {
  return points.toFixed(1);
};

export const formatRecord = (wins: number, losses: number, ties = 0): string => {
  return ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`;
};

export const getPositionColor = (position: string): string => {
  const colors = {
    QB: '#3b82f6',   // blue
    RB: '#059669',   // green
    WR: '#dc2626',   // red
    TE: '#7c3aed',   // purple
    K: '#f59e0b',    // yellow
    DST: '#64748b'   // gray
  };
  return colors[position as keyof typeof colors] || '#64748b';
};

export const getInjuryStatusColor = (status: string): string => {
  const colors = {
    healthy: '#059669',      // green
    questionable: '#f59e0b', // yellow
    doubtful: '#f97316',     // orange
    out: '#ef4444',          // red
    ir: '#7f1d1d'           // dark red
  };
  return colors[status as keyof typeof colors] || '#64748b';
};

export const getInjuryStatusLabel = (status: string): string => {
  const labels = {
    healthy: 'Healthy',
    questionable: 'Questionable',
    doubtful: 'Doubtful',
    out: 'Out',
    ir: 'Injured Reserve'
  };
  return labels[status as keyof typeof labels] || 'Unknown';
};

export const calculateSeasonLong = (weeklyScores: number[]): {
  total: number;
  average: number;
  best: number;
  worst: number;
  consistency: number;
} => {
  if (weeklyScores.length === 0) {
    return { total: 0, average: 0, best: 0, worst: 0, consistency: 0 };
  }

  const total = weeklyScores.reduce((sum, score) => sum + score, 0);
  const average = total / weeklyScores.length;
  const best = Math.max(...weeklyScores);
  const worst = Math.min(...weeklyScores);

  // Calculate consistency (lower standard deviation = more consistent)
  const variance = weeklyScores.reduce((sum, score) => sum + Math.pow(score - average, 2), 0) / weeklyScores.length;
  const standardDeviation = Math.sqrt(variance);
  const consistency = Math.max(0, 100 - (standardDeviation / average) * 100);

  return {
    total: Math.round(total * 10) / 10,
    average: Math.round(average * 10) / 10,
    best: Math.round(best * 10) / 10,
    worst: Math.round(worst * 10) / 10,
    consistency: Math.round(consistency)
  };
};