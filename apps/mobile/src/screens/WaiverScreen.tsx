/**
 * Enhanced Mobile Waiver Management Screen
 *
 * A comprehensive waiver wire interface with advanced player discovery,
 * claim management, priority tracking, and strategic recommendations.
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Modal,
  TextInput,
  ScrollView,
  Dimensions,
  Switch,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  MobilePlayerCard,
  type Player as UIPlayer
} from '@ultimate-fantasy/ui-components/src/components/PlayerCard';

// Enhanced interfaces for waiver management
interface Player extends UIPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  projected_points: number;
  status: 'healthy' | 'questionable' | 'doubtful' | 'out' | 'injured' | 'bye' | 'suspended';

  // Waiver-specific fields
  ownership_percentage: number;
  added_percentage: number; // % added this week
  dropped_percentage: number; // % dropped this week
  waiver_priority: number;
  recent_performance: number[];
  trending: 'up' | 'down' | 'steady';
  opportunity_score: number; // 0-100 based on role, matchup, etc.
  ros_rank: number; // Rest of season rank
  next_3_weeks_avg: number;
  injury_risk: 'low' | 'medium' | 'high';
  schedule_strength: number;
  bye_week: number;

  // News and updates
  news_count: number;
  last_updated: string;
  breakout_candidate: boolean;
  sleeper_pick: boolean;
}

interface WaiverClaim {
  id: string;
  player: Player;
  claim_type: 'add' | 'add_drop';
  drop_player?: Player;
  priority: number;
  amount: number; // FAAB amount
  status: 'pending' | 'successful' | 'failed' | 'cancelled';
  created_at: Date;
  processes_at: Date;
  reason: string;
}

interface WaiverSettings {
  budget: number;
  remaining_budget: number;
  priority_number: number;
  auto_process: boolean;
  notifications: boolean;
  min_ownership_threshold: number;
  max_bid_percentage: number;
}

interface WaiverFilter {
  position: string;
  team: string;
  trending: string;
  minOwnership: number;
  maxOwnership: number;
  opportunity: string;
  breakout: boolean;
  sleeper: boolean;
}

// Mock comprehensive waiver data
const MOCK_WAIVER_PLAYERS: Player[] = [
  {
    id: 'w1',
    name: 'Tank Dell',
    position: 'WR',
    team: 'HOU',
    projected_points: 12.4,
    status: 'healthy',
    ownership_percentage: 23.7,
    added_percentage: 15.2,
    dropped_percentage: 3.1,
    waiver_priority: 8,
    recent_performance: [18.3, 8.7, 14.2, 21.6],
    trending: 'up',
    opportunity_score: 78,
    ros_rank: 45,
    next_3_weeks_avg: 13.8,
    injury_risk: 'low',
    schedule_strength: 0.6,
    bye_week: 10,
    news_count: 2,
    last_updated: '2 hours ago',
    breakout_candidate: true,
    sleeper_pick: false,
  },
  {
    id: 'w2',
    name: 'Tyjae Spears',
    position: 'RB',
    team: 'TEN',
    projected_points: 9.8,
    status: 'healthy',
    ownership_percentage: 47.3,
    added_percentage: 8.9,
    dropped_percentage: 12.4,
    waiver_priority: 12,
    recent_performance: [6.2, 15.7, 4.3, 18.9],
    trending: 'steady',
    opportunity_score: 65,
    ros_rank: 67,
    next_3_weeks_avg: 11.2,
    injury_risk: 'medium',
    schedule_strength: 0.8,
    bye_week: 7,
    news_count: 1,
    last_updated: '1 hour ago',
    breakout_candidate: false,
    sleeper_pick: true,
  },
  {
    id: 'w3',
    name: 'Jordan Addison',
    position: 'WR',
    team: 'MIN',
    projected_points: 11.7,
    status: 'questionable',
    ownership_percentage: 34.2,
    added_percentage: 22.1,
    dropped_percentage: 5.8,
    waiver_priority: 6,
    recent_performance: [22.4, 7.8, 16.3, 12.1],
    trending: 'up',
    opportunity_score: 82,
    ros_rank: 38,
    next_3_weeks_avg: 14.6,
    injury_risk: 'medium',
    schedule_strength: 0.7,
    bye_week: 13,
    news_count: 3,
    last_updated: '30 minutes ago',
    breakout_candidate: true,
    sleeper_pick: false,
  },
  {
    id: 'w4',
    name: 'Jerome Ford',
    position: 'RB',
    team: 'CLE',
    projected_points: 8.9,
    status: 'healthy',
    ownership_percentage: 15.6,
    added_percentage: 31.4,
    dropped_percentage: 8.7,
    waiver_priority: 15,
    recent_performance: [2.3, 8.9, 19.7, 12.4],
    trending: 'up',
    opportunity_score: 88,
    ros_rank: 52,
    next_3_weeks_avg: 12.8,
    injury_risk: 'low',
    schedule_strength: 0.5,
    bye_week: 5,
    news_count: 4,
    last_updated: '15 minutes ago',
    breakout_candidate: true,
    sleeper_pick: true,
  },
];

const MOCK_WAIVER_CLAIMS: WaiverClaim[] = [
  {
    id: 'c1',
    player: MOCK_WAIVER_PLAYERS[0],
    claim_type: 'add_drop',
    drop_player: {
      id: 'p1',
      name: 'Curtis Samuel',
      position: 'WR',
      team: 'WAS',
      projected_points: 8.3,
      status: 'healthy',
    } as Player,
    priority: 3,
    amount: 15,
    status: 'pending',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
    processes_at: new Date(Date.now() + 10 * 60 * 60 * 1000),
    reason: 'Higher upside with C.J. Stroud connection'
  },
  {
    id: 'c2',
    player: MOCK_WAIVER_PLAYERS[3],
    claim_type: 'add',
    priority: 5,
    amount: 8,
    status: 'successful',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
    processes_at: new Date(Date.now() - 12 * 60 * 60 * 1000),
    reason: 'Injury replacement pickup'
  },
];

const MOCK_SETTINGS: WaiverSettings = {
  budget: 100,
  remaining_budget: 72,
  priority_number: 7,
  auto_process: true,
  notifications: true,
  min_ownership_threshold: 5,
  max_bid_percentage: 25,
};

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST'];
const TEAMS = ['ALL', 'HOU', 'TEN', 'MIN', 'CLE', 'BUF', 'KC', 'SF', 'LAR'];
const TRENDING_OPTIONS = ['ALL', 'up', 'down', 'steady'];
const OPPORTUNITY_LEVELS = ['ALL', 'high', 'medium', 'low'];

export default function WaiverScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = Dimensions.get('window');

  // Core state
  const [waiverPlayers] = useState<Player[]>(MOCK_WAIVER_PLAYERS);
  const [waiverClaims, setWaiverClaims] = useState<WaiverClaim[]>(MOCK_WAIVER_CLAIMS);
  const [settings, setSettings] = useState<WaiverSettings>(MOCK_SETTINGS);
  const [refreshing, setRefreshing] = useState(false);

  // UI state
  const [currentTab, setCurrentTab] = useState<'available' | 'claims' | 'trends' | 'settings'>('available');
  const [showAddClaim, setShowAddClaim] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Claim creation state
  const [newClaim, setNewClaim] = useState<{
    type: 'add' | 'add_drop';
    dropPlayer: Player | null;
    bidAmount: number;
    reason: string;
  }>({
    type: 'add',
    dropPlayer: null,
    bidAmount: 0,
    reason: ''
  });

  // Filtering state
  const [filters, setFilters] = useState<WaiverFilter>({
    position: 'ALL',
    team: 'ALL',
    trending: 'ALL',
    minOwnership: 0,
    maxOwnership: 100,
    opportunity: 'ALL',
    breakout: false,
    sleeper: false,
  });

  // Computed values
  const filteredPlayers = useMemo(() => {
    return waiverPlayers.filter(player => {
      if (filters.position !== 'ALL' && player.position !== filters.position) return false;
      if (filters.team !== 'ALL' && player.team !== filters.team) return false;
      if (filters.trending !== 'ALL' && player.trending !== filters.trending) return false;
      if (player.ownership_percentage < filters.minOwnership || player.ownership_percentage > filters.maxOwnership) return false;
      if (filters.opportunity !== 'ALL') {
        const level = player.opportunity_score >= 75 ? 'high' : player.opportunity_score >= 50 ? 'medium' : 'low';
        if (level !== filters.opportunity) return false;
      }
      if (filters.breakout && !player.breakout_candidate) return false;
      if (filters.sleeper && !player.sleeper_pick) return false;

      return true;
    });
  }, [waiverPlayers, filters]);

  const pendingClaims = waiverClaims.filter(claim => claim.status === 'pending');
  const completedClaims = waiverClaims.filter(claim => claim.status !== 'pending');

  // Waiver management
  const createWaiverClaim = useCallback(() => {
    if (!selectedPlayer) return;

    if (newClaim.bidAmount > settings.remaining_budget) {
      Alert.alert('Insufficient Budget', 'You don\'t have enough FAAB remaining for this bid.');
      return;
    }

    const claim: WaiverClaim = {
      id: `c${Date.now()}`,
      player: selectedPlayer,
      claim_type: newClaim.type,
      drop_player: newClaim.dropPlayer,
      priority: pendingClaims.length + 1,
      amount: newClaim.bidAmount,
      status: 'pending',
      created_at: new Date(),
      processes_at: new Date(Date.now() + 24 * 60 * 60 * 1000), // Tomorrow
      reason: newClaim.reason || `Claiming ${selectedPlayer.name}`
    };

    setWaiverClaims(prev => [claim, ...prev]);
    setSettings(prev => ({ ...prev, remaining_budget: prev.remaining_budget - newClaim.bidAmount }));
    setNewClaim({ type: 'add', dropPlayer: null, bidAmount: 0, reason: '' });
    setSelectedPlayer(null);
    setShowAddClaim(false);

    Alert.alert('Claim Submitted', `Your waiver claim for ${selectedPlayer.name} has been submitted.`);
  }, [selectedPlayer, newClaim, settings.remaining_budget, pendingClaims.length]);

  const cancelWaiverClaim = useCallback((claimId: string) => {
    Alert.alert(
      'Cancel Claim',
      'Are you sure you want to cancel this waiver claim?',
      [
        { text: 'No', style: 'cancel' },
        { text: 'Yes', onPress: () => {
          const claim = waiverClaims.find(c => c.id === claimId);
          if (claim) {
            setWaiverClaims(prev => prev.map(c =>
              c.id === claimId ? { ...c, status: 'cancelled' } : c
            ));
            setSettings(prev => ({ ...prev, remaining_budget: prev.remaining_budget + claim.amount }));
            Alert.alert('Claim Cancelled', 'Your waiver claim has been cancelled.');
          }
        }}
      ]
    );
  }, [waiverClaims]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  }, []);

  const getOpportunityColor = (score: number) => {
    if (score >= 75) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const getTrendingIcon = (trending: string) => {
    switch (trending) {
      case 'up': return 'trending-up';
      case 'down': return 'trending-down';
      case 'steady': return 'remove';
      default: return 'remove';
    }
  };

  const getTrendingColor = (trending: string) => {
    switch (trending) {
      case 'up': return '#10b981';
      case 'down': return '#ef4444';
      case 'steady': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getTimeUntilProcess = (processTime: Date) => {
    const now = new Date();
    const diff = processTime.getTime() - now.getTime();
    if (diff <= 0) return 'Processing';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const renderWaiverPlayer = ({ item: player }: { item: Player }) => (
    <View style={styles.playerContainer}>
      <MobilePlayerCard
        player={player}
        variant="standard"
        showProjection={true}
        onPress={() => {
          setSelectedPlayer(player);
          setShowAddClaim(true);
        }}
      />

      {/* Enhanced player overlay */}
      <View style={styles.playerOverlay}>
        <View style={styles.overlayTop}>
          {player.breakout_candidate && (
            <View style={styles.breakoutBadge}>
              <Text style={styles.badgeText}>🚀</Text>
            </View>
          )}
          {player.sleeper_pick && (
            <View style={styles.sleeperBadge}>
              <Text style={styles.badgeText}>💎</Text>
            </View>
          )}
          <View style={[styles.trendingBadge, { backgroundColor: getTrendingColor(player.trending) }]}>
            <Ionicons
              name={getTrendingIcon(player.trending) as any}
              size={12}
              color="#ffffff"
            />
          </View>
        </View>
      </View>

      {/* Enhanced stats */}
      <View style={styles.playerStats}>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Own:</Text>
          <Text style={styles.statValue}>{player.ownership_percentage.toFixed(1)}%</Text>
        </View>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Add:</Text>
          <Text style={[styles.statValue, { color: '#10b981' }]}>
            +{player.added_percentage.toFixed(1)}%
          </Text>
        </View>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Opp:</Text>
          <Text style={[styles.statValue, { color: getOpportunityColor(player.opportunity_score) }]}>
            {player.opportunity_score}
          </Text>
        </View>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>ROS:</Text>
          <Text style={styles.statValue}>#{player.ros_rank}</Text>
        </View>
      </View>

      {player.news_count > 0 && (
        <View style={styles.newsIndicator}>
          <Ionicons name="newspaper" size={12} color="#3b82f6" />
          <Text style={styles.newsCount}>{player.news_count}</Text>
        </View>
      )}
    </View>
  );

  const renderWaiverClaim = ({ item: claim }: { item: WaiverClaim }) => (
    <View style={styles.claimCard}>
      <View style={styles.claimHeader}>
        <View style={styles.claimPlayerInfo}>
          <Text style={styles.claimPlayerName}>{claim.player.name}</Text>
          <Text style={styles.claimPlayerDetails}>
            {claim.player.position} • {claim.player.team}
          </Text>
        </View>

        <View style={styles.claimStatus}>
          <View style={[
            styles.statusBadge,
            { backgroundColor: claim.status === 'pending' ? '#f59e0b' :
                              claim.status === 'successful' ? '#10b981' : '#ef4444' }
          ]}>
            <Text style={styles.statusText}>{claim.status.toUpperCase()}</Text>
          </View>
        </View>
      </View>

      <View style={styles.claimDetails}>
        <Text style={styles.claimType}>
          {claim.claim_type === 'add_drop' ? 'Add/Drop' : 'Add'} • ${claim.amount} FAAB
        </Text>
        {claim.drop_player && (
          <Text style={styles.dropPlayer}>Drop: {claim.drop_player.name}</Text>
        )}
        <Text style={styles.claimReason}>{claim.reason}</Text>
      </View>

      <View style={styles.claimFooter}>
        <Text style={styles.claimTime}>
          {claim.status === 'pending' ? `Processes in ${getTimeUntilProcess(claim.processes_at)}` :
           `Processed ${claim.processes_at.toLocaleDateString()}`}
        </Text>

        {claim.status === 'pending' && (
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => cancelWaiverClaim(claim.id)}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  const renderAddClaimModal = () => (
    <Modal
      visible={showAddClaim}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>
            Add Waiver Claim
          </Text>
          <TouchableOpacity onPress={() => setShowAddClaim(false)}>
            <Text style={styles.modalClose}>Cancel</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          {selectedPlayer && (
            <>
              {/* Player Info */}
              <View style={styles.claimSection}>
                <Text style={styles.sectionTitle}>Player</Text>
                <MobilePlayerCard
                  player={selectedPlayer}
                  variant="detailed"
                  showProjection={true}
                />
              </View>

              {/* Claim Type */}
              <View style={styles.claimSection}>
                <Text style={styles.sectionTitle}>Claim Type</Text>
                <View style={styles.claimTypeOptions}>
                  <TouchableOpacity
                    style={[
                      styles.claimTypeOption,
                      newClaim.type === 'add' && styles.selectedClaimType
                    ]}
                    onPress={() => setNewClaim(prev => ({ ...prev, type: 'add' }))}
                  >
                    <Text style={[
                      styles.claimTypeText,
                      newClaim.type === 'add' && styles.selectedClaimTypeText
                    ]}>
                      Add Only
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.claimTypeOption,
                      newClaim.type === 'add_drop' && styles.selectedClaimType
                    ]}
                    onPress={() => setNewClaim(prev => ({ ...prev, type: 'add_drop' }))}
                  >
                    <Text style={[
                      styles.claimTypeText,
                      newClaim.type === 'add_drop' && styles.selectedClaimTypeText
                    ]}>
                      Add/Drop
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Drop Player (if add/drop) */}
              {newClaim.type === 'add_drop' && (
                <View style={styles.claimSection}>
                  <Text style={styles.sectionTitle}>Drop Player</Text>
                  <TouchableOpacity style={styles.selectDropPlayer}>
                    <Text style={styles.selectDropPlayerText}>
                      {newClaim.dropPlayer ? newClaim.dropPlayer.name : 'Select player to drop'}
                    </Text>
                    <Ionicons name="chevron-forward" size={20} color="#6b7280" />
                  </TouchableOpacity>
                </View>
              )}

              {/* FAAB Bid */}
              <View style={styles.claimSection}>
                <Text style={styles.sectionTitle}>
                  FAAB Bid (Remaining: ${settings.remaining_budget})
                </Text>
                <TextInput
                  style={styles.bidInput}
                  placeholder="Enter bid amount"
                  value={newClaim.bidAmount.toString()}
                  onChangeText={(text) => setNewClaim(prev => ({
                    ...prev,
                    bidAmount: parseInt(text) || 0
                  }))}
                  keyboardType="numeric"
                />
                <View style={styles.bidSuggestions}>
                  {[5, 10, 15, 20].map(amount => (
                    <TouchableOpacity
                      key={amount}
                      style={styles.bidSuggestion}
                      onPress={() => setNewClaim(prev => ({ ...prev, bidAmount: amount }))}
                    >
                      <Text style={styles.bidSuggestionText}>${amount}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {/* Reason */}
              <View style={styles.claimSection}>
                <Text style={styles.sectionTitle}>Reason (Optional)</Text>
                <TextInput
                  style={styles.reasonInput}
                  placeholder="Why are you claiming this player?"
                  value={newClaim.reason}
                  onChangeText={(text) => setNewClaim(prev => ({ ...prev, reason: text }))}
                  multiline
                  numberOfLines={3}
                />
              </View>

              {/* Submit Button */}
              <TouchableOpacity
                style={[styles.submitClaimButton, {
                  opacity: newClaim.bidAmount > 0 ? 1 : 0.5
                }]}
                onPress={createWaiverClaim}
                disabled={newClaim.bidAmount === 0}
              >
                <Text style={styles.submitClaimButtonText}>
                  Submit Claim (${newClaim.bidAmount})
                </Text>
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );

  const renderTabBar = () => (
    <View style={styles.tabBar}>
      {[
        { key: 'available', label: 'Available', icon: 'people', badge: filteredPlayers.length },
        { key: 'claims', label: 'Claims', icon: 'list', badge: pendingClaims.length },
        { key: 'trends', label: 'Trends', icon: 'trending-up' },
        { key: 'settings', label: 'Settings', icon: 'settings' }
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
              color={currentTab === tab.key ? '#3b82f6' : '#6b7280'}
            />
            <Text style={[
              styles.tabLabel,
              currentTab === tab.key && styles.activeTabLabel
            ]}>
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

  const renderContent = () => {
    switch (currentTab) {
      case 'claims':
        return (
          <FlatList
            data={waiverClaims}
            renderItem={renderWaiverClaim}
            keyExtractor={(item) => item.id}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            contentContainerStyle={styles.claimsList}
            showsVerticalScrollIndicator={false}
          />
        );

      case 'trends':
        return (
          <ScrollView style={styles.trendsContainer} showsVerticalScrollIndicator={false}>
            <View style={styles.trendsSection}>
              <Text style={styles.sectionTitle}>Most Added This Week</Text>
              {waiverPlayers
                .sort((a, b) => b.added_percentage - a.added_percentage)
                .slice(0, 5)
                .map((player) => (
                  <View key={player.id} style={styles.trendItem}>
                    <Text style={styles.trendPlayerName}>{player.name}</Text>
                    <Text style={styles.trendStat}>+{player.added_percentage.toFixed(1)}%</Text>
                  </View>
                ))
              }
            </View>

            <View style={styles.trendsSection}>
              <Text style={styles.sectionTitle}>Breakout Candidates</Text>
              {waiverPlayers
                .filter(p => p.breakout_candidate)
                .map((player) => (
                  <View key={player.id} style={styles.trendItem}>
                    <Text style={styles.trendPlayerName}>{player.name}</Text>
                    <Text style={styles.trendStat}>Opp: {player.opportunity_score}</Text>
                  </View>
                ))
              }
            </View>
          </ScrollView>
        );

      case 'settings':
        return (
          <ScrollView style={styles.settingsContainer} showsVerticalScrollIndicator={false}>
            <View style={styles.settingsSection}>
              <Text style={styles.sectionTitle}>Budget Status</Text>
              <View style={styles.budgetInfo}>
                <Text style={styles.budgetText}>Remaining: ${settings.remaining_budget}</Text>
                <Text style={styles.budgetText}>Total: ${settings.budget}</Text>
              </View>
              <Text style={styles.priorityText}>
                Waiver Priority: #{settings.priority_number}
              </Text>
            </View>

            <View style={styles.settingsSection}>
              <Text style={styles.sectionTitle}>Preferences</Text>
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Auto Process Claims</Text>
                <Switch
                  value={settings.auto_process}
                  onValueChange={(value) => setSettings(prev => ({ ...prev, auto_process: value }))}
                />
              </View>
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Notifications</Text>
                <Switch
                  value={settings.notifications}
                  onValueChange={(value) => setSettings(prev => ({ ...prev, notifications: value }))}
                />
              </View>
            </View>
          </ScrollView>
        );

      default:
        return (
          <FlatList
            data={filteredPlayers}
            renderItem={renderWaiverPlayer}
            keyExtractor={(item) => item.id}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            contentContainerStyle={styles.playersList}
            showsVerticalScrollIndicator={false}
          />
        );
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Waiver Wire</Text>
          <Text style={styles.headerSubtitle}>
            ${settings.remaining_budget} budget • Priority #{settings.priority_number}
          </Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowFilters(true)}
          >
            <Ionicons name="filter" size={20} color="#6b7280" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab Bar */}
      {renderTabBar()}

      {/* Content */}
      <View style={styles.content}>
        {renderContent()}
      </View>

      {/* Modals */}
      {renderAddClaimModal()}
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

  // Tab Bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3b82f6',
  },
  tabContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tabLabel: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  activeTabLabel: {
    color: '#3b82f6',
    fontWeight: '600',
  },
  tabBadge: {
    backgroundColor: '#ef4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabBadgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },

  // Content
  content: {
    flex: 1,
  },

  // Player List
  playersList: {
    padding: 16,
  },
  playerContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  playerOverlay: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 1,
  },
  overlayTop: {
    flexDirection: 'row',
    gap: 4,
  },
  breakoutBadge: {
    backgroundColor: '#ef4444',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sleeperBadge: {
    backgroundColor: '#8b5cf6',
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trendingBadge: {
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    fontSize: 12,
  },
  playerStats: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statRow: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 10,
    color: '#6b7280',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1e293b',
  },
  newsIndicator: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 6,
    paddingVertical: 2,
    gap: 4,
  },
  newsCount: {
    fontSize: 10,
    fontWeight: '600',
    color: '#3b82f6',
  },

  // Claims List
  claimsList: {
    padding: 16,
  },
  claimCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  claimHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  claimPlayerInfo: {
    flex: 1,
  },
  claimPlayerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  claimPlayerDetails: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  claimStatus: {
    alignItems: 'flex-end',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: '600',
  },
  claimDetails: {
    marginBottom: 8,
  },
  claimType: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 4,
  },
  dropPlayer: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 4,
  },
  claimReason: {
    fontSize: 13,
    color: '#64748b',
    fontStyle: 'italic',
  },
  claimFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  claimTime: {
    fontSize: 12,
    color: '#9ca3af',
  },
  cancelButton: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  cancelButtonText: {
    fontSize: 12,
    color: '#ef4444',
    fontWeight: '500',
  },

  // Trends
  trendsContainer: {
    flex: 1,
  },
  trendsSection: {
    backgroundColor: '#ffffff',
    padding: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
  },
  trendItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  trendPlayerName: {
    fontSize: 16,
    color: '#1e293b',
  },
  trendStat: {
    fontSize: 14,
    color: '#10b981',
    fontWeight: '600',
  },

  // Settings
  settingsContainer: {
    flex: 1,
  },
  settingsSection: {
    backgroundColor: '#ffffff',
    padding: 16,
    marginBottom: 8,
  },
  budgetInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  budgetText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  priorityText: {
    fontSize: 14,
    color: '#64748b',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  settingLabel: {
    fontSize: 16,
    color: '#1e293b',
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
    padding: 16,
  },

  // Claim Form
  claimSection: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  claimTypeOptions: {
    flexDirection: 'row',
    gap: 12,
  },
  claimTypeOption: {
    flex: 1,
    backgroundColor: '#f1f5f9',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  selectedClaimType: {
    backgroundColor: '#3b82f6',
  },
  claimTypeText: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  selectedClaimTypeText: {
    color: '#ffffff',
  },
  selectDropPlayer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  selectDropPlayerText: {
    fontSize: 16,
    color: '#374151',
  },
  bidInput: {
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  bidSuggestions: {
    flexDirection: 'row',
    gap: 8,
  },
  bidSuggestion: {
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  bidSuggestionText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  reasonInput: {
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    textAlignVertical: 'top',
  },
  submitClaimButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  submitClaimButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});