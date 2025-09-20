import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Animated,
  PanGestureHandler,
  State,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  status: 'active' | 'injured' | 'bye';
}

interface LineupSlot {
  position: string;
  player: Player | null;
  isRequired: boolean;
}

// Mock players for demo
const MOCK_ROSTER: Player[] = [
  { id: 'p1', name: 'LeBron James', position: 'SF', team: 'LAL', projected_points: 52.5, status: 'active' },
  { id: 'p2', name: 'Stephen Curry', position: 'PG', team: 'GSW', projected_points: 48.2, status: 'active' },
  { id: 'p3', name: 'Kevin Durant', position: 'PF', team: 'PHX', projected_points: 46.8, status: 'injured' },
  { id: 'p4', name: 'Jayson Tatum', position: 'SF', team: 'BOS', projected_points: 45.7, status: 'active' },
  { id: 'p5', name: 'Damian Lillard', position: 'PG', team: 'MIL', projected_points: 44.3, status: 'active' },
  { id: 'p6', name: 'Anthony Davis', position: 'PF', team: 'LAL', projected_points: 48.9, status: 'bye' },
  { id: 'p7', name: 'Nikola Jokić', position: 'C', team: 'DEN', projected_points: 52.8, status: 'active' },
  { id: 'p8', name: 'Joel Embiid', position: 'C', team: 'PHI', projected_points: 49.4, status: 'active' },
];

const INITIAL_LINEUP: LineupSlot[] = [
  { position: 'PG', player: null, isRequired: true },
  { position: 'SG', player: null, isRequired: true },
  { position: 'SF', player: null, isRequired: true },
  { position: 'PF', player: null, isRequired: true },
  { position: 'C', player: null, isRequired: true },
  { position: 'UTIL', player: null, isRequired: true },
  { position: 'UTIL', player: null, isRequired: true },
  { position: 'BENCH', player: null, isRequired: false },
  { position: 'BENCH', player: null, isRequired: false },
];

export default function LineupScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { teamId } = route.params as { teamId: string };

  const [lineup, setLineup] = useState<LineupSlot[]>(INITIAL_LINEUP);
  const [bench, setBench] = useState<Player[]>(MOCK_ROSTER);
  const [draggedPlayer, setDraggedPlayer] = useState<Player | null>(null);
  const [totalProjectedPoints, setTotalProjectedPoints] = useState(0);

  // Animation values
  const dragAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    // Calculate total projected points
    const total = lineup.reduce((sum, slot) => {
      return sum + (slot.player?.projected_points || 0);
    }, 0);
    setTotalProjectedPoints(total);
  }, [lineup]);

  const canPlayerFitPosition = (player: Player, position: string): boolean => {
    if (position === 'BENCH' || position === 'UTIL') return true;
    return player.position === position;
  };

  const handlePlayerDrop = async (player: Player, slotIndex: number) => {
    const targetSlot = lineup[slotIndex];

    // Check if player can fit in this position
    if (!canPlayerFitPosition(player, targetSlot.position)) {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert('Invalid Position', `${player.name} cannot play ${targetSlot.position}`);
      return;
    }

    // Haptic feedback for successful drop
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    setLineup(prevLineup => {
      const newLineup = [...prevLineup];

      // If slot is occupied, move that player to bench
      if (targetSlot.player) {
        setBench(prevBench => [...prevBench, targetSlot.player!]);
      }

      // Place the new player in the slot
      newLineup[slotIndex] = { ...targetSlot, player };

      return newLineup;
    });

    // Remove player from bench
    setBench(prevBench => prevBench.filter(p => p.id !== player.id));

    // Animate the successful drop
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 1.1,
        duration: 150,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const removePlayerFromLineup = async (slotIndex: number) => {
    const slot = lineup[slotIndex];
    if (!slot.player) return;

    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    // Move player back to bench
    setBench(prevBench => [...prevBench, slot.player!]);

    // Clear the lineup slot
    setLineup(prevLineup => {
      const newLineup = [...prevLineup];
      newLineup[slotIndex] = { ...slot, player: null };
      return newLineup;
    });
  };

  const optimizeLineup = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);

    // Simple optimization: put highest projected players in starting spots
    const availablePlayers = [...bench];
    lineup.forEach(slot => {
      if (slot.player) availablePlayers.push(slot.player);
    });

    // Sort by projected points
    const sortedPlayers = availablePlayers.sort((a, b) => b.projected_points - a.projected_points);

    const newLineup = [...INITIAL_LINEUP];
    const remainingPlayers = [...sortedPlayers];

    // Fill required positions first
    newLineup.forEach((slot, index) => {
      if (slot.isRequired) {
        const playerIndex = remainingPlayers.findIndex(p =>
          canPlayerFitPosition(p, slot.position) && p.status === 'active'
        );
        if (playerIndex !== -1) {
          newLineup[index] = { ...slot, player: remainingPlayers[playerIndex] };
          remainingPlayers.splice(playerIndex, 1);
        }
      }
    });

    setLineup(newLineup);
    setBench(remainingPlayers);

    Alert.alert('Lineup Optimized', 'Your lineup has been optimized for maximum projected points!');
  };

  const saveLineup = async () => {
    // Check if all required positions are filled
    const unfilledRequired = lineup.filter(slot => slot.isRequired && !slot.player);
    if (unfilledRequired.length > 0) {
      Alert.alert('Incomplete Lineup', 'Please fill all required positions before saving.');
      return;
    }

    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Alert.alert('Lineup Saved', `Your lineup has been saved with ${totalProjectedPoints.toFixed(1)} projected points!`);
  };

  const getPlayerStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#059669';
      case 'injured': return '#ef4444';
      case 'bye': return '#f59e0b';
      default: return '#64748b';
    }
  };

  const getPlayerStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return 'checkmark-circle';
      case 'injured': return 'medical';
      case 'bye': return 'time';
      default: return 'help-circle';
    }
  };

  const renderLineupSlot = (slot: LineupSlot, index: number) => (
    <TouchableOpacity
      key={index}
      style={[
        styles.lineupSlot,
        slot.isRequired && styles.requiredSlot,
        !slot.player && styles.emptySlot,
      ]}
      onPress={() => slot.player && removePlayerFromLineup(index)}
    >
      <View style={styles.slotHeader}>
        <Text style={styles.slotPosition}>{slot.position}</Text>
        {slot.isRequired && <Text style={styles.requiredIndicator}>*</Text>}
      </View>

      {slot.player ? (
        <Animated.View style={[styles.slotPlayer, { transform: [{ scale: scaleAnim }] }]}>
          <View style={styles.playerInfo}>
            <Text style={styles.slotPlayerName}>{slot.player.name}</Text>
            <Text style={styles.slotPlayerTeam}>{slot.player.team}</Text>
            <Text style={styles.slotPlayerProjection}>
              {slot.player.projected_points} pts
            </Text>
          </View>
          <View style={styles.playerStatus}>
            <Ionicons
              name={getPlayerStatusIcon(slot.player.status)}
              size={16}
              color={getPlayerStatusColor(slot.player.status)}
            />
          </View>
        </Animated.View>
      ) : (
        <View style={styles.emptySlotContent}>
          <Ionicons name="person-add" size={24} color="#94a3b8" />
          <Text style={styles.emptySlotText}>Tap to add player</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderBenchPlayer = (player: Player) => (
    <TouchableOpacity
      key={player.id}
      style={styles.benchPlayer}
      onPress={() => {
        // Find first compatible empty slot
        const emptySlotIndex = lineup.findIndex(slot =>
          !slot.player && canPlayerFitPosition(player, slot.position)
        );

        if (emptySlotIndex !== -1) {
          handlePlayerDrop(player, emptySlotIndex);
        } else {
          Alert.alert('No Available Spots', 'No compatible positions available for this player.');
        }
      }}
    >
      <View style={styles.benchPlayerInfo}>
        <Text style={styles.benchPlayerName}>{player.name}</Text>
        <Text style={styles.benchPlayerDetails}>
          {player.position} • {player.team} • {player.projected_points} pts
        </Text>
      </View>
      <View style={styles.benchPlayerStatus}>
        <Ionicons
          name={getPlayerStatusIcon(player.status)}
          size={16}
          color={getPlayerStatusColor(player.status)}
        />
      </View>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header Stats */}
      <View style={styles.header}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{totalProjectedPoints.toFixed(1)}</Text>
          <Text style={styles.statLabel}>Projected Points</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {lineup.filter(slot => slot.player && slot.player.status === 'active').length}
          </Text>
          <Text style={styles.statLabel}>Active Players</Text>
        </View>
      </View>

      {/* Starting Lineup */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Starting Lineup</Text>
        <View style={styles.lineupGrid}>
          {lineup.filter(slot => slot.position !== 'BENCH').map(renderLineupSlot)}
        </View>
      </View>

      {/* Bench */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Bench</Text>
        <View style={styles.benchGrid}>
          {lineup.filter(slot => slot.position === 'BENCH').map(renderLineupSlot)}
        </View>
      </View>

      {/* Available Players */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Available Players</Text>
        <View style={styles.benchList}>
          {bench.map(renderBenchPlayer)}
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.optimizeButton} onPress={optimizeLineup}>
          <Ionicons name="flash" size={20} color="#fff" />
          <Text style={styles.buttonText}>Optimize</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.saveButton} onPress={saveLineup}>
          <Ionicons name="save" size={20} color="#fff" />
          <Text style={styles.buttonText}>Save Lineup</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  content: {
    padding: 16,
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 12,
  },
  lineupGrid: {
    gap: 8,
  },
  benchGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  lineupSlot: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#e2e8f0',
    minHeight: 80,
  },
  requiredSlot: {
    borderColor: '#2563eb',
    borderStyle: 'dashed',
  },
  emptySlot: {
    borderColor: '#cbd5e1',
    backgroundColor: '#f8fafc',
  },
  slotHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  slotPosition: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  requiredIndicator: {
    color: '#ef4444',
    marginLeft: 4,
  },
  slotPlayer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  playerInfo: {
    flex: 1,
  },
  slotPlayerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  slotPlayerTeam: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  slotPlayerProjection: {
    fontSize: 12,
    color: '#059669',
    marginTop: 2,
    fontWeight: '500',
  },
  playerStatus: {
    marginLeft: 8,
  },
  emptySlotContent: {
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.6,
  },
  emptySlotText: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
  },
  benchList: {
    gap: 8,
  },
  benchPlayer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  benchPlayerInfo: {
    flex: 1,
  },
  benchPlayerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  benchPlayerDetails: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  benchPlayerStatus: {
    marginLeft: 8,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  optimizeButton: {
    flex: 1,
    backgroundColor: '#f59e0b',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#059669',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});