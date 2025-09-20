import React from 'react';
import { designTokens } from '../tokens/design-tokens';

export interface League {
  id: string;
  name: string;
  status: 'setup' | 'drafting' | 'active' | 'completed';
  total_teams: number;
  current_teams: number;
  scoring_type: 'standard' | 'ppr' | 'half_ppr';
  draft_date?: string;
  user_team?: {
    name: string;
    record: string;
    rank: number;
  };
  avatar_url?: string;
}

export interface LeagueCardProps {
  league: League;
  variant?: 'default' | 'compact' | 'detailed';
  showUserTeam?: boolean;
  onPress?: (league: League) => void;
  onJoin?: (league: League) => void;
  style?: any;
  platform?: 'web' | 'mobile';
}

export const LeagueCard: React.FC<LeagueCardProps> = ({
  league,
  variant = 'default',
  showUserTeam = true,
  onPress,
  onJoin,
  style,
  platform = 'web'
}) => {
  const handlePress = () => {
    if (onPress) {
      onPress(league);
    }
  };

  const handleJoin = (e: any) => {
    e.stopPropagation();
    if (onJoin) {
      onJoin(league);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'setup': return designTokens.getColorValue('warning-yellow', platform);
      case 'drafting': return designTokens.getColorValue('info-blue', platform);
      case 'active': return designTokens.getColorValue('success-green', platform);
      case 'completed': return designTokens.getColorValue('neutral-500', platform);
      default: return designTokens.getColorValue('neutral-400', platform);
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'setup': return 'Setting Up';
      case 'drafting': return 'Drafting';
      case 'active': return 'Active';
      case 'completed': return 'Completed';
      default: return 'Unknown';
    }
  };

  const getScoringTypeLabel = (type: string) => {
    switch (type) {
      case 'standard': return 'Standard';
      case 'ppr': return 'PPR';
      case 'half_ppr': return 'Half PPR';
      default: return type.toUpperCase();
    }
  };

  const canJoin = league.status === 'setup' && league.current_teams < league.total_teams && !league.user_team;

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
      alignItems: 'flex-start',
      marginBottom: variant === 'compact' ? '8px' : '12px'
    };

    const leagueInfoStyles: React.CSSProperties = {
      flex: 1
    };

    const nameStyles: React.CSSProperties = {
      fontSize: variant === 'compact' ? '16px' : '18px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      margin: '0 0 4px 0'
    };

    const statusBadgeStyles: React.CSSProperties = {
      backgroundColor: getStatusColor(league.status),
      color: 'white',
      padding: '4px 8px',
      borderRadius: '6px',
      fontSize: '10px',
      fontWeight: '600',
      textAlign: 'center' as const,
      textTransform: 'uppercase' as const
    };

    const detailsStyles: React.CSSProperties = {
      display: 'flex',
      flexWrap: 'wrap' as const,
      gap: '12px',
      marginBottom: variant === 'detailed' ? '12px' : '8px',
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-600', platform)
    };

    const userTeamStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('primary-blue', platform) + '10',
      border: `1px solid ${designTokens.getColorValue('primary-blue', platform)}30`,
      borderRadius: '8px',
      padding: '8px 12px',
      marginTop: '8px'
    };

    const teamNameStyles: React.CSSProperties = {
      fontSize: '14px',
      fontWeight: '600',
      color: designTokens.getColorValue('primary-blue', platform),
      margin: '0 0 4px 0'
    };

    const teamStatsStyles: React.CSSProperties = {
      fontSize: '12px',
      color: designTokens.getColorValue('neutral-600', platform)
    };

    const joinButtonStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('secondary-green', platform),
      color: 'white',
      border: 'none',
      padding: '8px 16px',
      borderRadius: '6px',
      fontSize: '12px',
      fontWeight: '600',
      cursor: 'pointer',
      marginTop: '8px',
      transition: 'background-color 0.2s ease'
    };

    return (
      <div style={baseStyles} onClick={onPress ? handlePress : undefined}>
        <div style={headerStyles}>
          <div style={leagueInfoStyles}>
            <h3 style={nameStyles}>{league.name}</h3>
          </div>
          <div style={statusBadgeStyles}>
            {getStatusLabel(league.status)}
          </div>
        </div>

        <div style={detailsStyles}>
          <div>
            <strong>Teams:</strong> {league.current_teams}/{league.total_teams}
          </div>
          <div>
            <strong>Scoring:</strong> {getScoringTypeLabel(league.scoring_type)}
          </div>
          {league.draft_date && (
            <div>
              <strong>Draft:</strong> {new Date(league.draft_date).toLocaleDateString()}
            </div>
          )}
        </div>

        {showUserTeam && league.user_team && (
          <div style={userTeamStyles}>
            <h4 style={teamNameStyles}>{league.user_team.name}</h4>
            <div style={teamStatsStyles}>
              Record: {league.user_team.record} • Rank: #{league.user_team.rank}
            </div>
          </div>
        )}

        {canJoin && (
          <button style={joinButtonStyles} onClick={handleJoin}>
            Join League
          </button>
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
      alignItems: 'flex-start',
      marginBottom: variant === 'compact' ? 8 : 12
    },
    leagueInfo: {
      flex: 1
    },
    leagueName: {
      fontSize: variant === 'compact' ? 16 : 18,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      marginBottom: 4
    },
    statusBadge: {
      backgroundColor: getStatusColor(league.status),
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6,
      alignItems: 'center'
    },
    statusText: {
      color: 'white',
      fontSize: 10,
      fontWeight: '600',
      textTransform: 'uppercase'
    },
    detailsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginBottom: variant === 'detailed' ? 12 : 8
    },
    detailItem: {
      marginRight: 16,
      marginBottom: 4
    },
    detailText: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform)
    },
    detailLabel: {
      fontWeight: '600'
    },
    userTeamContainer: {
      backgroundColor: designTokens.getColorValue('primary-blue', platform) + '10',
      borderWidth: 1,
      borderColor: designTokens.getColorValue('primary-blue', platform) + '30',
      borderRadius: 8,
      padding: 12,
      marginTop: 8
    },
    teamName: {
      fontSize: 14,
      fontWeight: '600',
      color: designTokens.getColorValue('primary-blue', platform),
      marginBottom: 4
    },
    teamStats: {
      fontSize: 12,
      color: designTokens.getColorValue('neutral-600', platform)
    },
    joinButton: {
      backgroundColor: designTokens.getColorValue('secondary-green', platform),
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 6,
      marginTop: 8,
      alignItems: 'center'
    },
    joinButtonText: {
      color: 'white',
      fontSize: 12,
      fontWeight: '600'
    }
  });

  const CardComponent = onPress ? TouchableOpacity : View;

  return (
    <CardComponent
      style={styles.container}
      onPress={onPress ? handlePress : undefined}
      activeOpacity={onPress ? 0.7 : 1}
    >
      <View style={styles.header}>
        <View style={styles.leagueInfo}>
          <Text style={styles.leagueName}>{league.name}</Text>
        </View>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>{getStatusLabel(league.status)}</Text>
        </View>
      </View>

      <View style={styles.detailsRow}>
        <View style={styles.detailItem}>
          <Text style={styles.detailText}>
            <Text style={styles.detailLabel}>Teams:</Text> {league.current_teams}/{league.total_teams}
          </Text>
        </View>
        <View style={styles.detailItem}>
          <Text style={styles.detailText}>
            <Text style={styles.detailLabel}>Scoring:</Text> {getScoringTypeLabel(league.scoring_type)}
          </Text>
        </View>
        {league.draft_date && (
          <View style={styles.detailItem}>
            <Text style={styles.detailText}>
              <Text style={styles.detailLabel}>Draft:</Text> {new Date(league.draft_date).toLocaleDateString()}
            </Text>
          </View>
        )}
      </View>

      {showUserTeam && league.user_team && (
        <View style={styles.userTeamContainer}>
          <Text style={styles.teamName}>{league.user_team.name}</Text>
          <Text style={styles.teamStats}>
            Record: {league.user_team.record} • Rank: #{league.user_team.rank}
          </Text>
        </View>
      )}

      {canJoin && (
        <TouchableOpacity style={styles.joinButton} onPress={handleJoin}>
          <Text style={styles.joinButtonText}>Join League</Text>
        </TouchableOpacity>
      )}
    </CardComponent>
  );
};

// Web-specific wrapper
export const WebLeagueCard: React.FC<LeagueCardProps> = (props) => {
  return <LeagueCard {...props} platform="web" />;
};

// Mobile-specific wrapper
export const MobileLeagueCard: React.FC<LeagueCardProps> = (props) => {
  return <LeagueCard {...props} platform="mobile" />;
};

export default LeagueCard;