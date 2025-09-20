import React from 'react';
import { designTokens } from '../tokens/design-tokens';

export interface DraftPick {
  pick_number: number;
  round: number;
  team_id: string;
  team_name: string;
  player_id?: string;
  player_name?: string;
  player_position?: string;
  timestamp?: string;
}

export interface DraftTeam {
  id: string;
  name: string;
  owner: string;
  pick_order: number;
  is_current_turn: boolean;
  is_user_team: boolean;
}

export interface DraftBoardProps {
  teams: DraftTeam[];
  picks: DraftPick[];
  currentPick: number;
  totalRounds: number;
  variant?: 'default' | 'compact';
  onPickPress?: (pick: DraftPick) => void;
  style?: any;
  platform?: 'web' | 'mobile';
}

export const DraftBoard: React.FC<DraftBoardProps> = ({
  teams,
  picks,
  currentPick,
  totalRounds,
  variant = 'default',
  onPickPress,
  style,
  platform = 'web'
}) => {
  const getPickForPosition = (round: number, pickOrder: number): DraftPick | null => {
    // Calculate actual pick number based on snake draft format
    let actualPickOrder: number;
    if (round % 2 === 1) {
      // Odd rounds: normal order
      actualPickOrder = pickOrder;
    } else {
      // Even rounds: reverse order
      actualPickOrder = teams.length - pickOrder + 1;
    }

    const pickNumber = (round - 1) * teams.length + actualPickOrder;
    return picks.find(pick => pick.pick_number === pickNumber) || null;
  };

  const isCurrentPick = (round: number, pickOrder: number): boolean => {
    const pick = getPickForPosition(round, pickOrder);
    return pick ? pick.pick_number === currentPick : false;
  };

  const getTeamByPickOrder = (pickOrder: number): DraftTeam | undefined => {
    return teams.find(team => team.pick_order === pickOrder);
  };

  if (platform === 'web') {
    const containerStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('neutral-50', platform),
      border: `1px solid ${designTokens.getColorValue('neutral-200', platform)}`,
      borderRadius: '12px',
      padding: '16px',
      overflow: 'auto',
      ...style
    };

    const headerStyles: React.CSSProperties = {
      marginBottom: '16px',
      textAlign: 'center' as const
    };

    const titleStyles: React.CSSProperties = {
      fontSize: '18px',
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      margin: '0 0 8px 0'
    };

    const subtitleStyles: React.CSSProperties = {
      fontSize: '14px',
      color: designTokens.getColorValue('neutral-600', platform),
      margin: 0
    };

    const tableStyles: React.CSSProperties = {
      width: '100%',
      borderCollapse: 'collapse' as const,
      fontSize: variant === 'compact' ? '12px' : '14px'
    };

    const headerCellStyles: React.CSSProperties = {
      padding: '8px 4px',
      borderBottom: `1px solid ${designTokens.getColorValue('neutral-300', platform)}`,
      backgroundColor: designTokens.getColorValue('neutral-100', platform),
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-700', platform),
      textAlign: 'center' as const,
      fontSize: '12px'
    };

    const cellStyles: React.CSSProperties = {
      padding: variant === 'compact' ? '4px 2px' : '8px 4px',
      border: `1px solid ${designTokens.getColorValue('neutral-200', platform)}`,
      textAlign: 'center' as const,
      minWidth: '60px',
      position: 'relative'
    };

    const currentPickStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('warning-yellow', platform) + '30',
      borderColor: designTokens.getColorValue('warning-yellow', platform),
      borderWidth: '2px'
    };

    const userTeamStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('primary-blue', platform) + '20',
      borderColor: designTokens.getColorValue('primary-blue', platform)
    };

    const pickedPlayerStyles: React.CSSProperties = {
      backgroundColor: designTokens.getColorValue('success-green', platform) + '10',
      cursor: onPickPress ? 'pointer' : 'default'
    };

    const playerNameStyles: React.CSSProperties = {
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      marginBottom: '2px'
    };

    const positionStyles: React.CSSProperties = {
      fontSize: '10px',
      color: designTokens.getColorValue('neutral-600', platform)
    };

    return (
      <div style={containerStyles}>
        <div style={headerStyles}>
          <h3 style={titleStyles}>Draft Board</h3>
          <p style={subtitleStyles}>Current Pick: {currentPick}</p>
        </div>

        <table style={tableStyles}>
          <thead>
            <tr>
              <th style={headerCellStyles}>Round</th>
              {teams.map(team => (
                <th key={team.id} style={headerCellStyles}>
                  <div style={{ fontSize: '10px', marginBottom: '2px' }}>
                    {team.name}
                  </div>
                  <div style={{ fontSize: '9px', opacity: 0.7 }}>
                    {team.owner}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: totalRounds }, (_, roundIndex) => {
              const round = roundIndex + 1;
              return (
                <tr key={round}>
                  <td style={{ ...cellStyles, ...headerCellStyles }}>{round}</td>
                  {teams.map(team => {
                    const pick = getPickForPosition(round, team.pick_order);
                    const isCurrent = isCurrentPick(round, team.pick_order);
                    const isUserTeam = team.is_user_team;

                    let cellStyle = { ...cellStyles };
                    if (isCurrent) cellStyle = { ...cellStyle, ...currentPickStyles };
                    if (isUserTeam) cellStyle = { ...cellStyle, ...userTeamStyles };
                    if (pick?.player_name) cellStyle = { ...cellStyle, ...pickedPlayerStyles };

                    const handleCellClick = () => {
                      if (pick && onPickPress) {
                        onPickPress(pick);
                      }
                    };

                    return (
                      <td
                        key={`${round}-${team.pick_order}`}
                        style={cellStyle}
                        onClick={pick?.player_name ? handleCellClick : undefined}
                      >
                        {pick?.player_name ? (
                          <div>
                            <div style={playerNameStyles}>
                              {pick.player_name.split(' ').map(name => name[0]).join('.')}
                            </div>
                            <div style={positionStyles}>{pick.player_position}</div>
                          </div>
                        ) : isCurrent ? (
                          <div style={{ fontSize: '12px', fontWeight: '600' }}>
                            ON CLOCK
                          </div>
                        ) : (
                          <div style={{ opacity: 0.3 }}>-</div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }

  // React Native implementation
  const StyleSheet = require('react-native').StyleSheet;
  const { View, Text, TouchableOpacity, ScrollView } = require('react-native');

  const styles = StyleSheet.create({
    container: {
      backgroundColor: designTokens.getColorValue('neutral-50', platform),
      borderWidth: 1,
      borderColor: designTokens.getColorValue('neutral-200', platform),
      borderRadius: 12,
      padding: 16,
      ...style
    },
    header: {
      marginBottom: 16,
      alignItems: 'center'
    },
    title: {
      fontSize: 18,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      marginBottom: 8
    },
    subtitle: {
      fontSize: 14,
      color: designTokens.getColorValue('neutral-600', platform)
    },
    tableHeader: {
      flexDirection: 'row',
      backgroundColor: designTokens.getColorValue('neutral-100', platform),
      borderBottomWidth: 1,
      borderBottomColor: designTokens.getColorValue('neutral-300', platform),
      paddingVertical: 8
    },
    headerCell: {
      flex: 1,
      alignItems: 'center',
      paddingHorizontal: 4
    },
    roundHeaderCell: {
      width: 50,
      alignItems: 'center',
      paddingHorizontal: 4
    },
    headerText: {
      fontSize: 12,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-700', platform),
      textAlign: 'center'
    },
    teamHeaderText: {
      fontSize: 10,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-700', platform),
      textAlign: 'center',
      marginBottom: 2
    },
    ownerText: {
      fontSize: 9,
      color: designTokens.getColorValue('neutral-600', platform),
      textAlign: 'center',
      opacity: 0.7
    },
    tableRow: {
      flexDirection: 'row',
      borderBottomWidth: 1,
      borderBottomColor: designTokens.getColorValue('neutral-200', platform)
    },
    cell: {
      flex: 1,
      minHeight: variant === 'compact' ? 40 : 50,
      justifyContent: 'center',
      alignItems: 'center',
      borderRightWidth: 1,
      borderRightColor: designTokens.getColorValue('neutral-200', platform),
      paddingHorizontal: 2
    },
    roundCell: {
      width: 50,
      minHeight: variant === 'compact' ? 40 : 50,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: designTokens.getColorValue('neutral-100', platform),
      borderRightWidth: 1,
      borderRightColor: designTokens.getColorValue('neutral-200', platform)
    },
    currentPickCell: {
      backgroundColor: designTokens.getColorValue('warning-yellow', platform) + '30',
      borderWidth: 2,
      borderColor: designTokens.getColorValue('warning-yellow', platform)
    },
    userTeamCell: {
      backgroundColor: designTokens.getColorValue('primary-blue', platform) + '20'
    },
    pickedCell: {
      backgroundColor: designTokens.getColorValue('success-green', platform) + '10'
    },
    playerName: {
      fontSize: variant === 'compact' ? 10 : 12,
      fontWeight: '600',
      color: designTokens.getColorValue('neutral-800', platform),
      textAlign: 'center',
      marginBottom: 2
    },
    playerPosition: {
      fontSize: 9,
      color: designTokens.getColorValue('neutral-600', platform),
      textAlign: 'center'
    },
    onClockText: {
      fontSize: 10,
      fontWeight: '600',
      color: designTokens.getColorValue('warning-yellow', platform),
      textAlign: 'center'
    },
    emptyText: {
      fontSize: 16,
      color: designTokens.getColorValue('neutral-300', platform),
      opacity: 0.3
    }
  });

  const renderCell = (round: number, team: DraftTeam) => {
    const pick = getPickForPosition(round, team.pick_order);
    const isCurrent = isCurrentPick(round, team.pick_order);
    const isUserTeam = team.is_user_team;

    let cellStyle = [styles.cell];
    if (isCurrent) cellStyle.push(styles.currentPickCell);
    if (isUserTeam) cellStyle.push(styles.userTeamCell);
    if (pick?.player_name) cellStyle.push(styles.pickedCell);

    const handlePress = () => {
      if (pick && onPickPress) {
        onPickPress(pick);
      }
    };

    const CellComponent = pick?.player_name && onPickPress ? TouchableOpacity : View;

    return (
      <CellComponent
        key={`${round}-${team.pick_order}`}
        style={cellStyle}
        onPress={pick?.player_name ? handlePress : undefined}
        activeOpacity={0.7}
      >
        {pick?.player_name ? (
          <View>
            <Text style={styles.playerName}>
              {pick.player_name.split(' ').map(name => name[0]).join('.')}
            </Text>
            <Text style={styles.playerPosition}>{pick.player_position}</Text>
          </View>
        ) : isCurrent ? (
          <Text style={styles.onClockText}>ON CLOCK</Text>
        ) : (
          <Text style={styles.emptyText}>-</Text>
        )}
      </CellComponent>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Draft Board</Text>
        <Text style={styles.subtitle}>Current Pick: {currentPick}</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View>
          {/* Header */}
          <View style={styles.tableHeader}>
            <View style={styles.roundHeaderCell}>
              <Text style={styles.headerText}>Round</Text>
            </View>
            {teams.map(team => (
              <View key={team.id} style={styles.headerCell}>
                <Text style={styles.teamHeaderText}>{team.name}</Text>
                <Text style={styles.ownerText}>{team.owner}</Text>
              </View>
            ))}
          </View>

          {/* Rows */}
          <ScrollView showsVerticalScrollIndicator={false}>
            {Array.from({ length: totalRounds }, (_, roundIndex) => {
              const round = roundIndex + 1;
              return (
                <View key={round} style={styles.tableRow}>
                  <View style={styles.roundCell}>
                    <Text style={styles.headerText}>{round}</Text>
                  </View>
                  {teams.map(team => renderCell(round, team))}
                </View>
              );
            })}
          </ScrollView>
        </View>
      </ScrollView>
    </View>
  );
};

// Web-specific wrapper
export const WebDraftBoard: React.FC<DraftBoardProps> = (props) => {
  return <DraftBoard {...props} platform="web" />;
};

// Mobile-specific wrapper
export const MobileDraftBoard: React.FC<DraftBoardProps> = (props) => {
  return <DraftBoard {...props} platform="mobile" />;
};

export default DraftBoard;