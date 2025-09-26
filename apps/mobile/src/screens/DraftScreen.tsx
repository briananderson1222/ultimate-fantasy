/**
 * Enhanced Mobile Draft Screen
 *
 * A comprehensive mobile draft interface with real-time draft board,
 * advanced player filtering, draft queue management, and touch-optimized controls.
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  Animated,
  ScrollView,
  Dimensions,
  Modal,
  TextInput,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  MobileDraftBoard,
  type DraftPick as DraftBoardPick,
  type DraftTeam,
} from "@ultimate-fantasy/ui-components/src/components/DraftBoard";
import {
  MobilePlayerCard,
  type Player as UIPlayer,
} from "@ultimate-fantasy/ui-components/src/components/PlayerCard";

interface Player extends UIPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  rank: number;
  projected_points: number;
  status:
    | "healthy"
    | "questionable"
    | "doubtful"
    | "out"
    | "injured"
    | "bye"
    | "suspended";
  adp?: number;
  tier?: number;
  bye_week?: number;
}

interface DraftPick extends DraftBoardPick {
  pickNo: number;
  player: Player;
  teamId: string;
  timestamp: number;
  pick_number: number;
  round: number;
  team_id: string;
  team_name: string;
  player_id?: string;
  player_name?: string;
  player_position?: string;
}

interface DraftSettings {
  totalRounds: number;
  timePerPick: number;
  draftOrder: string[];
  snakeDraft: boolean;
}

interface PlayerFilter {
  position?: string;
  team?: string;
  searchTerm?: string;
  tier?: number;
  available?: boolean;
}

// Mock players for demo - Football players for fantasy sports
const MOCK_PLAYERS: Player[] = [
  {
    id: "p1",
    name: "Josh Allen",
    position: "QB",
    team: "BUF",
    rank: 1,
    projected_points: 24.2,
    status: "healthy",
    adp: 8.5,
    tier: 1,
    bye_week: 12,
  },
  {
    id: "p2",
    name: "Christian McCaffrey",
    position: "RB",
    team: "SF",
    rank: 2,
    projected_points: 22.8,
    status: "healthy",
    adp: 1.2,
    tier: 1,
    bye_week: 9,
  },
  {
    id: "p3",
    name: "Cooper Kupp",
    position: "WR",
    team: "LAR",
    rank: 3,
    projected_points: 19.4,
    status: "questionable",
    adp: 12.3,
    tier: 1,
    bye_week: 10,
  },
  {
    id: "p4",
    name: "Travis Kelce",
    position: "TE",
    team: "KC",
    rank: 4,
    projected_points: 15.7,
    status: "healthy",
    adp: 18.1,
    tier: 1,
    bye_week: 10,
  },
  {
    id: "p5",
    name: "Derrick Henry",
    position: "RB",
    team: "TEN",
    rank: 5,
    projected_points: 18.3,
    status: "healthy",
    adp: 15.7,
    tier: 2,
    bye_week: 7,
  },
  {
    id: "p6",
    name: "Stefon Diggs",
    position: "WR",
    team: "BUF",
    rank: 6,
    projected_points: 17.8,
    status: "healthy",
    adp: 14.2,
    tier: 2,
    bye_week: 12,
  },
  {
    id: "p7",
    name: "Patrick Mahomes",
    position: "QB",
    team: "KC",
    rank: 7,
    projected_points: 23.9,
    status: "healthy",
    adp: 22.4,
    tier: 1,
    bye_week: 10,
  },
  {
    id: "p8",
    name: "Tyreek Hill",
    position: "WR",
    team: "MIA",
    rank: 8,
    projected_points: 17.2,
    status: "healthy",
    adp: 16.8,
    tier: 2,
    bye_week: 11,
  },
  {
    id: "p9",
    name: "Austin Ekeler",
    position: "RB",
    team: "LAC",
    rank: 9,
    projected_points: 16.9,
    status: "doubtful",
    adp: 11.5,
    tier: 2,
    bye_week: 8,
  },
  {
    id: "p10",
    name: "Mark Andrews",
    position: "TE",
    team: "BAL",
    rank: 10,
    projected_points: 13.2,
    status: "healthy",
    adp: 28.3,
    tier: 2,
    bye_week: 14,
  },
];

const MOCK_TEAMS: DraftTeam[] = [
  {
    id: "team1",
    name: "Your Team",
    owner: "You",
    pick_order: 1,
    is_current_turn: true,
    is_user_team: true,
  },
  {
    id: "team2",
    name: "Rivals",
    owner: "Mike",
    pick_order: 2,
    is_current_turn: false,
    is_user_team: false,
  },
  {
    id: "team3",
    name: "Crushers",
    owner: "Sarah",
    pick_order: 3,
    is_current_turn: false,
    is_user_team: false,
  },
  {
    id: "team4",
    name: "Champions",
    owner: "Alex",
    pick_order: 4,
    is_current_turn: false,
    is_user_team: false,
  },
];

const POSITIONS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"];
const TEAMS = ["ALL", "BUF", "SF", "LAR", "KC", "TEN", "MIA", "LAC", "BAL"];
const TIERS = ["ALL", "1", "2", "3", "4", "5"];

export default function DraftScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = Dimensions.get("window");

  // Core draft state
  const [players] = useState<Player[]>(MOCK_PLAYERS);
  const [draftTeams, setDraftTeams] = useState<DraftTeam[]>(MOCK_TEAMS);
  const [draftPicks, setDraftPicks] = useState<DraftPick[]>([]);
  const [currentPick, setCurrentPick] = useState(1);
  const [timeRemaining, setTimeRemaining] = useState(90);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  // Enhanced features
  const [draftSettings] = useState<DraftSettings>({
    totalRounds: 16,
    timePerPick: 90,
    draftOrder: ["team1", "team2", "team3", "team4"],
    snakeDraft: true,
  });

  // UI state
  const [currentView, setCurrentView] = useState<"players" | "board" | "queue">(
    "players",
  );
  const [showFilters, setShowFilters] = useState(false);

  // Filtering and search
  const [filters, setFilters] = useState<PlayerFilter>({
    position: "ALL",
    team: "ALL",
    searchTerm: "",
    tier: undefined,
    available: true,
  });

  // Draft queue management
  const [draftQueue, setDraftQueue] = useState<Player[]>([]);
  const [watchlist, setWatchlist] = useState<Player[]>([]);

  // Animations
  const scaleAnim = useRef(new Animated.Value(1)).current;

  // Computed values
  const filteredPlayers = players.filter((player) => {
    const isAvailable = !draftPicks.some(
      (pick) => pick.player.id === player.id,
    );
    if (filters.available && !isAvailable) return false;

    if (
      filters.position &&
      filters.position !== "ALL" &&
      player.position !== filters.position
    )
      return false;
    if (filters.team && filters.team !== "ALL" && player.team !== filters.team)
      return false;
    if (filters.tier && player.tier !== filters.tier) return false;
    if (
      filters.searchTerm &&
      !player.name.toLowerCase().includes(filters.searchTerm.toLowerCase())
    )
      return false;

    return true;
  });

  const currentRound = Math.ceil(currentPick / draftTeams.length);
  const currentTeamIndex = (currentPick - 1) % draftTeams.length;
  const currentTeam = draftTeams[currentTeamIndex];
  const isMyTurn = currentTeam.is_user_team;

  // Convert draft picks to format expected by DraftBoard
  const boardPicks: DraftBoardPick[] = draftPicks.map((pick) => ({
    pick_number: pick.pickNo,
    round: Math.ceil(pick.pickNo / draftTeams.length),
    team_id: pick.teamId,
    team_name: draftTeams.find((t) => t.id === pick.teamId)?.name || "Unknown",
    player_id: pick.player.id,
    player_name: pick.player.name,
    player_position: pick.player.position,
    timestamp: new Date(pick.timestamp).toISOString(),
  }));

  const draftPlayer = useCallback(
    async (player: Player, isAutoDraft = false) => {
      const newPick: DraftPick = {
        pickNo: currentPick,
        player,
        teamId: currentTeam.id,
        timestamp: Date.now(),
        pick_number: currentPick,
        round: currentRound,
        team_id: currentTeam.id,
        team_name: currentTeam.name,
        player_id: player.id,
        player_name: player.name,
        player_position: player.position,
      };

      setDraftPicks((prev) => [...prev, newPick]);
      setCurrentPick((prev) => prev + 1);
      setTimeRemaining(draftSettings.timePerPick);
      setSelectedPlayer(null);

      // Update team turn
      const nextTeamIndex = currentPick % draftTeams.length;
      setDraftTeams((teams) =>
        teams.map((team, idx) => ({
          ...team,
          is_current_turn: idx === nextTeamIndex,
        })),
      );

      // Remove from queue if it was queued
      setDraftQueue((prev) => prev.filter((p) => p.id !== player.id));

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
        isAutoDraft ? "Auto-Drafted!" : "Player Drafted!",
        `${player.name} (${player.position}) has been selected by ${currentTeam.name} with pick #${currentPick}`,
        [{ text: "OK" }],
      );
    },
    [
      currentPick,
      currentTeam,
      currentRound,
      draftSettings.timePerPick,
      draftTeams.length,
      scaleAnim,
    ],
  );

  const autoDraft = useCallback(() => {
    // Use queue first, then best available
    let playerToDraft = draftQueue[0];

    if (!playerToDraft) {
      const availablePlayers = filteredPlayers.filter(
        (p) => !draftPicks.some((pick) => pick.player.id === p.id),
      );
      playerToDraft = availablePlayers[0]; // Highest ranked available
    }

    if (playerToDraft) {
      draftPlayer(playerToDraft, true);
    }
  }, [filteredPlayers, draftPicks, draftQueue, draftPlayer]);

  // Timer effect
  useEffect(() => {
    if (timeRemaining > 0 && isMyTurn) {
      const timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeRemaining === 0 && isMyTurn) {
      autoDraft();
    }
  }, [timeRemaining, isMyTurn, autoDraft]);

  const handlePlayerSelect = (player: Player) => {
    if (!isMyTurn) {
      Alert.alert("Not Your Turn", "Please wait for your turn to draft.");
      return;
    }

    const isAlreadyDrafted = draftPicks.some(
      (pick) => pick.player.id === player.id,
    );
    if (isAlreadyDrafted) {
      Alert.alert("Already Drafted", "This player has already been selected.");
      return;
    }

    setSelectedPlayer(player);

    Alert.alert(
      "Confirm Draft Pick",
      `Draft ${player.name} (${player.position} - ${player.team}) with pick #${currentPick}?`,
      [
        { text: "Cancel", style: "cancel" },
        { text: "Draft", onPress: () => draftPlayer(player) },
      ],
    );
  };

  const addToQueue = (player: Player) => {
    if (!draftQueue.find((p) => p.id === player.id)) {
      setDraftQueue((prev) => [...prev, player]);
      Alert.alert("Added to Queue", `${player.name} added to your draft queue`);
    }
  };

  const removeFromQueue = (player: Player) => {
    setDraftQueue((prev) => prev.filter((p) => p.id !== player.id));
  };

  const addToWatchlist = (player: Player) => {
    if (!watchlist.find((p) => p.id === player.id)) {
      setWatchlist((prev) => [...prev, player]);
      Alert.alert(
        "Added to Watchlist",
        `${player.name} added to your watchlist`,
      );
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const renderPlayer = ({ item: player }: { item: Player }) => {
    const isAlreadyDrafted = draftPicks.some(
      (pick) => pick.player.id === player.id,
    );
    const isSelected = selectedPlayer?.id === player.id;
    const isQueued = draftQueue.some((p) => p.id === player.id);

    return (
      <View style={styles.playerContainer}>
        <MobilePlayerCard
          player={player}
          variant="compact"
          selectable={!isAlreadyDrafted && isMyTurn}
          selected={isSelected}
          showProjection={true}
          onPress={() => handlePlayerSelect(player)}
          style={[
            isAlreadyDrafted && styles.playerCardDrafted,
            isQueued && styles.playerCardQueued,
          ]}
        />

        {!isAlreadyDrafted && (
          <View style={styles.playerActions}>
            <TouchableOpacity
              style={styles.queueButton}
              onPress={() =>
                isQueued ? removeFromQueue(player) : addToQueue(player)
              }
            >
              <Ionicons
                name={isQueued ? "checkmark-circle" : "add-circle-outline"}
                size={20}
                color={isQueued ? "#10b981" : "#6b7280"}
              />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.watchButton}
              onPress={() => addToWatchlist(player)}
            >
              <Ionicons name="eye-outline" size={20} color="#6b7280" />
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  const renderQueueItem = ({ item: player }: { item: Player }) => (
    <View style={styles.queueItem}>
      <View style={styles.queuePlayerInfo}>
        <Text style={styles.queuePlayerName}>{player.name}</Text>
        <Text style={styles.queuePlayerDetails}>
          {player.position} • {player.team} • {player.projected_points} pts
        </Text>
      </View>
      <TouchableOpacity
        style={styles.removeButton}
        onPress={() => removeFromQueue(player)}
      >
        <Ionicons name="close-circle" size={24} color="#ef4444" />
      </TouchableOpacity>
    </View>
  );

  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Filter Players</Text>
          <TouchableOpacity onPress={() => setShowFilters(false)}>
            <Text style={styles.modalClose}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          {/* Search */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Search</Text>
            <TextInput
              style={styles.searchInput}
              placeholder="Player name..."
              value={filters.searchTerm}
              onChangeText={(text) =>
                setFilters((prev) => ({ ...prev, searchTerm: text }))
              }
            />
          </View>

          {/* Position Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Position</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {POSITIONS.map((pos) => (
                <TouchableOpacity
                  key={pos}
                  style={[
                    styles.filterChip,
                    filters.position === pos && styles.filterChipActive,
                  ]}
                  onPress={() =>
                    setFilters((prev) => ({ ...prev, position: pos }))
                  }
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      filters.position === pos && styles.filterChipTextActive,
                    ]}
                  >
                    {pos}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Team Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Team</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {TEAMS.map((team) => (
                <TouchableOpacity
                  key={team}
                  style={[
                    styles.filterChip,
                    filters.team === team && styles.filterChipActive,
                  ]}
                  onPress={() => setFilters((prev) => ({ ...prev, team }))}
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      filters.team === team && styles.filterChipTextActive,
                    ]}
                  >
                    {team}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Reset Filters */}
          <TouchableOpacity
            style={styles.resetButton}
            onPress={() =>
              setFilters({
                position: "ALL",
                team: "ALL",
                searchTerm: "",
                tier: undefined,
                available: true,
              })
            }
          >
            <Text style={styles.resetButtonText}>Reset Filters</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderViewTabs = () => (
    <View style={styles.viewTabs}>
      {[
        { key: "players", label: "Players", icon: "people" },
        { key: "board", label: "Draft Board", icon: "grid" },
        {
          key: "queue",
          label: "Queue",
          icon: "list",
          badge: draftQueue.length,
        },
      ].map((tab) => (
        <TouchableOpacity
          key={tab.key}
          style={[
            styles.viewTab,
            currentView === tab.key && styles.viewTabActive,
          ]}
          onPress={() => setCurrentView(tab.key as any)}
        >
          <View style={styles.tabContent}>
            <Ionicons
              name={tab.icon as any}
              size={18}
              color={currentView === tab.key ? "#3b82f6" : "#6b7280"}
            />
            <Text
              style={[
                styles.viewTabText,
                currentView === tab.key && styles.viewTabTextActive,
              ]}
            >
              {tab.label}
            </Text>
            {tab.badge > 0 && (
              <View style={styles.tabBadge}>
                <Text style={styles.tabBadgeText}>{tab.badge}</Text>
              </View>
            )}
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderContent = () => {
    switch (currentView) {
      case "board":
        return (
          <View style={styles.boardContainer}>
            <MobileDraftBoard
              teams={draftTeams}
              picks={boardPicks}
              currentPick={currentPick}
              totalRounds={draftSettings.totalRounds}
              variant="compact"
            />
          </View>
        );

      case "queue":
        return (
          <View style={styles.queueContainer}>
            {draftQueue.length === 0 ? (
              <View style={styles.emptyQueue}>
                <Ionicons name="list-outline" size={48} color="#d1d5db" />
                <Text style={styles.emptyQueueText}>No players in queue</Text>
                <Text style={styles.emptyQueueSubtext}>
                  Add players to your draft queue for easy access
                </Text>
              </View>
            ) : (
              <FlatList
                data={draftQueue}
                renderItem={renderQueueItem}
                keyExtractor={(item) => item.id}
                style={styles.queueList}
              />
            )}
          </View>
        );

      default:
        return (
          <View style={styles.playersContainer}>
            <View style={styles.playersHeader}>
              <Text style={styles.playersCount}>
                {filteredPlayers.length} players available
              </Text>
              <TouchableOpacity
                style={styles.filterButton}
                onPress={() => setShowFilters(true)}
              >
                <Ionicons name="filter" size={20} color="#6b7280" />
                <Text style={styles.filterButtonText}>Filter</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={filteredPlayers}
              renderItem={renderPlayer}
              keyExtractor={(item) => item.id}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.playersList}
            />
          </View>
        );
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Draft Status Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.currentPickText}>Pick #{currentPick}</Text>
          <Text style={styles.roundText}>Round {currentRound}</Text>
          <Text style={[styles.turnText, isMyTurn && styles.myTurnText]}>
            {isMyTurn ? "YOUR TURN" : `${currentTeam.name}'s Turn`}
          </Text>
        </View>

        <Animated.View
          style={[styles.timerContainer, { transform: [{ scale: scaleAnim }] }]}
        >
          <Text
            style={[
              styles.timerText,
              timeRemaining <= 10 && styles.timerUrgent,
            ]}
          >
            {formatTime(timeRemaining)}
          </Text>
        </Animated.View>
      </View>

      {/* View Navigation */}
      {renderViewTabs()}

      {/* Main Content */}
      <View style={styles.content}>{renderContent()}</View>

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

      {renderFilterModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#2563eb",
  },
  headerLeft: {
    alignItems: "flex-start",
  },
  currentPickText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "bold",
  },
  roundText: {
    color: "#bfdbfe",
    fontSize: 14,
    marginTop: 2,
  },
  turnText: {
    color: "#bfdbfe",
    fontSize: 12,
    marginTop: 2,
  },
  myTurnText: {
    color: "#fbbf24",
    fontWeight: "bold",
  },
  timerContainer: {
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  timerText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "bold",
  },
  timerUrgent: {
    color: "#ef4444",
  },

  // View Tabs
  viewTabs: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  viewTab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
  },
  viewTabActive: {
    borderBottomWidth: 2,
    borderBottomColor: "#3b82f6",
  },
  tabContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  viewTabText: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  viewTabTextActive: {
    color: "#3b82f6",
    fontWeight: "600",
  },
  tabBadge: {
    backgroundColor: "#ef4444",
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: "center",
    alignItems: "center",
  },
  tabBadgeText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "600",
  },

  // Content Areas
  content: {
    flex: 1,
  },

  // Players View
  playersContainer: {
    flex: 1,
  },
  playersHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  playersCount: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  filterButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#f1f5f9",
    borderRadius: 6,
  },
  filterButtonText: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  playersList: {
    padding: 16,
  },
  playerContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  playerCardDrafted: {
    opacity: 0.6,
  },
  playerCardQueued: {
    borderColor: "#10b981",
    borderWidth: 2,
  },
  playerActions: {
    flexDirection: "column",
    marginLeft: 12,
    gap: 8,
  },
  queueButton: {
    padding: 8,
  },
  watchButton: {
    padding: 8,
  },

  // Draft Board View
  boardContainer: {
    flex: 1,
    padding: 16,
  },

  // Queue View
  queueContainer: {
    flex: 1,
  },
  emptyQueue: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  emptyQueueText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#6b7280",
    marginTop: 16,
  },
  emptyQueueSubtext: {
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
    marginTop: 8,
  },
  queueList: {
    flex: 1,
  },
  queueItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  queuePlayerInfo: {
    flex: 1,
  },
  queuePlayerName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  queuePlayerDetails: {
    fontSize: 14,
    color: "#6b7280",
    marginTop: 4,
  },
  removeButton: {
    padding: 8,
  },

  // Filter Modal
  modalContainer: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 20,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1e293b",
  },
  modalClose: {
    fontSize: 16,
    color: "#3b82f6",
    fontWeight: "500",
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  filterSection: {
    marginBottom: 24,
  },
  filterLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: 12,
  },
  searchInput: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  filterChip: {
    backgroundColor: "#f1f5f9",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: "#3b82f6",
  },
  filterChipText: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  filterChipTextActive: {
    color: "#ffffff",
  },
  resetButton: {
    backgroundColor: "#ef4444",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 16,
  },
  resetButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "600",
  },

  // Controls
  controls: {
    flexDirection: "row",
    padding: 16,
    gap: 12,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
  },
  controlButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  autoDraftButton: {
    backgroundColor: "#059669",
  },
  exitButton: {
    backgroundColor: "#ef4444",
  },
  controlButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});
