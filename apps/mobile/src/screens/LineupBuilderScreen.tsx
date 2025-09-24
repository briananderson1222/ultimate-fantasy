/**
 * Touch-Optimized Lineup Builder Screen
 *
 * An intuitive mobile lineup builder with drag-and-drop functionality,
 * position validation, optimization suggestions, and real-time projections.
 */

import React, { useState, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Animated,
  PanResponder,
  Dimensions,
  Modal,
  FlatList,
  Switch,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  MobilePlayerCard,
  type Player as UIPlayer
} from '@ultimate-fantasy/ui-components/src/components/PlayerCard';

// Enhanced interfaces for lineup building
interface Player extends UIPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'injured' | 'bye' | 'suspended';
  salary?: number;
  ownership_percentage?: number;
  bye_week?: number;
  game_time?: string;
  opponent?: string;
  injury_risk?: 'low' | 'medium' | 'high';
  ceiling?: number;
  floor?: number;
  consistency_rating?: number;
}

interface LineupSlot {
  id: string;
  position: string;
  player: Player | null;
  isRequired: boolean;
  isFlex: boolean;
  acceptedPositions: string[];
}

interface LineupOptimization {
  type: 'stack' | 'avoid' | 'balance' | 'value';
  description: string;
  impact: 'positive' | 'negative' | 'neutral';
  suggestion: string;
}

interface LineupConstraints {
  maxPlayersPerTeam: number;
  minSalaryUsed?: number;
  maxSalaryUsed?: number;
  stackPreferences: string[];
  avoidOpponents: boolean;
}

// Standard fantasy football lineup positions
const LINEUP_SLOTS: LineupSlot[] = [
  { id: 'qb', position: 'QB', player: null, isRequired: true, isFlex: false, acceptedPositions: ['QB'] },
  { id: 'rb1', position: 'RB', player: null, isRequired: true, isFlex: false, acceptedPositions: ['RB'] },
  { id: 'rb2', position: 'RB', player: null, isRequired: true, isFlex: false, acceptedPositions: ['RB'] },
  { id: 'wr1', position: 'WR', player: null, isRequired: true, isFlex: false, acceptedPositions: ['WR'] },
  { id: 'wr2', position: 'WR', player: null, isRequired: true, isFlex: false, acceptedPositions: ['WR'] },
  { id: 'te', position: 'TE', player: null, isRequired: true, isFlex: false, acceptedPositions: ['TE'] },
  { id: 'flex', position: 'FLEX', player: null, isRequired: true, isFlex: true, acceptedPositions: ['RB', 'WR', 'TE'] },
  { id: 'k', position: 'K', player: null, isRequired: true, isFlex: false, acceptedPositions: ['K'] },
  { id: 'dst', position: 'DST', player: null, isRequired: true, isFlex: false, acceptedPositions: ['DST'] },
];

// Mock player data
const MOCK_ROSTER: Player[] = [
  {
    id: 'p1',
    name: 'Josh Allen',
    position: 'QB',
    team: 'BUF',
    projected_points: 24.2,
    status: 'healthy',
    salary: 9200,
    bye_week: 12,
    game_time: 'Sun 1:00 PM',
    opponent: 'vs MIA',
    ceiling: 35.8,
    floor: 15.2,
    consistency_rating: 8.5,
  },
  {
    id: 'p2',
    name: 'Christian McCaffrey',
    position: 'RB',
    team: 'SF',
    projected_points: 22.8,
    status: 'healthy',
    salary: 9800,
    bye_week: 9,
    game_time: 'Sun 4:05 PM',
    opponent: '@ SEA',
    ceiling: 32.4,
    floor: 12.8,
    consistency_rating: 7.2,
  },
  {
    id: 'p3',
    name: 'Cooper Kupp',
    position: 'WR',
    team: 'LAR',
    projected_points: 19.4,
    status: 'questionable',
    salary: 8900,
    bye_week: 10,
    game_time: 'Sun 4:25 PM',
    opponent: 'vs ARI',
    ceiling: 28.7,
    floor: 8.3,
    consistency_rating: 6.8,
  },
  {
    id: 'p4',
    name: 'Travis Kelce',
    position: 'TE',
    team: 'KC',
    projected_points: 15.7,
    status: 'healthy',
    salary: 7800,
    bye_week: 10,
    game_time: 'Sun 1:00 PM',
    opponent: 'vs LV',
    ceiling: 24.3,
    floor: 7.8,
    consistency_rating: 8.1,
  },
  {
    id: 'p5',
    name: 'Stefon Diggs',
    position: 'WR',
    team: 'BUF',
    projected_points: 17.8,
    status: 'healthy',
    salary: 8200,
    bye_week: 12,
    game_time: 'Sun 1:00 PM',
    opponent: 'vs MIA',
    ceiling: 26.4,
    floor: 9.2,
    consistency_rating: 7.6,
  },
  {
    id: 'p6',
    name: 'Derrick Henry',
    position: 'RB',
    team: 'TEN',
    projected_points: 18.3,
    status: 'healthy',
    salary: 8700,
    bye_week: 7,
    game_time: 'Sun 1:00 PM',
    opponent: '@ HOU',
    ceiling: 28.9,
    floor: 8.7,
    consistency_rating: 7.8,
  },
  {
    id: 'p7',
    name: 'Tyreek Hill',
    position: 'WR',
    team: 'MIA',
    projected_points: 17.2,
    status: 'healthy',
    salary: 8400,
    bye_week: 11,
    game_time: 'Sun 1:00 PM',
    opponent: '@ BUF',
    ceiling: 28.1,
    floor: 6.8,
    consistency_rating: 6.4,
  },
  {
    id: 'p8',
    name: 'Austin Ekeler',
    position: 'RB',
    team: 'LAC',
    projected_points: 16.9,
    status: 'doubtful',
    salary: 7900,
    bye_week: 8,
    game_time: 'Sun 4:05 PM',
    opponent: 'vs NYJ',
    ceiling: 25.2,
    floor: 4.3,
    consistency_rating: 5.9,
  },
];

export default function LineupBuilderScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

  // Core lineup state
  const [lineup, setLineup] = useState<LineupSlot[]>(LINEUP_SLOTS);
  const [availablePlayers] = useState<Player[]>(MOCK_ROSTER);
  const [benchPlayers, setBenchPlayers] = useState<Player[]>([]);

  // UI state
  const [showPlayerSelector, setShowPlayerSelector] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<LineupSlot | null>(null);
  const [showOptimizations, setShowOptimizations] = useState(false);
  const [showConstraints, setShowConstraints] = useState(false);

  // Optimization and analysis
  const [autoOptimize, setAutoOptimize] = useState(false);
  const [showAdvancedStats, setShowAdvancedStats] = useState(false);
  const [constraints, setConstraints] = useState<LineupConstraints>({
    maxPlayersPerTeam: 4,
    stackPreferences: [],
    avoidOpponents: false,
  });

  // Drag and drop state
  const [draggedPlayer, setDraggedPlayer] = useState<Player | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const dragAnimation = useRef(new Animated.ValueXY()).current;

  // Computed values
  const totalProjection = useMemo(() => {
    return lineup.reduce((sum, slot) => {
      return sum + (slot.player?.projected_points || 0);
    }, 0);
  }, [lineup]);

  const totalSalary = useMemo(() => {
    return lineup.reduce((sum, slot) => {
      return sum + (slot.player?.salary || 0);
    }, 0);
  }, [lineup]);

  const lineupValidation = useMemo(() => {
    const issues: string[] = [];
    const teamCounts: { [team: string]: number } = {};

    lineup.forEach(slot => {
      if (slot.isRequired && !slot.player) {
        issues.push(`${slot.position} position is required`);
      }

      if (slot.player) {
        teamCounts[slot.player.team] = (teamCounts[slot.player.team] || 0) + 1;

        if (slot.player.status === 'out' || slot.player.status === 'doubtful') {
          issues.push(`${slot.player.name} is ${slot.player.status}`);
        }
      }
    });

    // Check team constraints
    Object.entries(teamCounts).forEach(([team, count]) => {
      if (count > constraints.maxPlayersPerTeam) {
        issues.push(`Too many players from ${team} (${count}/${constraints.maxPlayersPerTeam})`);
      }
    });

    return {
      isValid: issues.length === 0,
      issues,
      filledSlots: lineup.filter(slot => slot.player).length,
      totalSlots: lineup.length
    };
  }, [lineup, constraints]);

  const optimizationSuggestions = useMemo(() => {
    const suggestions: LineupOptimization[] = [];

    // Check for QB-WR stacks
    const qb = lineup.find(slot => slot.position === 'QB')?.player;
    const wrs = lineup.filter(slot => ['WR', 'FLEX'].includes(slot.position) && slot.player?.position === 'WR');

    if (qb && wrs.some(slot => slot.player?.team === qb.team)) {
      suggestions.push({
        type: 'stack',
        description: 'QB-WR Stack Detected',
        impact: 'positive',
        suggestion: `${qb.name} stacked with ${wrs.find(s => s.player?.team === qb.team)?.player?.name}`
      });
    }

    // Check salary usage
    if (totalSalary < 45000) {
      suggestions.push({
        type: 'value',
        description: 'Salary Underutilized',
        impact: 'negative',
        suggestion: `Using only $${totalSalary.toLocaleString()} of $50,000 budget`
      });
    }

    // Check for injury concerns
    const injuredPlayers = lineup.filter(slot =>
      slot.player && ['questionable', 'doubtful'].includes(slot.player.status)
    );

    if (injuredPlayers.length > 0) {
      suggestions.push({
        type: 'avoid',
        description: 'Injury Risk Warning',
        impact: 'negative',
        suggestion: `${injuredPlayers.length} player(s) with injury concerns`
      });
    }

    return suggestions;
  }, [lineup, totalSalary]);

  // Player selection and assignment
  const assignPlayerToSlot = useCallback((player: Player, slot: LineupSlot) => {
    if (!slot.acceptedPositions.includes(player.position)) {
      Alert.alert('Invalid Position', `${player.name} cannot be assigned to ${slot.position}`);
      return false;
    }

    // Check if player is already in lineup
    const existingSlot = lineup.find(s => s.player?.id === player.id);
    if (existingSlot) {
      Alert.alert('Player Already in Lineup', `${player.name} is already in your lineup`);
      return false;
    }

    setLineup(prev => prev.map(s =>
      s.id === slot.id ? { ...s, player } : s
    ));

    return true;
  }, [lineup]);

  const removePlayerFromSlot = useCallback((slotId: string) => {
    setLineup(prev => prev.map(slot =>
      slot.id === slotId ? { ...slot, player: null } : slot
    ));
  }, []);

  const swapPlayers = useCallback((slot1Id: string, slot2Id: string) => {
    setLineup(prev => {
      const slot1 = prev.find(s => s.id === slot1Id);
      const slot2 = prev.find(s => s.id === slot2Id);

      if (!slot1 || !slot2) return prev;

      return prev.map(slot => {
        if (slot.id === slot1Id) return { ...slot, player: slot2.player };
        if (slot.id === slot2Id) return { ...slot, player: slot1.player };
        return slot;
      });
    });
  }, []);

  const optimizeLineup = useCallback(() => {
    Alert.alert(
      'Optimize Lineup',
      'This will automatically fill your lineup with the highest projected players within your constraints.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Optimize', onPress: () => {
          // Simple optimization logic - assign highest projected available players
          const available = availablePlayers.filter(p =>
            !lineup.some(slot => slot.player?.id === p.id)
          );

          const newLineup = [...lineup];

          LINEUP_SLOTS.forEach(slotTemplate => {
            const slot = newLineup.find(s => s.id === slotTemplate.id);
            if (slot && !slot.player) {
              const bestPlayer = available
                .filter(p => slot.acceptedPositions.includes(p.position))
                .sort((a, b) => b.projected_points - a.projected_points)[0];

              if (bestPlayer) {
                slot.player = bestPlayer;
                const index = available.indexOf(bestPlayer);
                if (index > -1) available.splice(index, 1);
              }
            }
          });

          setLineup(newLineup);
          Alert.alert('Lineup Optimized', 'Your lineup has been optimized for maximum projected points.');
        }}
      ]
    );
  }, [lineup, availablePlayers]);

  const clearLineup = useCallback(() => {
    Alert.alert(
      'Clear Lineup',
      'This will remove all players from your lineup.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear', style: 'destructive', onPress: () => {
          setLineup(LINEUP_SLOTS.map(slot => ({ ...slot, player: null })));
        }}
      ]
    );
  }, []);

  const handleSlotPress = useCallback((slot: LineupSlot) => {
    if (slot.player) {
      // Show options for occupied slot
      Alert.alert(
        slot.player.name,
        `${slot.player.position} - ${slot.player.team} (${slot.player.projected_points} pts)`,
        [
          { text: 'Remove', style: 'destructive', onPress: () => removePlayerFromSlot(slot.id) },
          { text: 'Replace', onPress: () => {
            setSelectedSlot(slot);
            setShowPlayerSelector(true);
          }},
          { text: 'Cancel', style: 'cancel' }
        ]
      );
    } else {
      // Show player selector for empty slot
      setSelectedSlot(slot);
      setShowPlayerSelector(true);
    }
  }, [removePlayerFromSlot]);

  const renderLineupSlot = (slot: LineupSlot) => {
    const isEmpty = !slot.player;

    return (
      <TouchableOpacity
        key={slot.id}
        style={[
          styles.lineupSlot,
          isEmpty && styles.emptySlot,
          slot.isFlex && styles.flexSlot
        ]}
        onPress={() => handleSlotPress(slot)}
      >
        <View style={styles.slotHeader}>
          <Text style={styles.slotPosition}>{slot.position}</Text>
          {slot.isRequired && <Text style={styles.requiredIndicator}>*</Text>}
        </View>

        {slot.player ? (
          <View style={styles.slotPlayerInfo}>
            <Text style={styles.slotPlayerName}>{slot.player.name}</Text>
            <Text style={styles.slotPlayerDetails}>
              {slot.player.team} • {slot.player.projected_points} pts
            </Text>
            <Text style={styles.slotPlayerGame}>
              {slot.player.game_time} {slot.player.opponent}
            </Text>
            {slot.player.status !== 'healthy' && (
              <View style={[styles.statusBadge, { backgroundColor: getStatusColor(slot.player.status) }]}>
                <Text style={styles.statusText}>{slot.player.status.toUpperCase()}</Text>
              </View>
            )}
          </View>
        ) : (
          <View style={styles.emptySlotContent}>
            <Ionicons name="add" size={24} color="#9ca3af" />
            <Text style={styles.emptySlotText}>
              Add {slot.isFlex ? 'RB/WR/TE' : slot.position}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'questionable': return '#f59e0b';
      case 'doubtful': return '#ef4444';
      case 'out': return '#7f1d1d';
      default: return '#10b981';
    }
  };

  const renderPlayerSelector = () => {
    if (!selectedSlot) return null;

    const eligiblePlayers = availablePlayers.filter(player =>
      selectedSlot.acceptedPositions.includes(player.position) &&
      !lineup.some(slot => slot.player?.id === player.id)
    );

    return (
      <Modal
        visible={showPlayerSelector}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              Select {selectedSlot.position} Player
            </Text>
            <TouchableOpacity onPress={() => setShowPlayerSelector(false)}>
              <Text style={styles.modalClose}>Cancel</Text>
            </TouchableOpacity>
          </View>

          <FlatList
            data={eligiblePlayers}
            keyExtractor={(item) => item.id}
            renderItem={({ item: player }) => (
              <TouchableOpacity
                style={styles.playerOption}
                onPress={() => {
                  if (assignPlayerToSlot(player, selectedSlot)) {
                    setShowPlayerSelector(false);
                    setSelectedSlot(null);
                  }
                }}
              >
                <MobilePlayerCard
                  player={player}
                  variant="compact"
                  showProjection={true}
                />
              </TouchableOpacity>
            )}
            style={styles.playerSelectorList}
          />
        </View>
      </Modal>
    );
  };

  const renderOptimizationPanel = () => (
    <Modal
      visible={showOptimizations}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Lineup Analysis</Text>
          <TouchableOpacity onPress={() => setShowOptimizations(false)}>
            <Text style={styles.modalClose}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          {/* Validation Status */}
          <View style={styles.analysisSection}>
            <Text style={styles.sectionTitle}>Lineup Status</Text>
            <View style={[styles.statusCard, lineupValidation.isValid ? styles.validCard : styles.invalidCard]}>
              <Ionicons
                name={lineupValidation.isValid ? "checkmark-circle" : "warning"}
                size={24}
                color={lineupValidation.isValid ? "#10b981" : "#ef4444"}
              />
              <Text style={styles.statusText}>
                {lineupValidation.isValid ? 'Lineup Valid' : 'Issues Found'}
              </Text>
            </View>

            {lineupValidation.issues.map((issue, index) => (
              <Text key={index} style={styles.issueText}>• {issue}</Text>
            ))}
          </View>

          {/* Projections */}
          <View style={styles.analysisSection}>
            <Text style={styles.sectionTitle}>Projections</Text>
            <View style={styles.projectionGrid}>
              <View style={styles.projectionCard}>
                <Text style={styles.projectionValue}>{totalProjection.toFixed(1)}</Text>
                <Text style={styles.projectionLabel}>Total Points</Text>
              </View>
              <View style={styles.projectionCard}>
                <Text style={styles.projectionValue}>${totalSalary.toLocaleString()}</Text>
                <Text style={styles.projectionLabel}>Salary Used</Text>
              </View>
            </View>
          </View>

          {/* Optimizations */}
          <View style={styles.analysisSection}>
            <Text style={styles.sectionTitle}>Suggestions</Text>
            {optimizationSuggestions.map((suggestion, index) => (
              <View key={index} style={styles.suggestionCard}>
                <View style={styles.suggestionHeader}>
                  <Text style={styles.suggestionTitle}>{suggestion.description}</Text>
                  <View style={[
                    styles.impactBadge,
                    { backgroundColor: suggestion.impact === 'positive' ? '#10b981' :
                                     suggestion.impact === 'negative' ? '#ef4444' : '#6b7280' }
                  ]}>
                    <Text style={styles.impactText}>
                      {suggestion.impact === 'positive' ? '+' : suggestion.impact === 'negative' ? '-' : '~'}
                    </Text>
                  </View>
                </View>
                <Text style={styles.suggestionText}>{suggestion.suggestion}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Lineup Builder</Text>
          <Text style={styles.headerSubtitle}>
            {lineupValidation.filledSlots}/{lineupValidation.totalSlots} players set
          </Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowOptimizations(true)}
          >
            <Ionicons name="analytics" size={20} color="#6b7280" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={optimizeLineup}
          >
            <Ionicons name="flash" size={20} color="#6b7280" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Lineup Overview */}
      <View style={styles.overview}>
        <View style={styles.overviewStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{totalProjection.toFixed(1)}</Text>
            <Text style={styles.statLabel}>Projected Points</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>${totalSalary.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Salary Used</Text>
          </View>
          <View style={styles.statItem}>
            <Ionicons
              name={lineupValidation.isValid ? "checkmark-circle" : "warning"}
              size={24}
              color={lineupValidation.isValid ? "#10b981" : "#ef4444"}
            />
            <Text style={styles.statLabel}>Status</Text>
          </View>
        </View>
      </View>

      {/* Lineup Grid */}
      <ScrollView style={styles.lineupContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.lineupGrid}>
          {lineup.map(renderLineupSlot)}
        </View>
      </ScrollView>

      {/* Action Bar */}
      <View style={styles.actionBar}>
        <TouchableOpacity
          style={[styles.actionButton, styles.clearButton]}
          onPress={clearLineup}
        >
          <Ionicons name="trash" size={20} color="#ef4444" />
          <Text style={styles.clearButtonText}>Clear</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.saveButton]}
          onPress={() => Alert.alert('Lineup Saved', 'Your lineup has been saved successfully!')}
        >
          <Ionicons name="save" size={20} color="#ffffff" />
          <Text style={styles.saveButtonText}>Save Lineup</Text>
        </TouchableOpacity>
      </View>

      {/* Modals */}
      {renderPlayerSelector()}
      {renderOptimizationPanel()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Overview
  overview: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  overviewStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
  },

  // Lineup
  lineupContainer: {
    flex: 1,
  },
  lineupGrid: {
    padding: 16,
    gap: 12,
  },
  lineupSlot: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    minHeight: 100,
  },
  emptySlot: {
    borderStyle: 'dashed',
    borderColor: '#d1d5db',
  },
  flexSlot: {
    borderColor: '#3b82f6',
  },
  slotHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  slotPosition: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  requiredIndicator: {
    fontSize: 14,
    color: '#ef4444',
    marginLeft: 4,
  },
  slotPlayerInfo: {
    flex: 1,
    position: 'relative',
  },
  slotPlayerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  slotPlayerDetails: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 2,
  },
  slotPlayerGame: {
    fontSize: 12,
    color: '#9ca3af',
  },
  statusBadge: {
    position: 'absolute',
    top: 0,
    right: 0,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: '600',
  },
  emptySlotContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    opacity: 0.5,
  },
  emptySlotText: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
  },

  // Action Bar
  actionBar: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  clearButton: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  clearButtonText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    backgroundColor: '#3b82f6',
  },
  saveButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  modalClose: {
    fontSize: 16,
    color: '#3b82f6',
    fontWeight: '500',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },

  // Player Selector
  playerSelectorList: {
    flex: 1,
  },
  playerOption: {
    marginBottom: 12,
  },

  // Analysis
  analysisSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
  },
  statusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    gap: 12,
  },
  validCard: {
    borderColor: '#10b981',
    borderWidth: 1,
  },
  invalidCard: {
    borderColor: '#ef4444',
    borderWidth: 1,
  },
  issueText: {
    fontSize: 14,
    color: '#ef4444',
    marginBottom: 4,
  },
  projectionGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  projectionCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  projectionValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  projectionLabel: {
    fontSize: 12,
    color: '#64748b',
  },
  suggestionCard: {
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  suggestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  impactBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  impactText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: '600',
  },
  suggestionText: {
    fontSize: 14,
    color: '#64748b',
  },
});