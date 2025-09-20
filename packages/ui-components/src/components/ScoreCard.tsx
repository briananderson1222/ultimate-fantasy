import React from 'react';
import { designTokens } from '../tokens/design-tokens';

export interface TeamScore {
  team_id: string;
  team_name: string;
  team_owner: string;
  projected_points: number;
  actual_points: number;
  is_winner?: boolean;
  avatar_url?: string;
}

export interface Matchup {
  id: string;
  week: number;
  home_team: TeamScore;
  away_team: TeamScore;
  status: 'scheduled' | 'in_progress' | 'completed';
  game_time?: string;
}

export interface ScoreCardProps {
  matchup: Matchup;
  variant?: 'default' | 'compact' | 'detailed';
  showProjections?: boolean;
  showOwners?: boolean;
  onPress?: (matchup: Matchup) => void;
  style?: any;
  platform?: 'web' | 'mobile';
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  matchup,
  variant = 'default',
  showProjections = true,
  showOwners = false,
  onPress,
  style,
  platform = 'web'
}) => {
  const handlePress = () => {
    if (onPress) {
      onPress(matchup);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return designTokens.getColorValue('neutral-400', platform);
      case 'in_progress': return designTokens.getColorValue('warning-yellow', platform);
      case 'completed': return designTokens.getColorValue('success-green', platform);
      default: return designTokens.getColorValue('neutral-400', platform);
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'scheduled': return 'Upcoming';
      case 'in_progress': return 'Live';
      case 'completed': return 'Final';
      default: return 'Unknown';
    }
  };

  const formatScore = (actual: number, projected: number, showProjected: boolean) => {
    if (matchup.status === 'scheduled' && showProjected) {
      return `${projected.toFixed(1)}`;
    }
    return `${actual.toFixed(1)}`;
  };

  const getWinnerStyle = (team: TeamScore) => {
    if (matchup.status !== 'completed') return {};

    return team.is_winner ? {
      backgroundColor: designTokens.getColorValue('success-green', platform) + '10',
      borderColor: designTokens.getColorValue('success-green', platform),
      borderWidth: 2
    } : {};
  };

  if (platform === 'web') {
    const baseStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('neutral-50', platform),
      border: `1px solid ${designTokens.getColorValue('neutral-200', platform)}`,
      borderRadius: '12px',
      padding: variant === 'compact' ? '12px' : '16px',
      cursor: onPress ? 'pointer' : 'default',
      transition: 'all 0.2s ease',
      position: 'relative',
      ...(onPress && {
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
      alignItems: 'center',
      marginBottom: '12px'
    };

    const weekLabelStyles: React.CSSProperties = {
      fontSize: '12px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-600', platform)
    };

    const statusBadgeStyles: React.CSSProperties = {
      backgroundColor: getStatusColor(matchup.status),
      color: 'white',
      padding: '4px 8px',
      borderRadius: '6px',
      fontSize: '10px',
      fontWeight: '600',
      textTransform: 'uppercase' as const
    };

    const matchupStyles: React.CSSProperties = {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '16px'
    };

    const teamStyles: React.CSSProperties = {
      flex: 1,
      textAlign: 'center' as const
    };

    const teamNameStyles: React.CSSProperties = {
      fontSize: variant === 'compact' ? '14px' : '16px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      marginBottom: '4px'
    };

    const ownerNameStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-600', platform),
      marginBottom: '8px'
    };

    const scoreStyles: React.CSSProperties = {
      fontSize: variant === 'compact' ? '18px' : '24px',
      fontWeight: 'bold',
      color: designTokens.getColorValue('primary-blue', platform)
    };

    const projectionStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-500', platform),
      marginTop: '4px'
    };

    const vsStyles: React.CSSProperties = {
      fontSize: '14px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-400', platform),
      padding: '0 8px'
    };

    const gameTimeStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-500', platform),
      textAlign: 'center' as const,
      marginTop: '8px'
    };

    return (
      <div style={baseStyles} onClick={onPress ? handlePress : undefined}>
        <div style={headerStyles}>
          <div style={weekLabelStyles}>Week {matchup.week}</div>
          <div style={statusBadgeStyles}>{getStatusLabel(matchup.status)}</div>
        </div>

        <div style={matchupStyles}>
          <div style={{ ...teamStyles, ...getWinnerStyle(matchup.away_team) }}>
            <div style={teamNameStyles}>{matchup.away_team.team_name}</div>
            {showOwners && (
              <div style={ownerNameStyles}>{matchup.away_team.team_owner}</div>
            )}
            <div style={scoreStyles}>
              {formatScore(matchup.away_team.actual_points, matchup.away_team.projected_points, showProjections)}
            </div>
            {showProjections && matchup.status !== 'scheduled' && (
              <div style={projectionStyles}>
                Proj: {matchup.away_team.projected_points.toFixed(1)}
              </div>
            )}
          </div>

          <div style={vsStyles}>VS</div>

          <div style={{ ...teamStyles, ...getWinnerStyle(matchup.home_team) }}>
            <div style={teamNameStyles}>{matchup.home_team.team_name}</div>
            {showOwners && (
              <div style={ownerNameStyles}>{matchup.home_team.team_owner}</div>
            )}
            <div style={scoreStyles}>
              {formatScore(matchup.home_team.actual_points, matchup.home_team.projected_points, showProjections)}
            </div>
            {showProjections && matchup.status !== 'scheduled' && (
              <div style={projectionStyles}>
                Proj: {matchup.home_team.projected_points.toFixed(1)}
              </div>
            )}
          </div>
        </div>

        {matchup.game_time && (
          <div style={gameTimeStyles}>
            {new Date(matchup.game_time).toLocaleString()}
          </div>
        )}
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
      borderColor: designTokens.getColorValue('neutral-200', platform),
      borderRadius: 12,
      padding: variant === 'compact' ? 12 : 16,
      marginBottom: 8,
      ...style
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12
    },
    weekLabel: {
      fontSize: 12,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-600', platform)
    },
    statusBadge: {
      backgroundColor: getStatusColor(matchup.status),
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6
    },
    statusText: {
      color: 'white',
      fontSize: 10,
      fontWeight: '600',
      textTransform: 'uppercase'
    },
    matchup: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    team: {
      flex: 1,
      alignItems: 'center'
    },
    winnerTeam: {
      backgroundColor: designTokens.getColorValue('success-green', platform) + '10',
      borderWidth: 2,
      borderColor: designTokens.getColorValue('success-green', platform),
      borderRadius: 8,
      padding: 8
    },
    teamName: {
      fontSize: variant === 'compact' ? 14 : 16,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      textAlign: 'center',
      marginBottom: 4
    },
    ownerName: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform),
      textAlign: 'center',
      marginBottom: 8
    },
    score: {
      fontSize: variant === 'compact' ? 18 : 24,
      fontWeight: 'bold',
      color: designTokens.getColorValue('primary-blue', platform),
      textAlign: 'center'
    },
    projection: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-500', platform),
      textAlign: 'center',
      marginTop: 4
    },
    vs: {
      fontSize: 14,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-400', platform),
      paddingHorizontal: 8
    },
    gameTime: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-500', platform),
      textAlign: 'center',
      marginTop: 8
    }
  });

  const CardComponent = onPress ? TouchableOpacity : View;

  const getTeamStyle = (team: TeamScore) => {
    if (matchup.status === 'completed' && team.is_winner) {
      return [styles.team, styles.winnerTeam];
    }
    return styles.team;
  };

  return (
    <CardComponent
      style={styles.container}
      onPress={onPress ? handlePress : undefined}
      activeOpacity={onPress ? 0.7 : 1}
    >
      <View style={styles.header}>
        <Text style={styles.weekLabel}>Week {matchup.week}</Text>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>{getStatusLabel(matchup.status)}</Text>
        </View>
      </View>

      <View style={styles.matchup}>
        <View style={getTeamStyle(matchup.away_team)}>
          <Text style={styles.teamName}>{matchup.away_team.team_name}</Text>
          {showOwners && (
            <Text style={styles.ownerName}>{matchup.away_team.team_owner}</Text>
          )}
          <Text style={styles.score}>
            {formatScore(matchup.away_team.actual_points, matchup.away_team.projected_points, showProjections)}
          </Text>
          {showProjections && matchup.status !== 'scheduled' && (
            <Text style={styles.projection}>
              Proj: {matchup.away_team.projected_points.toFixed(1)}
            </Text>
          )}
        </View>

        <Text style={styles.vs}>VS</Text>

        <View style={getTeamStyle(matchup.home_team)}>
          <Text style={styles.teamName}>{matchup.home_team.team_name}</Text>
          {showOwners && (
            <Text style={styles.ownerName}>{matchup.home_team.team_owner}</Text>
          )}
          <Text style={styles.score}>
            {formatScore(matchup.home_team.actual_points, matchup.home_team.projected_points, showProjections)}
          </Text>
          {showProjections && matchup.status !== 'scheduled' && (
            <Text style={styles.projection}>
              Proj: {matchup.home_team.projected_points.toFixed(1)}
            </Text>
          )}
        </View>
      </View>

      {matchup.game_time && (
        <Text style={styles.gameTime}>
          {new Date(matchup.game_time).toLocaleString()}
        </Text>
      )}
    </CardComponent>
  );
};

// Web-specific wrapper
export const WebScoreCard: React.FC<ScoreCardProps> = (props) => {
  return <ScoreCard {...props} platform="web" />;
};

// Mobile-specific wrapper
export const MobileScoreCard: React.FC<ScoreCardProps> = (props) => {
  return <ScoreCard {...props} platform="mobile" />;
};

export default ScoreCard;