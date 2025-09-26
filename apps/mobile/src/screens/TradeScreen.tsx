/**
 * Enhanced Mobile Trade Interface Screen
 *
 * A comprehensive trade management interface with AI-powered trade analysis,
 * real-time trade evaluation, negotiation tools, and market insights.
 */

import React, { useState, useCallback, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Modal,
  FlatList,
  TextInput,
  Switch,
  Dimensions,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  MobileTradeAnalyzer,
  type Trade as AnalyzerTrade,
  type TradePlayer,
  type TradeTeam,
} from "@ultimate-fantasy/ui-components/src/components/TradeAnalyzer";
import {
  MobilePlayerCard,
  type Player as UIPlayer,
} from "@ultimate-fantasy/ui-components/src/components/PlayerCard";

// Enhanced interfaces for comprehensive trade management
interface Player extends UIPlayer, TradePlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  status:
    | "healthy"
    | "questionable"
    | "doubtful"
    | "out"
    | "injured"
    | "bye"
    | "suspended";

  // Trade-specific fields
  trade_value: number;
  market_value: number;
  recent_performance: number[];
  injury_risk: "low" | "medium" | "high";
  schedule_strength: number;
  bye_week: number;
  ownership_percentage?: number;
  ceiling?: number;
  floor?: number;
  consistency_rating?: number;
}

interface Trade extends AnalyzerTrade {
  id: string;
  from_team: string;
  to_team: string;
  offer_players: Player[];
  request_players: Player[];
  status: "pending" | "accepted" | "rejected" | "countered" | "expired";
  created_at: Date;
  expires_at: Date;
  fairness_score: number;
  ai_analysis?: {
    recommendation: "accept" | "reject" | "counter";
    reasoning: string;
    confidence: number;
  };
  counter_history?: CounterOffer[];
  notes?: string;
}

interface CounterOffer {
  id: string;
  timestamp: Date;
  from_team: string;
  offer_players: Player[];
  request_players: Player[];
  message?: string;
}

interface TradeFilter {
  status: string;
  team: string;
  dateRange: "all" | "week" | "month";
  minValue: number;
  maxValue: number;
}

interface MarketInsight {
  player_id: string;
  player_name: string;
  demand_level: "high" | "medium" | "low";
  price_trend: "rising" | "falling" | "stable";
  recent_trades: number;
  avg_value: number;
}

// Mock comprehensive data
const MOCK_PLAYERS: Player[] = [
  {
    id: "p1",
    name: "Josh Allen",
    position: "QB",
    team: "BUF",
    projected_points: 24.2,
    status: "healthy",
    trade_value: 85,
    market_value: 88,
    recent_performance: [28.3, 21.7, 26.8, 19.4],
    injury_risk: "low",
    schedule_strength: 0.7,
    bye_week: 12,
    ceiling: 35.8,
    floor: 15.2,
    consistency_rating: 8.5,
  },
  {
    id: "p2",
    name: "Christian McCaffrey",
    position: "RB",
    team: "SF",
    projected_points: 22.8,
    status: "healthy",
    trade_value: 92,
    market_value: 90,
    recent_performance: [25.6, 18.9, 27.2, 15.3],
    injury_risk: "medium",
    schedule_strength: 0.6,
    bye_week: 9,
    ceiling: 32.4,
    floor: 12.8,
    consistency_rating: 7.2,
  },
  {
    id: "p3",
    name: "Cooper Kupp",
    position: "WR",
    team: "LAR",
    projected_points: 19.4,
    status: "questionable",
    trade_value: 75,
    market_value: 82,
    recent_performance: [22.1, 14.8, 16.7, 11.2],
    injury_risk: "high",
    schedule_strength: 0.8,
    bye_week: 10,
    ceiling: 28.7,
    floor: 8.3,
    consistency_rating: 6.8,
  },
];

const MOCK_TRADES: Trade[] = [
  {
    id: "t1",
    from_team: "Team Alpha",
    to_team: "My Team",
    offer_players: [MOCK_PLAYERS[0]],
    request_players: [MOCK_PLAYERS[1]],
    status: "pending",
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
    expires_at: new Date(Date.now() + 22 * 60 * 60 * 1000),
    fairness_score: 75,
    ai_analysis: {
      recommendation: "counter",
      reasoning:
        "Josh Allen is valuable but CMC provides more positional scarcity at RB. Consider adding a WR2 to balance the trade.",
      confidence: 0.78,
    },
    notes: "Interested in your QB depth",
  },
  {
    id: "t2",
    from_team: "My Team",
    to_team: "Team Beta",
    offer_players: [MOCK_PLAYERS[2]],
    request_players: [MOCK_PLAYERS[0]],
    status: "countered",
    created_at: new Date(Date.now() - 6 * 60 * 60 * 1000),
    expires_at: new Date(Date.now() + 18 * 60 * 60 * 1000),
    fairness_score: 68,
    counter_history: [
      {
        id: "c1",
        timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
        from_team: "Team Beta",
        offer_players: [MOCK_PLAYERS[0]],
        request_players: [MOCK_PLAYERS[2], MOCK_PLAYERS[1]],
        message: "Need more value for my QB1",
      },
    ],
  },
];

const MOCK_TEAMS: TradeTeam[] = [
  { id: "team1", name: "My Team", record: "7-3", rank: 3 },
  { id: "team2", name: "Team Alpha", record: "6-4", rank: 5 },
  { id: "team3", name: "Team Beta", record: "8-2", rank: 1 },
  { id: "team4", name: "Team Gamma", record: "5-5", rank: 7 },
];

const MOCK_MARKET_INSIGHTS: MarketInsight[] = [
  {
    player_id: "p1",
    player_name: "Josh Allen",
    demand_level: "high",
    price_trend: "rising",
    recent_trades: 3,
    avg_value: 87,
  },
  {
    player_id: "p2",
    player_name: "Christian McCaffrey",
    demand_level: "high",
    price_trend: "stable",
    recent_trades: 5,
    avg_value: 91,
  },
];

export default function TradeScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = Dimensions.get("window");

  // Core state
  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [myPlayers] = useState<Player[]>(MOCK_PLAYERS);
  const [refreshing, setRefreshing] = useState(false);

  // UI state
  const [currentTab, setCurrentTab] = useState<
    "active" | "history" | "create" | "market"
  >("active");
  const [showTradeAnalyzer, setShowTradeAnalyzer] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [showCreateTrade, setShowCreateTrade] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Trade creation state
  const [newTrade, setNewTrade] = useState<{
    targetTeam: string;
    myPlayers: Player[];
    theirPlayers: Player[];
    message: string;
  }>({
    targetTeam: "",
    myPlayers: [],
    theirPlayers: [],
    message: "",
  });

  // Filtering state
  const [filters, setFilters] = useState<TradeFilter>({
    status: "all",
    team: "all",
    dateRange: "all",
    minValue: 0,
    maxValue: 100,
  });

  // Settings
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [notifications, setNotifications] = useState(true);

  // Computed values
  const filteredTrades = useMemo(() => {
    return trades.filter((trade) => {
      if (filters.status !== "all" && trade.status !== filters.status)
        return false;
      if (
        filters.team !== "all" &&
        trade.from_team !== filters.team &&
        trade.to_team !== filters.team
      )
        return false;

      const tradeValue =
        (trade.offer_players.reduce((sum, p) => sum + p.trade_value, 0) +
          trade.request_players.reduce((sum, p) => sum + p.trade_value, 0)) /
        2;

      if (tradeValue < filters.minValue || tradeValue > filters.maxValue)
        return false;

      // Date range filtering
      if (filters.dateRange !== "all") {
        const now = new Date();
        const daysDiff = Math.floor(
          (now.getTime() - trade.created_at.getTime()) / (1000 * 60 * 60 * 24),
        );

        if (filters.dateRange === "week" && daysDiff > 7) return false;
        if (filters.dateRange === "month" && daysDiff > 30) return false;
      }

      return true;
    });
  }, [trades, filters]);

  const activeTrades = filteredTrades.filter((t) =>
    ["pending", "countered"].includes(t.status),
  );
  const completedTrades = filteredTrades.filter((t) =>
    ["accepted", "rejected", "expired"].includes(t.status),
  );

  // Trade actions
  const handleTradeAction = useCallback(
    (trade: Trade, action: "accept" | "reject" | "counter") => {
      const actionMessages = {
        accept: "Accept this trade offer?",
        reject: "Reject this trade offer?",
        counter: "Create a counter offer?",
      };

      Alert.alert(
        `${action.charAt(0).toUpperCase() + action.slice(1)} Trade`,
        actionMessages[action],
        [
          { text: "Cancel", style: "cancel" },
          {
            text: action.charAt(0).toUpperCase() + action.slice(1),
            onPress: () => {
              if (action === "counter") {
                setSelectedTrade(trade);
                setShowCreateTrade(true);
              } else {
                setTrades((prev) =>
                  prev.map((t) =>
                    t.id === trade.id
                      ? {
                          ...t,
                          status: action === "accept" ? "accepted" : "rejected",
                        }
                      : t,
                  ),
                );
                Alert.alert(
                  "Trade Updated",
                  `Trade has been ${action}ed successfully.`,
                );
              }
            },
          },
        ],
      );
    },
    [],
  );

  const createTrade = useCallback(() => {
    if (newTrade.myPlayers.length === 0 || newTrade.theirPlayers.length === 0) {
      Alert.alert(
        "Invalid Trade",
        "Please select players for both sides of the trade.",
      );
      return;
    }

    const trade: Trade = {
      id: `t${Date.now()}`,
      from_team: "My Team",
      to_team: newTrade.targetTeam,
      offer_players: newTrade.myPlayers,
      request_players: newTrade.theirPlayers,
      status: "pending",
      created_at: new Date(),
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
      fairness_score: Math.floor(Math.random() * 40) + 60, // Mock calculation
      notes: newTrade.message,
    };

    setTrades((prev) => [trade, ...prev]);
    setNewTrade({
      targetTeam: "",
      myPlayers: [],
      theirPlayers: [],
      message: "",
    });
    setShowCreateTrade(false);
    Alert.alert("Trade Sent", "Your trade offer has been sent successfully!");
  }, [newTrade]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setRefreshing(false);
  }, []);

  const getTradeStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "#f59e0b";
      case "accepted":
        return "#10b981";
      case "rejected":
        return "#ef4444";
      case "countered":
        return "#3b82f6";
      case "expired":
        return "#6b7280";
      default:
        return "#6b7280";
    }
  };

  const getTimeRemaining = (expiresAt: Date) => {
    const now = new Date();
    const diff = expiresAt.getTime() - now.getTime();
    if (diff <= 0) return "Expired";

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const renderTradeCard = ({ item: trade }: { item: Trade }) => (
    <TouchableOpacity
      style={styles.tradeCard}
      onPress={() => {
        setSelectedTrade(trade);
        setShowTradeAnalyzer(true);
      }}
    >
      <View style={styles.tradeHeader}>
        <View style={styles.tradeTeams}>
          <Text style={styles.fromTeam}>{trade.from_team}</Text>
          <Ionicons name="arrow-forward" size={16} color="#6b7280" />
          <Text style={styles.toTeam}>{trade.to_team}</Text>
        </View>

        <View style={styles.tradeStatus}>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getTradeStatusColor(trade.status) },
            ]}
          >
            <Text style={styles.statusText}>{trade.status.toUpperCase()}</Text>
          </View>
        </View>
      </View>

      <View style={styles.tradePlayers}>
        <View style={styles.tradePlayersSide}>
          <Text style={styles.sideLabel}>Offering</Text>
          {trade.offer_players.map((player) => (
            <Text key={player.id} style={styles.playerSummary}>
              {player.name} ({player.position})
            </Text>
          ))}
        </View>

        <View style={styles.tradePlayersSide}>
          <Text style={styles.sideLabel}>Requesting</Text>
          {trade.request_players.map((player) => (
            <Text key={player.id} style={styles.playerSummary}>
              {player.name} ({player.position})
            </Text>
          ))}
        </View>
      </View>

      <View style={styles.tradeFooter}>
        <View style={styles.tradeMetrics}>
          <Text style={styles.metricText}>
            Fairness: {trade.fairness_score}%
          </Text>
          <Text style={styles.metricText}>
            Expires: {getTimeRemaining(trade.expires_at)}
          </Text>
        </View>

        {trade.status === "pending" && trade.to_team === "My Team" && (
          <View style={styles.tradeActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={(e) => {
                e.stopPropagation();
                handleTradeAction(trade, "accept");
              }}
            >
              <Ionicons name="checkmark" size={16} color="#10b981" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={(e) => {
                e.stopPropagation();
                handleTradeAction(trade, "reject");
              }}
            >
              <Ionicons name="close" size={16} color="#ef4444" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={(e) => {
                e.stopPropagation();
                handleTradeAction(trade, "counter");
              }}
            >
              <Ionicons name="return-up-back" size={16} color="#3b82f6" />
            </TouchableOpacity>
          </View>
        )}
      </View>

      {trade.ai_analysis && autoAnalyze && (
        <View style={styles.aiAnalysis}>
          <View style={styles.aiHeader}>
            <Ionicons name="sparkles" size={14} color="#8b5cf6" />
            <Text style={styles.aiLabel}>AI Analysis</Text>
          </View>
          <Text style={styles.aiRecommendation}>
            {trade.ai_analysis.recommendation.toUpperCase()}:{" "}
            {trade.ai_analysis.reasoning}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderTabBar = () => (
    <View style={styles.tabBar}>
      {[
        {
          key: "active",
          label: "Active",
          icon: "time",
          badge: activeTrades.length,
        },
        { key: "history", label: "History", icon: "archive" },
        { key: "create", label: "Create", icon: "add-circle" },
        { key: "market", label: "Market", icon: "trending-up" },
      ].map((tab) => (
        <TouchableOpacity
          key={tab.key}
          style={[styles.tab, currentTab === tab.key && styles.activeTab]}
          onPress={() => setCurrentTab(tab.key as any)}
        >
          <View style={styles.tabContent}>
            <Ionicons
              name={tab.icon as any}
              size={20}
              color={currentTab === tab.key ? "#3b82f6" : "#6b7280"}
            />
            <Text
              style={[
                styles.tabLabel,
                currentTab === tab.key && styles.activeTabLabel,
              ]}
            >
              {tab.label}
            </Text>
            {tab.badge && tab.badge > 0 && (
              <View style={styles.tabBadge}>
                <Text style={styles.tabBadgeText}>{tab.badge}</Text>
              </View>
            )}
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderActiveTab = () => (
    <FlatList
      data={activeTrades}
      renderItem={renderTradeCard}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      contentContainerStyle={styles.tradesList}
      showsVerticalScrollIndicator={false}
      ListEmptyComponent={
        <View style={styles.emptyState}>
          <Ionicons name="swap-horizontal" size={48} color="#d1d5db" />
          <Text style={styles.emptyTitle}>No Active Trades</Text>
          <Text style={styles.emptySubtitle}>
            Create a trade to get started
          </Text>
        </View>
      }
    />
  );

  const renderHistoryTab = () => (
    <FlatList
      data={completedTrades}
      renderItem={renderTradeCard}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      contentContainerStyle={styles.tradesList}
      showsVerticalScrollIndicator={false}
    />
  );

  const renderCreateTab = () => (
    <ScrollView
      style={styles.createContainer}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.createSection}>
        <Text style={styles.sectionTitle}>Select Target Team</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {MOCK_TEAMS.filter((t) => t.name !== "My Team").map((team) => (
            <TouchableOpacity
              key={team.id}
              style={[
                styles.teamOption,
                newTrade.targetTeam === team.name && styles.selectedTeamOption,
              ]}
              onPress={() =>
                setNewTrade((prev) => ({ ...prev, targetTeam: team.name }))
              }
            >
              <Text
                style={[
                  styles.teamOptionText,
                  newTrade.targetTeam === team.name &&
                    styles.selectedTeamOptionText,
                ]}
              >
                {team.name}
              </Text>
              <Text style={styles.teamRecord}>{team.record}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <View style={styles.createSection}>
        <Text style={styles.sectionTitle}>
          My Players ({newTrade.myPlayers.length})
        </Text>
        <Text style={styles.sectionSubtitle}>
          Select players you want to trade away
        </Text>
        {/* Player selection would be implemented here */}
        <TouchableOpacity style={styles.addPlayersButton}>
          <Ionicons name="add" size={20} color="#3b82f6" />
          <Text style={styles.addPlayersText}>Add My Players</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.createSection}>
        <Text style={styles.sectionTitle}>
          Their Players ({newTrade.theirPlayers.length})
        </Text>
        <Text style={styles.sectionSubtitle}>
          Select players you want to receive
        </Text>
        {/* Player selection would be implemented here */}
        <TouchableOpacity style={styles.addPlayersButton}>
          <Ionicons name="add" size={20} color="#3b82f6" />
          <Text style={styles.addPlayersText}>Add Their Players</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.createSection}>
        <Text style={styles.sectionTitle}>Message (Optional)</Text>
        <TextInput
          style={styles.messageInput}
          placeholder="Add a note to your trade offer..."
          value={newTrade.message}
          onChangeText={(text) =>
            setNewTrade((prev) => ({ ...prev, message: text }))
          }
          multiline
          numberOfLines={3}
        />
      </View>

      <TouchableOpacity
        style={[
          styles.createTradeButton,
          {
            opacity:
              newTrade.targetTeam &&
              newTrade.myPlayers.length > 0 &&
              newTrade.theirPlayers.length > 0
                ? 1
                : 0.5,
          },
        ]}
        onPress={createTrade}
        disabled={
          !newTrade.targetTeam ||
          newTrade.myPlayers.length === 0 ||
          newTrade.theirPlayers.length === 0
        }
      >
        <Text style={styles.createTradeButtonText}>Send Trade Offer</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderMarketTab = () => (
    <ScrollView
      style={styles.marketContainer}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.marketSection}>
        <Text style={styles.sectionTitle}>Market Insights</Text>
        {MOCK_MARKET_INSIGHTS.map((insight) => (
          <View key={insight.player_id} style={styles.insightCard}>
            <View style={styles.insightHeader}>
              <Text style={styles.insightPlayerName}>
                {insight.player_name}
              </Text>
              <View
                style={[
                  styles.demandBadge,
                  {
                    backgroundColor:
                      insight.demand_level === "high"
                        ? "#10b981"
                        : insight.demand_level === "medium"
                          ? "#f59e0b"
                          : "#6b7280",
                  },
                ]}
              >
                <Text style={styles.demandText}>
                  {insight.demand_level.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text style={styles.insightText}>
              Avg Value: {insight.avg_value} • Recent Trades:{" "}
              {insight.recent_trades}
            </Text>
            <Text style={styles.insightText}>
              Price Trend:{" "}
              {insight.price_trend.charAt(0).toUpperCase() +
                insight.price_trend.slice(1)}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderContent = () => {
    switch (currentTab) {
      case "history":
        return renderHistoryTab();
      case "create":
        return renderCreateTab();
      case "market":
        return renderMarketTab();
      default:
        return renderActiveTab();
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Trade Center</Text>
          <Text style={styles.headerSubtitle}>
            {activeTrades.length} active • {completedTrades.length} completed
          </Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowFilters(true)}
          >
            <Ionicons name="filter" size={20} color="#6b7280" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setAutoAnalyze(!autoAnalyze)}
          >
            <Ionicons
              name={autoAnalyze ? "sparkles" : "sparkles-outline"}
              size={20}
              color={autoAnalyze ? "#8b5cf6" : "#6b7280"}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab Bar */}
      {renderTabBar()}

      {/* Content */}
      <View style={styles.content}>{renderContent()}</View>

      {/* Trade Analyzer Modal */}
      {selectedTrade && (
        <Modal
          visible={showTradeAnalyzer}
          animationType="slide"
          presentationStyle="fullScreen"
        >
          <View style={styles.analyzerContainer}>
            <View style={styles.analyzerHeader}>
              <Text style={styles.analyzerTitle}>Trade Analysis</Text>
              <TouchableOpacity onPress={() => setShowTradeAnalyzer(false)}>
                <Ionicons name="close" size={24} color="#6b7280" />
              </TouchableOpacity>
            </View>

            <MobileTradeAnalyzer
              trade={selectedTrade}
              userTeam={{
                id: "team1",
                name: "My Team",
                record: "7-3",
                rank: 3,
              }}
              teams={MOCK_TEAMS}
              showAdvancedMetrics={true}
              onAccept={() => handleTradeAction(selectedTrade, "accept")}
              onReject={() => handleTradeAction(selectedTrade, "reject")}
              onCounter={() => handleTradeAction(selectedTrade, "counter")}
            />
          </View>
        </Modal>
      )}
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
    padding: 20,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#1e293b",
  },
  headerSubtitle: {
    fontSize: 14,
    color: "#64748b",
    marginTop: 2,
  },
  headerActions: {
    flexDirection: "row",
    gap: 12,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#f1f5f9",
    justifyContent: "center",
    alignItems: "center",
  },

  // Tab Bar
  tabBar: {
    flexDirection: "row",
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: "#3b82f6",
  },
  tabContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  tabLabel: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  activeTabLabel: {
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

  // Content
  content: {
    flex: 1,
  },

  // Trade Cards
  tradesList: {
    padding: 16,
  },
  tradeCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  tradeHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  tradeTeams: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  fromTeam: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  toTeam: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  tradeStatus: {
    alignItems: "flex-end",
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 10,
    color: "#ffffff",
    fontWeight: "600",
  },
  tradePlayers: {
    flexDirection: "row",
    gap: 16,
    marginBottom: 12,
  },
  tradePlayersSide: {
    flex: 1,
  },
  sideLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#6b7280",
    marginBottom: 6,
  },
  playerSummary: {
    fontSize: 14,
    color: "#374151",
    marginBottom: 2,
  },
  tradeFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  tradeMetrics: {
    flex: 1,
  },
  metricText: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 2,
  },
  tradeActions: {
    flexDirection: "row",
    gap: 8,
  },
  actionButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#f1f5f9",
    justifyContent: "center",
    alignItems: "center",
  },

  // AI Analysis
  aiAnalysis: {
    backgroundColor: "#f8fafc",
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    borderLeftWidth: 3,
    borderLeftColor: "#8b5cf6",
  },
  aiHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 6,
  },
  aiLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#8b5cf6",
  },
  aiRecommendation: {
    fontSize: 13,
    color: "#64748b",
    lineHeight: 18,
  },

  // Empty State
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#6b7280",
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: "#9ca3af",
    textAlign: "center",
    marginTop: 8,
  },

  // Create Trade
  createContainer: {
    flex: 1,
  },
  createSection: {
    padding: 16,
    backgroundColor: "#ffffff",
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: "#64748b",
    marginBottom: 12,
  },
  teamOption: {
    backgroundColor: "#f1f5f9",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    marginRight: 8,
    alignItems: "center",
    minWidth: 100,
  },
  selectedTeamOption: {
    backgroundColor: "#3b82f6",
  },
  teamOptionText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
  },
  selectedTeamOptionText: {
    color: "#ffffff",
  },
  teamRecord: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 2,
  },
  addPlayersButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f1f5f9",
    paddingVertical: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderStyle: "dashed",
    gap: 8,
  },
  addPlayersText: {
    fontSize: 16,
    color: "#3b82f6",
    fontWeight: "500",
  },
  messageInput: {
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    textAlignVertical: "top",
  },
  createTradeButton: {
    backgroundColor: "#3b82f6",
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: "center",
    margin: 16,
  },
  createTradeButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "600",
  },

  // Market
  marketContainer: {
    flex: 1,
  },
  marketSection: {
    padding: 16,
    backgroundColor: "#ffffff",
  },
  insightCard: {
    backgroundColor: "#f8fafc",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  insightHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  insightPlayerName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  demandBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  demandText: {
    fontSize: 10,
    color: "#ffffff",
    fontWeight: "600",
  },
  insightText: {
    fontSize: 14,
    color: "#64748b",
    marginBottom: 2,
  },

  // Trade Analyzer Modal
  analyzerContainer: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  analyzerHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 20,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  analyzerTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#1e293b",
  },
});
