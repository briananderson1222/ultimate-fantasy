/**
 * Enhanced Mobile Player Search Screen
 *
 * A comprehensive player search interface with advanced filtering,
 * sorting, comparison tools, and detailed player information.
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Modal,
  ScrollView,
  Alert,
  RefreshControl,
  Dimensions,
  Switch,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  MobilePlayerCard,
  type Player as UIPlayer,
} from "@ultimate-fantasy/ui-components/src/components/PlayerCard";

// Enhanced player interface with search-specific data
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

  // Additional search/filter fields
  adp?: number; // Average Draft Position
  tier?: number;
  bye_week?: number;
  salary?: number; // DFS salary
  ownership_percentage?: number;
  target_share?: number;
  snap_count?: number;
  recent_points?: number[];
  trending?: "up" | "down" | "steady";
  news_count?: number;
  injury_risk?: "low" | "medium" | "high";

  // Stats for filtering
  stats?: {
    rushing_yards?: number;
    passing_yards?: number;
    receiving_yards?: number;
    touchdowns?: number;
    receptions?: number;
    targets?: number;
    carries?: number;
    fantasy_points_per_game?: number;
  };
}

interface SearchFilters {
  searchTerm: string;
  position: string;
  team: string;
  status: string;
  tier?: number;
  minRank?: number;
  maxRank?: number;
  minProjection?: number;
  maxProjection?: number;
  trending?: string;
  injuryRisk?: string;
  availability: "all" | "available" | "owned";
}

interface SortOption {
  key: string;
  label: string;
  field: keyof Player | string;
  direction: "asc" | "desc";
}

// Mock comprehensive player data
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
    salary: 9200,
    ownership_percentage: 23.4,
    trending: "up",
    news_count: 2,
    injury_risk: "low",
    stats: {
      passing_yards: 3264,
      touchdowns: 28,
      fantasy_points_per_game: 23.8,
    },
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
    salary: 9800,
    ownership_percentage: 31.2,
    trending: "steady",
    news_count: 1,
    injury_risk: "medium",
    stats: {
      rushing_yards: 1139,
      receiving_yards: 564,
      touchdowns: 18,
      fantasy_points_per_game: 21.4,
    },
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
    salary: 8900,
    ownership_percentage: 18.7,
    trending: "down",
    news_count: 4,
    injury_risk: "high",
    stats: {
      receiving_yards: 1492,
      receptions: 145,
      touchdowns: 8,
      fantasy_points_per_game: 18.2,
    },
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
    salary: 7800,
    ownership_percentage: 27.3,
    trending: "up",
    news_count: 0,
    injury_risk: "low",
    stats: {
      receiving_yards: 992,
      receptions: 110,
      touchdowns: 12,
      fantasy_points_per_game: 14.9,
    },
  },
  {
    id: "p5",
    name: "Stefon Diggs",
    position: "WR",
    team: "BUF",
    rank: 5,
    projected_points: 17.8,
    status: "healthy",
    adp: 14.2,
    tier: 2,
    bye_week: 12,
    salary: 8200,
    ownership_percentage: 15.8,
    trending: "steady",
    news_count: 1,
    injury_risk: "low",
    stats: {
      receiving_yards: 1429,
      receptions: 108,
      touchdowns: 11,
      fantasy_points_per_game: 16.7,
    },
  },
  // Add more players for better search experience
  {
    id: "p6",
    name: "Derrick Henry",
    position: "RB",
    team: "TEN",
    rank: 6,
    projected_points: 18.3,
    status: "healthy",
    adp: 15.7,
    tier: 2,
    bye_week: 7,
    salary: 8700,
    ownership_percentage: 22.1,
    trending: "up",
    news_count: 0,
    injury_risk: "low",
    stats: {
      rushing_yards: 1538,
      touchdowns: 13,
      fantasy_points_per_game: 17.2,
    },
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
    salary: 8800,
    ownership_percentage: 19.6,
    trending: "steady",
    news_count: 2,
    injury_risk: "low",
    stats: {
      passing_yards: 4839,
      touchdowns: 37,
      fantasy_points_per_game: 22.3,
    },
  },
];

const POSITIONS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"];
const TEAMS = [
  "ALL",
  "BUF",
  "SF",
  "LAR",
  "KC",
  "TEN",
  "MIA",
  "LAC",
  "BAL",
  "NE",
  "NYJ",
  "DAL",
];
const STATUSES = [
  "ALL",
  "healthy",
  "questionable",
  "doubtful",
  "out",
  "injured",
];
const TRENDING_OPTIONS = ["ALL", "up", "down", "steady"];
const INJURY_RISK_OPTIONS = ["ALL", "low", "medium", "high"];

const SORT_OPTIONS: SortOption[] = [
  {
    key: "rank-asc",
    label: "Rank (Best First)",
    field: "rank",
    direction: "asc",
  },
  {
    key: "projection-desc",
    label: "Projected Points (High to Low)",
    field: "projected_points",
    direction: "desc",
  },
  {
    key: "adp-asc",
    label: "ADP (Early to Late)",
    field: "adp",
    direction: "asc",
  },
  { key: "name-asc", label: "Name (A to Z)", field: "name", direction: "asc" },
  { key: "team-asc", label: "Team (A to Z)", field: "team", direction: "asc" },
  {
    key: "salary-desc",
    label: "Salary (High to Low)",
    field: "salary",
    direction: "desc",
  },
  {
    key: "ownership-desc",
    label: "Ownership % (High to Low)",
    field: "ownership_percentage",
    direction: "desc",
  },
];

export default function PlayerSearchScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = Dimensions.get("window");

  // State
  const [players] = useState<Player[]>(MOCK_PLAYERS);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPlayers, setSelectedPlayers] = useState<Set<string>>(
    new Set(),
  );

  // Filter and search state
  const [filters, setFilters] = useState<SearchFilters>({
    searchTerm: "",
    position: "ALL",
    team: "ALL",
    status: "ALL",
    tier: undefined,
    minRank: undefined,
    maxRank: undefined,
    minProjection: undefined,
    maxProjection: undefined,
    trending: "ALL",
    injuryRisk: "ALL",
    availability: "all",
  });

  // Sorting
  const [currentSort, setCurrentSort] = useState<SortOption>(SORT_OPTIONS[0]);

  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [showSortOptions, setShowSortOptions] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  // Advanced search modes
  const [advancedMode, setAdvancedMode] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);

  // Filter and sort players
  const filteredAndSortedPlayers = useMemo(() => {
    let filtered = players.filter((player) => {
      // Text search
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        if (
          !player.name.toLowerCase().includes(searchLower) &&
          !player.team.toLowerCase().includes(searchLower) &&
          !player.position.toLowerCase().includes(searchLower)
        ) {
          return false;
        }
      }

      // Position filter
      if (filters.position !== "ALL" && player.position !== filters.position)
        return false;

      // Team filter
      if (filters.team !== "ALL" && player.team !== filters.team) return false;

      // Status filter
      if (filters.status !== "ALL" && player.status !== filters.status)
        return false;

      // Tier filter
      if (filters.tier && player.tier !== filters.tier) return false;

      // Rank range
      if (filters.minRank && player.rank < filters.minRank) return false;
      if (filters.maxRank && player.rank > filters.maxRank) return false;

      // Projection range
      if (
        filters.minProjection &&
        player.projected_points < filters.minProjection
      )
        return false;
      if (
        filters.maxProjection &&
        player.projected_points > filters.maxProjection
      )
        return false;

      // Trending filter
      if (filters.trending !== "ALL" && player.trending !== filters.trending)
        return false;

      // Injury risk filter
      if (
        filters.injuryRisk !== "ALL" &&
        player.injury_risk !== filters.injuryRisk
      )
        return false;

      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      const field = currentSort.field;
      let aVal = a[field as keyof Player];
      let bVal = b[field as keyof Player];

      // Handle undefined values
      if (aVal === undefined)
        aVal = currentSort.direction === "asc" ? Infinity : -Infinity;
      if (bVal === undefined)
        bVal = currentSort.direction === "asc" ? Infinity : -Infinity;

      if (typeof aVal === "string" && typeof bVal === "string") {
        return currentSort.direction === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      const numA = Number(aVal);
      const numB = Number(bVal);
      return currentSort.direction === "asc" ? numA - numB : numB - numA;
    });

    return filtered;
  }, [players, filters, currentSort]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setRefreshing(false);
  }, []);

  const togglePlayerSelection = (playerId: string) => {
    const newSelection = new Set(selectedPlayers);
    if (newSelection.has(playerId)) {
      newSelection.delete(playerId);
    } else {
      newSelection.add(playerId);
    }
    setSelectedPlayers(newSelection);
  };

  const clearFilters = () => {
    setFilters({
      searchTerm: "",
      position: "ALL",
      team: "ALL",
      status: "ALL",
      tier: undefined,
      minRank: undefined,
      maxRank: undefined,
      minProjection: undefined,
      maxProjection: undefined,
      trending: "ALL",
      injuryRisk: "ALL",
      availability: "all",
    });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.searchTerm) count++;
    if (filters.position !== "ALL") count++;
    if (filters.team !== "ALL") count++;
    if (filters.status !== "ALL") count++;
    if (filters.tier) count++;
    if (filters.minRank || filters.maxRank) count++;
    if (filters.minProjection || filters.maxProjection) count++;
    if (filters.trending !== "ALL") count++;
    if (filters.injuryRisk !== "ALL") count++;
    if (filters.availability !== "all") count++;
    return count;
  };

  const renderPlayer = ({ item: player }: { item: Player }) => {
    const isSelected = selectedPlayers.has(player.id);

    return (
      <View style={styles.playerContainer}>
        <MobilePlayerCard
          player={player}
          variant={viewMode === "grid" ? "compact" : "standard"}
          selected={isSelected}
          selectable={comparisonMode}
          showProjection={true}
          onPress={() =>
            comparisonMode
              ? togglePlayerSelection(player.id)
              : handlePlayerPress(player)
          }
          style={[
            viewMode === "grid" && styles.gridPlayerCard,
            isSelected && styles.selectedCard,
          ]}
        />

        {/* Additional player info overlay */}
        <View style={styles.playerOverlay}>
          {player.trending && (
            <View
              style={[
                styles.trendingBadge,
                { backgroundColor: getTrendingColor(player.trending) },
              ]}
            >
              <Ionicons
                name={getTrendingIcon(player.trending)}
                size={12}
                color="#ffffff"
              />
            </View>
          )}

          {player.news_count > 0 && (
            <View style={styles.newsBadge}>
              <Text style={styles.newsBadgeText}>{player.news_count}</Text>
            </View>
          )}

          {comparisonMode && (
            <TouchableOpacity
              style={[
                styles.selectionButton,
                isSelected && styles.selectionButtonActive,
              ]}
              onPress={() => togglePlayerSelection(player.id)}
            >
              <Ionicons
                name={isSelected ? "checkmark-circle" : "add-circle-outline"}
                size={24}
                color={isSelected ? "#10b981" : "#6b7280"}
              />
            </TouchableOpacity>
          )}
        </View>

        {/* Extended stats for advanced mode */}
        {advancedMode && (
          <View style={styles.extendedStats}>
            <Text style={styles.statText}>
              ADP: {player.adp?.toFixed(1) || "N/A"} | Own:{" "}
              {player.ownership_percentage?.toFixed(1)}% | Tier:{" "}
              {player.tier || "N/A"}
            </Text>
            {player.stats && (
              <Text style={styles.statText}>
                FPPG:{" "}
                {player.stats.fantasy_points_per_game?.toFixed(1) || "N/A"}
              </Text>
            )}
          </View>
        )}
      </View>
    );
  };

  const handlePlayerPress = (player: Player) => {
    Alert.alert(
      player.name,
      `${player.position} - ${player.team}\nProjected: ${player.projected_points} pts\nRank: #${player.rank}`,
      [
        {
          text: "Add to Watchlist",
          onPress: () => console.log("Add to watchlist"),
        },
        { text: "View Details", onPress: () => console.log("View details") },
        { text: "Cancel", style: "cancel" },
      ],
    );
  };

  const getTrendingColor = (trending: string) => {
    switch (trending) {
      case "up":
        return "#10b981";
      case "down":
        return "#ef4444";
      case "steady":
        return "#6b7280";
      default:
        return "#6b7280";
    }
  };

  const getTrendingIcon = (trending: string) => {
    switch (trending) {
      case "up":
        return "trending-up" as const;
      case "down":
        return "trending-down" as const;
      case "steady":
        return "remove" as const;
      default:
        return "remove" as const;
    }
  };

  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Filter Players</Text>
          <View style={styles.modalHeaderButtons}>
            <TouchableOpacity style={styles.clearButton} onPress={clearFilters}>
              <Text style={styles.clearButtonText}>Clear All</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setShowFilters(false)}>
              <Text style={styles.modalClose}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView style={styles.modalContent}>
          {/* Search */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Search Player</Text>
            <TextInput
              style={styles.searchInput}
              placeholder="Player name, team, or position..."
              value={filters.searchTerm}
              onChangeText={(text) =>
                setFilters((prev) => ({ ...prev, searchTerm: text }))
              }
            />
          </View>

          {/* Position */}
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

          {/* Team */}
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

          {/* Status */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Health Status</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {STATUSES.map((status) => (
                <TouchableOpacity
                  key={status}
                  style={[
                    styles.filterChip,
                    filters.status === status && styles.filterChipActive,
                  ]}
                  onPress={() => setFilters((prev) => ({ ...prev, status }))}
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      filters.status === status && styles.filterChipTextActive,
                    ]}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Advanced Filters */}
          <View style={styles.filterSection}>
            <View style={styles.switchRow}>
              <Text style={styles.filterLabel}>Advanced Filters</Text>
              <Switch
                value={advancedMode}
                onValueChange={setAdvancedMode}
                trackColor={{ false: "#d1d5db", true: "#3b82f6" }}
                thumbColor={advancedMode ? "#ffffff" : "#f4f3f4"}
              />
            </View>

            {advancedMode && (
              <>
                {/* Rank Range */}
                <View style={styles.rangeSection}>
                  <Text style={styles.rangeLabel}>Rank Range</Text>
                  <View style={styles.rangeInputs}>
                    <TextInput
                      style={styles.rangeInput}
                      placeholder="Min"
                      value={filters.minRank?.toString() || ""}
                      onChangeText={(text) =>
                        setFilters((prev) => ({
                          ...prev,
                          minRank: text ? parseInt(text) : undefined,
                        }))
                      }
                      keyboardType="numeric"
                    />
                    <Text style={styles.rangeSeparator}>to</Text>
                    <TextInput
                      style={styles.rangeInput}
                      placeholder="Max"
                      value={filters.maxRank?.toString() || ""}
                      onChangeText={(text) =>
                        setFilters((prev) => ({
                          ...prev,
                          maxRank: text ? parseInt(text) : undefined,
                        }))
                      }
                      keyboardType="numeric"
                    />
                  </View>
                </View>

                {/* Projection Range */}
                <View style={styles.rangeSection}>
                  <Text style={styles.rangeLabel}>Projected Points Range</Text>
                  <View style={styles.rangeInputs}>
                    <TextInput
                      style={styles.rangeInput}
                      placeholder="Min"
                      value={filters.minProjection?.toString() || ""}
                      onChangeText={(text) =>
                        setFilters((prev) => ({
                          ...prev,
                          minProjection: text ? parseFloat(text) : undefined,
                        }))
                      }
                      keyboardType="numeric"
                    />
                    <Text style={styles.rangeSeparator}>to</Text>
                    <TextInput
                      style={styles.rangeInput}
                      placeholder="Max"
                      value={filters.maxProjection?.toString() || ""}
                      onChangeText={(text) =>
                        setFilters((prev) => ({
                          ...prev,
                          maxProjection: text ? parseFloat(text) : undefined,
                        }))
                      }
                      keyboardType="numeric"
                    />
                  </View>
                </View>

                {/* Trending */}
                <View style={styles.filterSection}>
                  <Text style={styles.filterLabel}>Trending</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    {TRENDING_OPTIONS.map((trend) => (
                      <TouchableOpacity
                        key={trend}
                        style={[
                          styles.filterChip,
                          filters.trending === trend && styles.filterChipActive,
                        ]}
                        onPress={() =>
                          setFilters((prev) => ({ ...prev, trending: trend }))
                        }
                      >
                        <Text
                          style={[
                            styles.filterChipText,
                            filters.trending === trend &&
                              styles.filterChipTextActive,
                          ]}
                        >
                          {trend.charAt(0).toUpperCase() + trend.slice(1)}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              </>
            )}
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderSortModal = () => (
    <Modal
      visible={showSortOptions}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Sort Players</Text>
          <TouchableOpacity onPress={() => setShowSortOptions(false)}>
            <Text style={styles.modalClose}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          {SORT_OPTIONS.map((option) => (
            <TouchableOpacity
              key={option.key}
              style={[
                styles.sortOption,
                currentSort.key === option.key && styles.sortOptionActive,
              ]}
              onPress={() => {
                setCurrentSort(option);
                setShowSortOptions(false);
              }}
            >
              <Text
                style={[
                  styles.sortOptionText,
                  currentSort.key === option.key && styles.sortOptionTextActive,
                ]}
              >
                {option.label}
              </Text>
              {currentSort.key === option.key && (
                <Ionicons name="checkmark" size={20} color="#3b82f6" />
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </Modal>
  );

  const renderComparisonPanel = () => {
    if (!comparisonMode || selectedPlayers.size === 0) return null;

    const selectedPlayerData = players.filter((p) => selectedPlayers.has(p.id));

    return (
      <View style={styles.comparisonPanel}>
        <View style={styles.comparisonHeader}>
          <Text style={styles.comparisonTitle}>
            Compare Players ({selectedPlayers.size})
          </Text>
          <TouchableOpacity
            style={styles.compareButton}
            onPress={() => setShowComparison(true)}
            disabled={selectedPlayers.size < 2}
          >
            <Text style={styles.compareButtonText}>Compare</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Player Search</Text>
          <Text style={styles.headerSubtitle}>
            {filteredAndSortedPlayers.length} players found
          </Text>
        </View>

        <View style={styles.headerButtons}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setViewMode(viewMode === "list" ? "grid" : "list")}
          >
            <Ionicons
              name={viewMode === "list" ? "grid" : "list"}
              size={20}
              color="#6b7280"
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.headerButton,
              comparisonMode && styles.headerButtonActive,
            ]}
            onPress={() => {
              setComparisonMode(!comparisonMode);
              if (comparisonMode) {
                setSelectedPlayers(new Set());
              }
            }}
          >
            <Ionicons
              name="analytics"
              size={20}
              color={comparisonMode ? "#3b82f6" : "#6b7280"}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Quick Search */}
      <View style={styles.quickSearch}>
        <View style={styles.searchInputContainer}>
          <Ionicons
            name="search"
            size={20}
            color="#6b7280"
            style={styles.searchIcon}
          />
          <TextInput
            style={styles.quickSearchInput}
            placeholder="Search players..."
            value={filters.searchTerm}
            onChangeText={(text) =>
              setFilters((prev) => ({ ...prev, searchTerm: text }))
            }
          />
          {filters.searchTerm.length > 0 && (
            <TouchableOpacity
              style={styles.clearSearchButton}
              onPress={() =>
                setFilters((prev) => ({ ...prev, searchTerm: "" }))
              }
            >
              <Ionicons name="close-circle" size={20} color="#6b7280" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Filter and Sort Bar */}
      <View style={styles.controlBar}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setShowFilters(true)}
        >
          <Ionicons name="filter" size={18} color="#6b7280" />
          <Text style={styles.controlButtonText}>
            Filter {getActiveFilterCount() > 0 && `(${getActiveFilterCount()})`}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setShowSortOptions(true)}
        >
          <Ionicons name="swap-vertical" size={18} color="#6b7280" />
          <Text style={styles.controlButtonText}>Sort</Text>
        </TouchableOpacity>

        <Text style={styles.sortIndicator}>{currentSort.label}</Text>
      </View>

      {/* Player List */}
      <FlatList
        data={filteredAndSortedPlayers}
        renderItem={renderPlayer}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={[
          styles.playersList,
          viewMode === "grid" && styles.playersListGrid,
        ]}
        numColumns={viewMode === "grid" ? 2 : 1}
        key={viewMode} // Force re-render when switching modes
        showsVerticalScrollIndicator={false}
      />

      {/* Comparison Panel */}
      {renderComparisonPanel()}

      {/* Modals */}
      {renderFilterModal()}
      {renderSortModal()}
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
  headerButtons: {
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
  headerButtonActive: {
    backgroundColor: "#eff6ff",
  },

  // Quick Search
  quickSearch: {
    padding: 16,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  searchInputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f8fafc",
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  quickSearchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
    color: "#1e293b",
  },
  clearSearchButton: {
    padding: 4,
  },

  // Control Bar
  controlBar: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  controlButton: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#f1f5f9",
    borderRadius: 6,
    marginRight: 12,
    gap: 6,
  },
  controlButtonText: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  sortIndicator: {
    flex: 1,
    fontSize: 12,
    color: "#9ca3af",
    textAlign: "right",
  },

  // Player List
  playersList: {
    padding: 16,
  },
  playersListGrid: {
    alignItems: "stretch",
  },
  playerContainer: {
    position: "relative",
    marginBottom: 12,
  },
  gridPlayerCard: {
    width: "100%",
  },
  selectedCard: {
    borderColor: "#3b82f6",
    borderWidth: 2,
  },

  // Player Overlay
  playerOverlay: {
    position: "absolute",
    top: 8,
    right: 8,
    flexDirection: "row",
    gap: 6,
  },
  trendingBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
  },
  newsBadge: {
    backgroundColor: "#ef4444",
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 6,
  },
  newsBadgeText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "600",
  },
  selectionButton: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  selectionButtonActive: {
    backgroundColor: "#eff6ff",
  },

  // Extended Stats
  extendedStats: {
    backgroundColor: "#f8fafc",
    borderRadius: 6,
    padding: 8,
    marginTop: 8,
  },
  statText: {
    fontSize: 11,
    color: "#6b7280",
    marginBottom: 2,
  },

  // Comparison Panel
  comparisonPanel: {
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e2e8f0",
    padding: 16,
  },
  comparisonHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  comparisonTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b",
  },
  compareButton: {
    backgroundColor: "#3b82f6",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  compareButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600",
  },

  // Modal Styles
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
  modalHeaderButtons: {
    flexDirection: "row",
    gap: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1e293b",
  },
  clearButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#f1f5f9",
    borderRadius: 6,
  },
  clearButtonText: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
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

  // Filter Sections
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

  // Advanced Filters
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  rangeSection: {
    marginTop: 16,
  },
  rangeLabel: {
    fontSize: 14,
    fontWeight: "500",
    color: "#374151",
    marginBottom: 8,
  },
  rangeInputs: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  rangeInput: {
    flex: 1,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 6,
    padding: 10,
    fontSize: 14,
    textAlign: "center",
  },
  rangeSeparator: {
    fontSize: 14,
    color: "#6b7280",
  },

  // Sort Options
  sortOption: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f5f9",
  },
  sortOptionActive: {
    backgroundColor: "#eff6ff",
  },
  sortOptionText: {
    fontSize: 16,
    color: "#1e293b",
  },
  sortOptionTextActive: {
    color: "#3b82f6",
    fontWeight: "600",
  },
});
