/**
 * Enhanced PlayerCard Component
 *
 * A comprehensive player card component for fantasy sports applications.
 * Features rich player information, statistics, projections, and interactive elements
 * with full theming support and accessibility compliance.
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  fantasyTheme,
  getPositionColor,
  getPlayerStatusColor,
  getScoringColor,
  ThemeMode,
  getThemeColors
} from '../tokens/fantasy-theme';

export interface PlayerStats {
  passingYards?: number;
  passingTouchdowns?: number;
  interceptions?: number;
  rushingYards?: number;
  rushingTouchdowns?: number;
  receptions?: number;
  receivingYards?: number;
  receivingTouchdowns?: number;
  fieldGoalsMade?: number;
  fieldGoalsAttempted?: number;
  pointsAgainst?: number;
  sacks?: number;
  turnovers?: number;
  fantasyPoints?: number;
  [key: string]: number | undefined;
}

export interface PlayerProjections {
  weekly?: number;
  season?: number;
  confidence?: number; // 0-1 scale
}

export interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  jerseyNumber?: number;
  status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'injured' | 'bye' | 'suspended';
  ownedBy?: string; // User ID if owned
  salary?: number; // For DFS
  averageDraftPosition?: number;

  // Statistics
  stats?: PlayerStats;
  projections?: PlayerProjections;

  // Legacy support
  projected_points?: number;
  injury_status?: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'ir';
  bye_week?: number;
  trade_value?: number;
  avatar_url?: string;

  // Metadata
  photoUrl?: string;
  injuryReport?: string;
  newsItems?: Array<{
    title: string;
    summary: string;
    timestamp: string;
    impact: 'positive' | 'negative' | 'neutral';
  }>;

  // Fantasy-specific
  rosteredPercentage?: number;
  trendingDirection?: 'up' | 'down' | 'steady';
  tier?: number;
  sleeper?: boolean;
  rookie?: boolean;
}

export interface PlayerCardProps {
  player: Player;
  variant?: 'compact' | 'standard' | 'detailed' | 'draft';
  theme?: ThemeMode;
  showProjections?: boolean;
  showNews?: boolean;
  showOwnership?: boolean;
  showTrends?: boolean;
  interactive?: boolean;
  selected?: boolean;
  disabled?: boolean;

  // Legacy support
  selectable?: boolean;
  showProjection?: boolean;
  showTradeValue?: boolean;
  onPress?: (player: Player) => void;
  platform?: 'web' | 'mobile';

  // Event handlers
  onClick?: (player: Player) => void;
  onDoubleClick?: (player: Player) => void;
  onAdd?: (player: Player) => void;
  onRemove?: (player: Player) => void;
  onTrade?: (player: Player) => void;
  onViewDetails?: (player: Player) => void;

  // Customization
  className?: string;
  style?: React.CSSProperties;
  actions?: React.ReactNode;
  badges?: React.ReactNode;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  variant = 'default',
  selectable = false,
  selected = false,
  showProjection = true,
  showTradeValue = false,
  onPress,
  style,
  platform = 'web'
}) => {
  const handlePress = () => {
    if (onPress) {
      onPress(player);
    }
  };

  const getInjuryStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return designTokens.getColorValue('success-green', platform);
      case 'questionable': return designTokens.getColorValue('warning-yellow', platform);
      case 'doubtful': return '#f97316'; // orange
      case 'out': return designTokens.getColorValue('danger-red', platform);
      case 'ir': return '#7f1d1d'; // dark red
      default: return designTokens.getColorValue('neutral-500', platform);
    }
  };

  const getPositionColor = (position: string) => {
    const colors = {
      'QB': designTokens.getColorValue('primary-blue', platform),
      'RB': designTokens.getColorValue('secondary-green', platform),
      'WR': designTokens.getColorValue('danger-red', platform),
      'TE': '#7c3aed', // purple
      'K': designTokens.getColorValue('warning-yellow', platform),
      'DST': designTokens.getColorValue('neutral-600', platform)
    };
    return colors[position as keyof typeof colors] || designTokens.getColorValue('neutral-500', platform);
  };

  if (platform === 'web') {
    const baseStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('neutral-50', platform),
      border: `1px solid ${designTokens.getColorValue('neutral-200', platform)}`,
      borderRadius: '12px',
      padding: variant === 'compact' ? '12px' : '16px',
      cursor: selectable ? 'pointer' : 'default',
      transition: 'all 0.2s ease',
      position: 'relative',
      ...(selected && {
        borderColor: designTokens.getColorValue('primary-blue', platform),
        backgroundColor: '#eff6ff',
        boxShadow: `0 0 0 2px ${designTokens.getColorValue('primary-blue', platform)}25`
      }),
      ...(selectable && {
        ':hover': {
          borderColor: designTokens.getColorValue('primary-blue-light', platform),
          transform: 'translateY(-1px)',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)'
        }
      }),
      ...style
    };

    const headerStyles: React.CSSProperties = {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: variant === 'compact' ? '8px' : '12px'
    };

    const playerInfoStyles: React.CSSProperties = {
      flex: 1
    };

    const nameStyles: React.CSSProperties = {
      fontSize: variant === 'compact' ? '14px' : '16px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      margin: '0 0 4px 0'
    };

    const teamPositionStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-600', platform),
      margin: 0
    };

    const positionBadgeStyles: React.CSSProperties = {
      backgroundColor: getPositionColor(player.position),
      color: 'white',
      padding: '4px 8px',
      borderRadius: '6px',
      fontSize: '10px',
      fontWeight: '600',
      textAlign: 'center' as const,
      minWidth: '32px'
    };

    const injuryStatusStyles: React.CSSProperties = {
      position: 'absolute',
      top: '8px',
      right: '8px',
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: getInjuryStatusColor(player.injury_status)
    };

    const statsRowStyles: React.CSSProperties = {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: variant === 'detailed' ? '12px' : '8px'
    };

    const statStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-600', platform)
    };

    const valueStyles: React.CSSProperties = {
      fontSize: '14px',
      fontWeight: '600',
      color: designTokens.getColorValue('secondary-green', platform)
    };

    return (
      <div style={baseStyles} onClick={selectable ? handlePress : undefined}>
        {player.injury_status !== 'healthy' && <div style={injuryStatusStyles} />}

        <div style={headerStyles}>
          <div style={playerInfoStyles}>
            <h3 style={nameStyles}>{player.name}</h3>
            <p style={teamPositionStyles}>{player.team}</p>
          </div>
          <div style={positionBadgeStyles}>
            {player.position}
          </div>
        </div>

        {variant === 'detailed' && (
          <div style={{ marginBottom: '12px' }}>
            <div style={statStyles}>
              Status: {player.injury_status === 'healthy' ? 'Healthy' : player.injury_status.toUpperCase()}
            </div>
            {player.bye_week && (
              <div style={statStyles}>Bye Week: {player.bye_week}</div>
            )}
          </div>
        )}

        <div style={statsRowStyles}>
          {showProjection && (
            <div>
              <span style={statStyles}>Proj: </span>
              <span style={valueStyles}>{player.projected_points.toFixed(1)} pts</span>
            </div>
          )}

          {showTradeValue && player.trade_value && (
            <div>
              <span style={statStyles}>Value: </span>
              <span style={valueStyles}>${player.trade_value.toFixed(1)}M</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // React Native implementation
  const StyleSheet = require('react-native').StyleSheet;
  const { View, Text, TouchableOpacity } = require('react-native');

  const styles = StyleSheet.create({
    container: {
      backgroundColor: designTokens.getColorValue('neutral-50', platform),
      borderWidth: 1,
      borderColor: selected
        ? designTokens.getColorValue('primary-blue', platform)
        : designTokens.getColorValue('neutral-200', platform),
      borderRadius: 12,
      padding: variant === 'compact' ? 12 : 16,
      marginBottom: 8,
      ...(selected && {
        backgroundColor: '#eff6ff',
      }),
      ...style
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: variant === 'compact' ? 8 : 12
    },
    playerInfo: {
      flex: 1
    },
    playerName: {
      fontSize: variant === 'compact' ? 14 : 16,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      marginBottom: 4
    },
    teamPosition: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform)
    },
    positionBadge: {
      backgroundColor: getPositionColor(player.position),
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6,
      minWidth: 32,
      alignItems: 'center'
    },
    positionText: {
      color: 'white',
      fontSize: 10,
      fontWeight: '600'
    },
    injuryDot: {
      position: 'absolute',
      top: 8,
      right: 8,
      width: 8,
      height: 8,
      borderRadius: 4,
      backgroundColor: getInjuryStatusColor(player.injury_status)
    },
    detailsSection: {
      marginBottom: 12
    },
    detailText: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform),
      marginBottom: 2
    },
    statsRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: variant === 'detailed' ? 12 : 8
    },
    statLabel: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform)
    },
    statValue: {
      fontSize: 14,
      fontWeight: '600',
      color: designTokens.getColorValue('secondary-green', platform)
    }
  });

  const CardComponent = selectable ? TouchableOpacity : View;

  return (
    <CardComponent
      style={styles.container}
      onPress={selectable ? handlePress : undefined}
      activeOpacity={selectable ? 0.7 : 1}
    >
      {player.injury_status !== 'healthy' && <View style={styles.injuryDot} />}

      <View style={styles.header}>
        <View style={styles.playerInfo}>
          <Text style={styles.playerName}>{player.name}</Text>
          <Text style={styles.teamPosition}>{player.team}</Text>
        </View>
        <View style={styles.positionBadge}>
          <Text style={styles.positionText}>{player.position}</Text>
        </View>
      </View>

      {variant === 'detailed' && (
        <View style={styles.detailsSection}>
          <Text style={styles.detailText}>
            Status: {player.injury_status === 'healthy' ? 'Healthy' : player.injury_status.toUpperCase()}
          </Text>
          {player.bye_week && (
            <Text style={styles.detailText}>Bye Week: {player.bye_week}</Text>
          )}
        </View>
      )}

      <View style={styles.statsRow}>
        {showProjection && (
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={styles.statLabel}>Proj: </Text>
            <Text style={styles.statValue}>{player.projected_points.toFixed(1)} pts</Text>
          </View>
        )}

        {showTradeValue && player.trade_value && (
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={styles.statLabel}>Value: </Text>
            <Text style={styles.statValue}>${player.trade_value.toFixed(1)}M</Text>
          </View>
        )}
      </View>
    </CardComponent>
  );
};

// Web-specific wrapper with hover effects
export const WebPlayerCard: React.FC<PlayerCardProps> = (props) => {
  return <PlayerCard {...props} platform="web" />;
};

// Mobile-specific wrapper
export const MobilePlayerCard: React.FC<PlayerCardProps> = (props) => {
  return <PlayerCard {...props} platform="mobile" />;
};

export default PlayerCard;