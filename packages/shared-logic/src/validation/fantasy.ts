// Enhanced validation schemas for Ultimate Fantasy platform

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface PlayerValidation {
  id: string;
  name: string;
  position: string;
  team: string;
  isValid: boolean;
  errors: string[];
}

export interface LineupValidation {
  lineup: any;
  isValid: boolean;
  errors: string[];
  warnings: string[];
  missingPositions: string[];
  invalidPlayers: PlayerValidation[];
}

export interface TradeValidation {
  trade: any;
  isValid: boolean;
  errors: string[];
  warnings: string[];
  fairnessScore: number;
  riskFactors: string[];
}

// Player validation functions
export const validatePlayer = (player: any): PlayerValidation => {
  const errors: string[] = [];

  if (!player.id) {
    errors.push('Player ID is required');
  }

  if (!player.name || player.name.trim().length === 0) {
    errors.push('Player name is required');
  }

  if (!player.position) {
    errors.push('Player position is required');
  } else if (!['QB', 'RB', 'WR', 'TE', 'K', 'DST'].includes(player.position)) {
    errors.push('Invalid player position');
  }

  if (!player.team) {
    errors.push('Player team is required');
  }

  if (player.projected_points && (typeof player.projected_points !== 'number' || player.projected_points < 0)) {
    errors.push('Projected points must be a positive number');
  }

  return {
    id: player.id || '',
    name: player.name || '',
    position: player.position || '',
    team: player.team || '',
    isValid: errors.length === 0,
    errors
  };
};

// Lineup validation functions
export const validateLineup = (lineup: any): LineupValidation => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const missingPositions: string[] = [];
  const invalidPlayers: PlayerValidation[] = [];

  if (!lineup) {
    return {
      lineup,
      isValid: false,
      errors: ['Lineup is required'],
      warnings: [],
      missingPositions: [],
      invalidPlayers: []
    };
  }

  if (!lineup.slots || !Array.isArray(lineup.slots)) {
    errors.push('Lineup slots are required');
    return {
      lineup,
      isValid: false,
      errors,
      warnings: [],
      missingPositions: [],
      invalidPlayers: []
    };
  }

  // Standard lineup requirements
  const requiredPositions = {
    QB: 1,
    RB: 2,
    WR: 2,
    TE: 1,
    FLEX: 1,
    K: 1,
    DST: 1
  };

  const positionCounts: Record<string, number> = {};

  lineup.slots.forEach((slot: any, index: number) => {
    if (slot.is_required && !slot.player) {
      missingPositions.push(slot.position);
      errors.push(`Missing required ${slot.position} player at slot ${index + 1}`);
    }

    if (slot.player) {
      const playerValidation = validatePlayer(slot.player);
      if (!playerValidation.isValid) {
        invalidPlayers.push(playerValidation);
        errors.push(`Invalid player at slot ${index + 1}: ${playerValidation.errors.join(', ')}`);
      }

      // Count positions for starting lineup only
      if (slot.position !== 'BENCH') {
        positionCounts[slot.position] = (positionCounts[slot.position] || 0) + 1;
      }

      // Check if player can fit in slot
      if (!canPlayerFitInSlot(slot.player, slot)) {
        errors.push(`${slot.player.name} cannot play ${slot.position}`);
      }

      // Check for injury warnings
      if (slot.player.injury_status === 'out' || slot.player.injury_status === 'ir') {
        errors.push(`${slot.player.name} is ${slot.player.injury_status} and cannot play`);
      } else if (slot.player.injury_status === 'questionable' || slot.player.injury_status === 'doubtful') {
        warnings.push(`${slot.player.name} is ${slot.player.injury_status}`);
      }

      // Check for bye week
      if (slot.player.bye_week === lineup.week) {
        warnings.push(`${slot.player.name} is on bye week`);
      }
    }
  });

  // Check position requirements
  Object.entries(requiredPositions).forEach(([position, required]) => {
    const count = positionCounts[position] || 0;
    if (count < required) {
      errors.push(`Need ${required - count} more ${position} player(s)`);
    }
  });

  return {
    lineup,
    isValid: errors.length === 0,
    errors,
    warnings,
    missingPositions,
    invalidPlayers
  };
};

// Trade validation functions
export const validateTrade = (trade: any): TradeValidation => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const riskFactors: string[] = [];

  if (!trade) {
    return {
      trade,
      isValid: false,
      errors: ['Trade data is required'],
      warnings: [],
      fairnessScore: 0,
      riskFactors: []
    };
  }

  if (!trade.proposing_team_id) {
    errors.push('Proposing team is required');
  }

  if (!trade.receiving_team_id) {
    errors.push('Receiving team is required');
  }

  if (trade.proposing_team_id === trade.receiving_team_id) {
    errors.push('Cannot trade with yourself');
  }

  if (!trade.proposed_players || trade.proposed_players.length === 0) {
    errors.push('Must include at least one player to trade away');
  }

  if (!trade.requested_players || trade.requested_players.length === 0) {
    errors.push('Must include at least one player to trade for');
  }

  // Validate all players in trade
  const allPlayers = [...(trade.proposed_players || []), ...(trade.requested_players || [])];
  allPlayers.forEach((player, index) => {
    const playerValidation = validatePlayer(player);
    if (!playerValidation.isValid) {
      errors.push(`Invalid player ${index + 1}: ${playerValidation.errors.join(', ')}`);
    }

    // Risk factors
    if (player.injury_status === 'questionable' || player.injury_status === 'doubtful') {
      riskFactors.push(`${player.name} has injury concerns`);
    }

    if (player.age && player.age > 30) {
      riskFactors.push(`${player.name} is over 30 years old`);
    }

    if (player.projected_points < 5) {
      warnings.push(`${player.name} has low projected points`);
    }
  });

  // Calculate basic fairness score
  const proposedValue = (trade.proposed_players || []).reduce((sum: number, p: any) => sum + (p.trade_value || 0), 0);
  const requestedValue = (trade.requested_players || []).reduce((sum: number, p: any) => sum + (p.trade_value || 0), 0);

  const totalValue = proposedValue + requestedValue;
  const valueDifference = Math.abs(proposedValue - requestedValue);
  const fairnessScore = totalValue > 0 ? Math.max(0, 100 - (valueDifference / totalValue) * 100) : 0;

  if (fairnessScore < 70) {
    warnings.push('Trade appears unbalanced based on player values');
  }

  // Check for expired trade
  if (trade.expires_at && new Date() > new Date(trade.expires_at)) {
    errors.push('Trade has expired');
  }

  return {
    trade,
    isValid: errors.length === 0,
    errors,
    warnings,
    fairnessScore,
    riskFactors
  };
};

// League validation functions
export const validateLeagueSettings = (settings: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!settings) {
    return {
      isValid: false,
      errors: ['League settings are required'],
      warnings: []
    };
  }

  if (!settings.max_teams || settings.max_teams < 2) {
    errors.push('League must have at least 2 teams');
  } else if (settings.max_teams > 20) {
    warnings.push('Large leagues may have reduced player availability');
  }

  if (!settings.scoring_type || !['standard', 'ppr', 'half_ppr'].includes(settings.scoring_type)) {
    errors.push('Invalid scoring type');
  }

  if (!settings.roster_size || settings.roster_size < 10) {
    errors.push('Roster size must be at least 10 players');
  } else if (settings.roster_size > 20) {
    warnings.push('Large rosters may make waiver wire thin');
  }

  if (settings.playoff_teams && settings.max_teams) {
    if (settings.playoff_teams > settings.max_teams / 2) {
      warnings.push('More than half the teams make playoffs');
    }
  }

  if (settings.waiver_type && !['rolling', 'faab'].includes(settings.waiver_type)) {
    errors.push('Invalid waiver type');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// Draft validation functions
export const validateDraftPick = (pick: any, draft: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!pick) {
    return {
      isValid: false,
      errors: ['Draft pick data is required'],
      warnings: []
    };
  }

  if (!pick.player_id) {
    errors.push('Must select a player');
  }

  if (!pick.team_id) {
    errors.push('Team ID is required');
  }

  if (!draft) {
    errors.push('Draft context is required');
  } else {
    // Check if it's the team's turn
    if (draft.current_team_id !== pick.team_id) {
      errors.push('Not your turn to pick');
    }

    // Check if player is already drafted
    if (draft.picks && draft.picks.some((p: any) => p.player_id === pick.player_id)) {
      errors.push('Player has already been drafted');
    }

    // Check if draft is in progress
    if (draft.status !== 'in_progress') {
      errors.push('Draft is not currently in progress');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// Utility functions
export const canPlayerFitInSlot = (player: any, slot: any): boolean => {
  if (!player || !slot) return false;

  // Bench accepts any player
  if (slot.position === 'BENCH') return true;

  // Flex positions accept RB, WR, TE
  if (slot.is_flex && ['RB', 'WR', 'TE'].includes(player.position)) return true;

  // Exact position match
  return slot.position === player.position;
};

export const calculateLineupScore = (lineup: any): number => {
  if (!lineup || !lineup.slots) return 0;

  return lineup.slots
    .filter((slot: any) => slot.position !== 'BENCH' && slot.player)
    .reduce((total: number, slot: any) => total + (slot.player.projected_points || 0), 0);
};

export const getPositionLimits = () => ({
  QB: { min: 1, max: 4, starter: 1 },
  RB: { min: 2, max: 8, starter: 2 },
  WR: { min: 2, max: 8, starter: 2 },
  TE: { min: 1, max: 4, starter: 1 },
  K: { min: 1, max: 3, starter: 1 },
  DST: { min: 1, max: 3, starter: 1 }
});

export const validateRosterComposition = (roster: any[]): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const limits = getPositionLimits();

  const positionCounts = roster.reduce((counts, player) => {
    counts[player.position] = (counts[player.position] || 0) + 1;
    return counts;
  }, {} as Record<string, number>);

  Object.entries(limits).forEach(([position, limit]) => {
    const count = positionCounts[position] || 0;

    if (count < limit.min) {
      errors.push(`Need at least ${limit.min} ${position} players (have ${count})`);
    } else if (count > limit.max) {
      errors.push(`Cannot have more than ${limit.max} ${position} players (have ${count})`);
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// Form validation helpers
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): ValidationResult => {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings: []
  };
};

export const validateTeamName = (name: string): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!name || name.trim().length === 0) {
    errors.push('Team name is required');
  } else if (name.length < 3) {
    errors.push('Team name must be at least 3 characters long');
  } else if (name.length > 50) {
    errors.push('Team name cannot exceed 50 characters');
  }

  // Check for inappropriate content (basic check)
  const inappropriateWords = ['damn', 'hell']; // This would be more comprehensive in practice
  if (inappropriateWords.some(word => name.toLowerCase().includes(word))) {
    warnings.push('Team name may contain inappropriate content');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};