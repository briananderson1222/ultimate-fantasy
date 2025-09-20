// Fantasy Sports Specific Design Tokens and Theme
import { DesignTokenSystem } from './design-tokens';

export interface FantasyTheme {
  name: string;
  colors: {
    // Team colors
    field: string;
    endzone: string;

    // Position colors
    quarterback: string;
    runningBack: string;
    wideReceiver: string;
    tightEnd: string;
    kicker: string;
    defense: string;

    // Status colors
    healthy: string;
    questionable: string;
    doubtful: string;
    out: string;
    injuredReserve: string;

    // Performance colors
    trending: {
      up: string;
      down: string;
      steady: string;
    };

    // League status
    draft: string;
    active: string;
    playoffs: string;

    // Trade evaluation
    trade: {
      fair: string;
      favorable: string;
      unfavorable: string;
    };

    // Scoring
    points: {
      positive: string;
      negative: string;
      projected: string;
    };
  };

  // Fantasy-specific spacing for different content types
  layout: {
    playerCard: {
      padding: string | number;
      margin: string | number;
      borderRadius: string | number;
    };
    leagueCard: {
      padding: string | number;
      margin: string | number;
      borderRadius: string | number;
    };
    draftBoard: {
      cellPadding: string | number;
      headerHeight: string | number;
    };
    scoreCard: {
      padding: string | number;
      teamSpacing: string | number;
    };
  };

  // Typography specific to fantasy content
  typography: {
    playerName: any;
    teamName: any;
    position: any;
    points: any;
    projection: any;
    statLabel: any;
    statValue: any;
  };
}

// NFL-inspired fantasy theme
export const nflFantasyTheme: FantasyTheme = {
  name: 'nfl',
  colors: {
    // Field colors inspired by NFL
    field: '#2F5233', // Field green
    endzone: '#003D82', // NFL blue

    // Position colors - distinct and accessible
    quarterback: '#FF6B35', // Orange - QB is the focal point
    runningBack: '#2E8B57', // Sea green - ground game
    wideReceiver: '#DC143C', // Crimson - speed and excitement
    tightEnd: '#4B0082', // Indigo - versatility
    kicker: '#FFD700', // Gold - precision
    defense: '#2F4F4F', // Dark slate gray - defense

    // Injury status with clear visual hierarchy
    healthy: '#228B22', // Forest green
    questionable: '#FFA500', // Orange
    doubtful: '#FF6347', // Tomato
    out: '#DC143C', // Crimson
    injuredReserve: '#800080', // Purple

    // Performance trends
    trending: {
      up: '#32CD32', // Lime green
      down: '#FF4500', // Orange red
      steady: '#808080', // Gray
    },

    // League status progression
    draft: '#4169E1', // Royal blue
    active: '#228B22', // Forest green
    playoffs: '#FFD700', // Gold

    // Trade evaluation
    trade: {
      fair: '#228B22', // Green
      favorable: '#32CD32', // Lime green
      unfavorable: '#FF6347', // Tomato
    },

    // Scoring colors
    points: {
      positive: '#228B22', // Green
      negative: '#DC143C', // Crimson
      projected: '#808080', // Gray
    },
  },

  layout: {
    playerCard: {
      padding: 16,
      margin: 8,
      borderRadius: 12,
    },
    leagueCard: {
      padding: 16,
      margin: 8,
      borderRadius: 12,
    },
    draftBoard: {
      cellPadding: 8,
      headerHeight: 40,
    },
    scoreCard: {
      padding: 16,
      teamSpacing: 24,
    },
  },

  typography: {
    playerName: {
      fontSize: 16,
      fontWeight: '600',
      letterSpacing: 0.5,
    },
    teamName: {
      fontSize: 18,
      fontWeight: 'bold',
      letterSpacing: 0.5,
    },
    position: {
      fontSize: 12,
      fontWeight: '700',
      letterSpacing: 1,
      textTransform: 'uppercase',
    },
    points: {
      fontSize: 20,
      fontWeight: 'bold',
      fontFamily: 'monospace',
    },
    projection: {
      fontSize: 12,
      fontWeight: '500',
      fontStyle: 'italic',
    },
    statLabel: {
      fontSize: 12,
      fontWeight: '500',
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    statValue: {
      fontSize: 14,
      fontWeight: '600',
      fontFamily: 'monospace',
    },
  },
};

// Basketball fantasy theme
export const nbaFantasyTheme: FantasyTheme = {
  name: 'nba',
  colors: {
    field: '#8B4513', // Saddle brown - court color
    endzone: '#FF8C00', // Dark orange - rim color

    // Position colors for basketball
    quarterback: '#FF4500', // Point Guard - Orange red
    runningBack: '#4169E1', // Shooting Guard - Royal blue
    wideReceiver: '#FF1493', // Small Forward - Deep pink
    tightEnd: '#32CD32', // Power Forward - Lime green
    kicker: '#9370DB', // Center - Medium purple
    defense: '#2F4F4F', // Bench - Dark slate gray

    healthy: '#32CD32',
    questionable: '#FFA500',
    doubtful: '#FF6347',
    out: '#DC143C',
    injuredReserve: '#800080',

    trending: {
      up: '#32CD32',
      down: '#FF4500',
      steady: '#808080',
    },

    draft: '#4169E1',
    active: '#32CD32',
    playoffs: '#FFD700',

    trade: {
      fair: '#32CD32',
      favorable: '#7FFF00',
      unfavorable: '#FF6347',
    },

    points: {
      positive: '#32CD32',
      negative: '#DC143C',
      projected: '#808080',
    },
  },

  layout: {
    playerCard: {
      padding: 14,
      margin: 6,
      borderRadius: 8,
    },
    leagueCard: {
      padding: 16,
      margin: 8,
      borderRadius: 10,
    },
    draftBoard: {
      cellPadding: 6,
      headerHeight: 36,
    },
    scoreCard: {
      padding: 14,
      teamSpacing: 20,
    },
  },

  typography: {
    playerName: {
      fontSize: 15,
      fontWeight: '600',
      letterSpacing: 0.3,
    },
    teamName: {
      fontSize: 17,
      fontWeight: 'bold',
      letterSpacing: 0.3,
    },
    position: {
      fontSize: 11,
      fontWeight: '700',
      letterSpacing: 0.8,
      textTransform: 'uppercase',
    },
    points: {
      fontSize: 18,
      fontWeight: 'bold',
      fontFamily: 'monospace',
    },
    projection: {
      fontSize: 11,
      fontWeight: '500',
      fontStyle: 'italic',
    },
    statLabel: {
      fontSize: 11,
      fontWeight: '500',
      textTransform: 'uppercase',
      letterSpacing: 0.3,
    },
    statValue: {
      fontSize: 13,
      fontWeight: '600',
      fontFamily: 'monospace',
    },
  },
};

// Utility functions for fantasy themes
export const getPositionColor = (position: string, theme: FantasyTheme = nflFantasyTheme): string => {
  const positionMap: Record<string, keyof FantasyTheme['colors']> = {
    'QB': 'quarterback',
    'RB': 'runningBack',
    'WR': 'wideReceiver',
    'TE': 'tightEnd',
    'K': 'kicker',
    'DST': 'defense',
    'DEF': 'defense',
    // Basketball positions
    'PG': 'quarterback',
    'SG': 'runningBack',
    'SF': 'wideReceiver',
    'PF': 'tightEnd',
    'C': 'kicker',
  };

  const colorKey = positionMap[position.toUpperCase()];
  return colorKey ? theme.colors[colorKey] : theme.colors.defense;
};

export const getInjuryStatusColor = (status: string, theme: FantasyTheme = nflFantasyTheme): string => {
  const statusMap: Record<string, keyof FantasyTheme['colors']> = {
    'healthy': 'healthy',
    'questionable': 'questionable',
    'doubtful': 'doubtful',
    'out': 'out',
    'ir': 'injuredReserve',
  };

  const colorKey = statusMap[status.toLowerCase()];
  return colorKey ? theme.colors[colorKey] : theme.colors.healthy;
};

export const getTrendingColor = (trend: 'up' | 'down' | 'steady', theme: FantasyTheme = nflFantasyTheme): string => {
  return theme.colors.trending[trend];
};

export const getTradeEvaluationColor = (evaluation: 'fair' | 'favorable' | 'unfavorable', theme: FantasyTheme = nflFantasyTheme): string => {
  return theme.colors.trade[evaluation];
};

// Create themed design token system
export const createFantasyDesignSystem = (fantasyTheme: FantasyTheme): DesignTokenSystem => {
  const system = new DesignTokenSystem();

  // Add fantasy-specific color tokens
  Object.entries(fantasyTheme.colors).forEach(([key, value]) => {
    if (typeof value === 'string') {
      // Simple color value
      system['addToken'](system['DesignToken'].createColor(`fantasy-${key}`, value, value, value));
    } else if (typeof value === 'object') {
      // Nested color object
      Object.entries(value).forEach(([subKey, subValue]) => {
        if (typeof subValue === 'string') {
          system['addToken'](system['DesignToken'].createColor(`fantasy-${key}-${subKey}`, subValue, subValue, subValue));
        }
      });
    }
  });

  return system;
};

// Export default theme
export const defaultFantasyTheme = nflFantasyTheme;

// Theme selector utility
export const getFantasyTheme = (sport: 'nfl' | 'nba' = 'nfl'): FantasyTheme => {
  switch (sport) {
    case 'nba':
      return nbaFantasyTheme;
    case 'nfl':
    default:
      return nflFantasyTheme;
  }
};

// CSS custom properties generator for fantasy themes
export const generateFantasyCSS = (theme: FantasyTheme): string => {
  const flattenColors = (obj: any, prefix = ''): Record<string, string> => {
    const result: Record<string, string> = {};

    Object.entries(obj).forEach(([key, value]) => {
      if (typeof value === 'string') {
        result[`${prefix}${key}`] = value;
      } else if (typeof value === 'object' && value !== null) {
        Object.assign(result, flattenColors(value, `${prefix}${key}-`));
      }
    });

    return result;
  };

  const colors = flattenColors(theme.colors, 'fantasy-color-');

  const cssProperties = Object.entries(colors)
    .map(([key, value]) => `  --uf-${key}: ${value};`)
    .join('\n');

  return `:root {\n${cssProperties}\n}`;
};

export default {
  nflFantasyTheme,
  nbaFantasyTheme,
  getPositionColor,
  getInjuryStatusColor,
  getTrendingColor,
  getTradeEvaluationColor,
  createFantasyDesignSystem,
  getFantasyTheme,
  generateFantasyCSS,
};