import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  Vibration,
  Dimensions,
  Animated,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  rank: number;
  projected_points: number;
}

interface DraftPick {
  pickNo: number;
  player: Player;
  teamId: string;
  timestamp: number;
}

const { width } = Dimensions.get('window');

// Mock players for demo
const MOCK_PLAYERS: Player[] = [
  { id: 'p1', name: 'LeBron James', position: 'SF', team: 'LAL', rank: 1, projected_points: 52.5 },
  { id: 'p2', name: 'Stephen Curry', position: 'PG', team: 'GSW', rank: 2, projected_points: 48.2 },
  { id: 'p3', name: 'Kevin Durant', position: 'PF', team: 'PHX', rank: 3, projected_points: 46.8 },
  { id: 'p4', name: 'Giannis Antetokounmpo', position: 'PF', team: 'MIL', rank: 4, projected_points: 55.1 },
  { id: 'p5', name: 'Luka Dončić', position: 'PG', team: 'DAL', rank: 5, projected_points: 50.3 },
  { id: 'p6', name: 'Jayson Tatum', position: 'SF', team: 'BOS', rank: 6, projected_points: 45.7 },
  { id: 'p7', name: 'Nikola Jokić', position: 'C', team: 'DEN', rank: 7, projected_points: 52.8 },
  { id: 'p8', name: 'Joel Embiid', position: 'C', team: 'PHI', rank: 8, projected_points: 49.4 },
];

export default function DraftScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { leagueId } = route.params as { leagueId: string };

  const [players, setPlayers] = useState<Player[]>(MOCK_PLAYERS);
  const [draftPicks, setDraftPicks] = useState<DraftPick[]>([]);
  const [currentPick, setCurrentPick] = useState(1);
  const [timeRemaining, setTimeRemaining] = useState(90); // 90 seconds per pick
  const [isMyTurn, setIsMyTurn] = useState(true);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  // Animations
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  // Timer effect
  useEffect(() => {
    if (timeRemaining > 0 && isMyTurn) {
      const timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeRemaining === 0 && isMyTurn) {
      // Auto-draft best available player
      autoDraft();
    }
  }, [timeRemaining, isMyTurn]);

  const autoDraft = () => {
    const availablePlayers = players.filter(p =>
      !draftPicks.some(pick => pick.player.id === p.id)
    );

    if (availablePlayers.length > 0) {
      const bestPlayer = availablePlayers[0]; // First available is highest ranked
      draftPlayer(bestPlayer, true);
    }
  };

  const draftPlayer = async (player: Player, isAutoDraft = false) => {
    // Haptic feedback
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    const newPick: DraftPick = {
      pickNo: currentPick,
      player,
      teamId: isMyTurn ? 'my-team' : `team-${currentPick % 4}`,
      timestamp: Date.now(),
    };

    setDraftPicks(prev => [...prev, newPick]);
    setCurrentPick(prev => prev + 1);
    setTimeRemaining(90);
    setIsMyTurn(!isMyTurn); // Toggle turn for demo
    setSelectedPlayer(null);

    // Animate the pick
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 1.2,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();

    Alert.alert(
      isAutoDraft ? 'Auto-Drafted!' : 'Player Drafted!',
      `${player.name} has been selected with pick #${currentPick}`,
      [{ text: 'OK' }]
    );
  };

  const handlePlayerSelect = (player: Player) => {
    if (!isMyTurn) {
      Alert.alert('Not Your Turn', 'Please wait for your turn to draft.');
      return;
    }

    const isAlreadyDrafted = draftPicks.some(pick => pick.player.id === player.id);
    if (isAlreadyDrafted) {
      Alert.alert('Already Drafted', 'This player has already been selected.');
      return;
    }

    setSelectedPlayer(player);

    Alert.alert(
      'Confirm Draft Pick',
      `Draft ${player.name} (${player.position} - ${player.team}) with pick #${currentPick}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Draft', onPress: () => draftPlayer(player) },
      ]
    );
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderPlayer = ({ item: player }: { item: Player }) => {
    const isAlreadyDrafted = draftPicks.some(pick => pick.player.id === player.id);
    const isSelected = selectedPlayer?.id === player.id;

    return (
      <TouchableOpacity
        style={[
          styles.playerCard,
          isAlreadyDrafted && styles.playerCardDrafted,
          isSelected && styles.playerCardSelected,
        ]}
        onPress={() => handlePlayerSelect(player)}
        disabled={isAlreadyDrafted}
      >
        <View style={styles.playerInfo}>
          <Text style={[styles.playerName, isAlreadyDrafted && styles.draftedText]}>
            {player.name}
          </Text>
          <Text style={[styles.playerDetails, isAlreadyDrafted && styles.draftedText]}>
            {player.position} • {player.team} • Rank #{player.rank}
          </Text>
          <Text style={[styles.playerProjection, isAlreadyDrafted && styles.draftedText]}>
            Proj: {player.projected_points} pts
          </Text>
        </View>
        {isAlreadyDrafted && (
          <View style={styles.draftedBadge}>
            <Text style={styles.draftedBadgeText}>DRAFTED</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderDraftPick = ({ item: pick }: { item: DraftPick }) => (
    <View style={styles.pickCard}>
      <Text style={styles.pickNumber}>#{pick.pickNo}</Text>
      <View style={styles.pickInfo}>
        <Text style={styles.pickPlayerName}>{pick.player.name}</Text>
        <Text style={styles.pickPlayerDetails}>
          {pick.player.position} • {pick.player.team}
        </Text>
      </View>
      <Text style={styles.pickTeam}>
        {pick.teamId === 'my-team' ? 'YOU' : 'OPP'}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Draft Status Header */}
      <View style={styles.header}>
        <View style={styles.pickInfo}>
          <Text style={styles.currentPickText}>Pick #{currentPick}</Text>
          <Text style={[styles.turnText, isMyTurn && styles.myTurnText]}>
            {isMyTurn ? 'YOUR TURN' : 'WAITING...'}
          </Text>
        </View>
        <Animated.View style={[styles.timerContainer, { transform: [{ scale: scaleAnim }] }]}>
          <Text style={[styles.timerText, timeRemaining <= 10 && styles.timerUrgent]}>
            {formatTime(timeRemaining)}
          </Text>
        </Animated.View>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {/* Draft Board */}
        <View style={styles.draftBoard}>
          <Text style={styles.sectionTitle}>Recent Picks</Text>
          <FlatList
            data={draftPicks.slice(-3).reverse()}
            renderItem={renderDraftPick}
            keyExtractor={(item) => item.pickNo.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.picksList}
          />
        </View>

        {/* Available Players */}
        <View style={styles.playersSection}>
          <Text style={styles.sectionTitle}>Available Players</Text>
          <FlatList
            data={players}
            renderItem={renderPlayer}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.playersList}
          />
        </View>
      </View>

      {/* Draft Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.controlButton, styles.autoDraftButton]}
          onPress={autoDraft}
          disabled={!isMyTurn}
        >
          <Ionicons name="flash" size={20} color="#fff" />
          <Text style={styles.controlButtonText}>Auto Draft</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.controlButton, styles.exitButton]}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="exit" size={20} color="#fff" />
          <Text style={styles.controlButtonText}>Exit Draft</Text>
        </TouchableOpacity>
      </View>
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
    padding: 16,
    backgroundColor: '#2563eb',
  },
  pickInfo: {
    alignItems: 'flex-start',
  },
  currentPickText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  turnText: {
    color: '#bfdbfe',
    fontSize: 14,
    marginTop: 2,
  },
  myTurnText: {
    color: '#fbbf24',
    fontWeight: 'bold',
  },
  timerContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  timerText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  timerUrgent: {
    color: '#ef4444',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  draftBoard: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 12,
  },
  picksList: {
    paddingHorizontal: 4,
  },
  pickCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginHorizontal: 4,
    minWidth: 140,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  pickNumber: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#2563eb',
    marginBottom: 4,
  },
  pickPlayerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  pickPlayerDetails: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  pickTeam: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#059669',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  playersSection: {
    flex: 1,
  },
  playersList: {
    paddingBottom: 20,
  },
  playerCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    position: 'relative',
  },
  playerCardDrafted: {
    backgroundColor: '#f1f5f9',
    opacity: 0.6,
  },
  playerCardSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  playerDetails: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  playerProjection: {
    fontSize: 12,
    color: '#059669',
    marginTop: 4,
    fontWeight: '500',
  },
  draftedText: {
    color: '#94a3b8',
  },
  draftedBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#ef4444',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  draftedBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  controls: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  controlButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  autoDraftButton: {
    backgroundColor: '#059669',
  },
  exitButton: {
    backgroundColor: '#ef4444',
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});