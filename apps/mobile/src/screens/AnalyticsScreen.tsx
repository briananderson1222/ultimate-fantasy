/**
 * Enhanced Mobile Analytics Screen
 *
 * A comprehensive analytics dashboard providing deep insights into fantasy
 * performance, player trends, league comparisons, and strategic recommendations.
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
  Modal,
  Switch,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Enhanced interfaces for comprehensive analytics
interface PerformanceMetrics {
  weeklyPoints: number[];
  seasonTotal: number;
  averagePoints: number;
  bestWeek: number;
  worstWeek: number;
  consistency: number; // 0-100 scale
  winRate: number;
  currentRank: number;
  projectedFinish: number;
  pointsAboveAverage: number;
  optimalLineupPercentage: number;
}

interface PlayerAnalysis {
  playerId: string;
  name: string;
  position: string;
  team: string;
  weeklyPerformance: number[];
  averagePoints: number;
  consistency: number;
  valueOverReplacement: number;
  timesBenched: number;
  timesStarted: number;
  bestPerformance: number;
  worstPerformance: number;
  trend: 'improving' | 'declining' | 'stable';
}

interface PositionAnalysis {
  position: string;
  totalPoints: number;
  averagePoints: number;
  bestPlayer: PlayerAnalysis;
  consistency: number;
  dropoffToNext: number;
  strengthRank: number; // 1-12 vs league
}

interface LeagueComparison {
  metric: string;
  myValue: number;
  leagueAverage: number;
  leagueMedian: number;
  rank: number;
  percentile: number;
}

interface WeeklyMatchup {
  week: number;
  opponent: string;
  myScore: number;
  opponentScore: number;
  result: 'W' | 'L';
  pointsDifference: number;
  optimalScore: number;
  efficiencyPercentage: number;
}

interface TrendInsight {
  id: string;
  type: 'positive' | 'negative' | 'neutral';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation?: string;
}

// Mock comprehensive analytics data
const MOCK_PERFORMANCE: PerformanceMetrics = {
  weeklyPoints: [87.2, 92.4, 76.8, 105.3, 89.7, 94.1, 82.5, 98.2, 91.6, 88.9],
  seasonTotal: 906.7,
  averagePoints: 90.67,
  bestWeek: 105.3,
  worstWeek: 76.8,
  consistency: 78,
  winRate: 70,
  currentRank: 3,
  projectedFinish: 2,
  pointsAboveAverage: 45.2,
  optimalLineupPercentage: 82.5,
};

const MOCK_PLAYER_ANALYSIS: PlayerAnalysis[] = [
  {
    playerId: 'p1',
    name: 'Josh Allen',
    position: 'QB',
    team: 'BUF',
    weeklyPerformance: [24.3, 21.7, 18.9, 28.4, 22.1, 25.8, 19.6, 26.2, 23.5, 20.8],
    averagePoints: 23.13,
    consistency: 85,
    valueOverReplacement: 6.8,
    timesBenched: 0,
    timesStarted: 10,
    bestPerformance: 28.4,
    worstPerformance: 18.9,
    trend: 'stable',
  },
  {
    playerId: 'p2',
    name: 'Christian McCaffrey',
    position: 'RB',
    team: 'SF',
    weeklyPerformance: [28.6, 15.2, 22.8, 31.4, 19.7, 26.3, 21.9, 29.1, 24.6, 18.3],
    averagePoints: 23.79,
    consistency: 72,
    valueOverReplacement: 8.2,
    timesBenched: 1,
    timesStarted: 9,
    bestPerformance: 31.4,
    worstPerformance: 15.2,
    trend: 'improving',
  },
];

const MOCK_POSITION_ANALYSIS: PositionAnalysis[] = [
  {
    position: 'QB',
    totalPoints: 231.3,
    averagePoints: 23.13,
    bestPlayer: MOCK_PLAYER_ANALYSIS[0],
    consistency: 85,
    dropoffToNext: 2.4,
    strengthRank: 4,
  },
  {
    position: 'RB',
    totalPoints: 237.9,
    averagePoints: 23.79,
    bestPlayer: MOCK_PLAYER_ANALYSIS[1],
    consistency: 72,
    dropoffToNext: 5.1,
    strengthRank: 2,
  },
];

const MOCK_LEAGUE_COMPARISON: LeagueComparison[] = [
  { metric: 'Total Points', myValue: 906.7, leagueAverage: 861.4, leagueMedian: 855.2, rank: 3, percentile: 83 },
  { metric: 'Avg Points', myValue: 90.67, leagueAverage: 86.14, leagueMedian: 85.52, rank: 3, percentile: 83 },
  { metric: 'Consistency', myValue: 78, leagueAverage: 72, leagueMedian: 70, rank: 4, percentile: 75 },
  { metric: 'Optimal %', myValue: 82.5, leagueAverage: 76.8, leagueMedian: 75.2, rank: 2, percentile: 92 },
];

const MOCK_WEEKLY_MATCHUPS: WeeklyMatchup[] = [
  { week: 1, opponent: 'Team Alpha', myScore: 87.2, opponentScore: 92.1, result: 'L', pointsDifference: -4.9, optimalScore: 98.3, efficiencyPercentage: 88.7 },
  { week: 2, opponent: 'Team Beta', myScore: 92.4, opponentScore: 78.6, result: 'W', pointsDifference: 13.8, optimalScore: 105.2, efficiencyPercentage: 87.8 },
  { week: 3, opponent: 'Team Gamma', myScore: 76.8, opponentScore: 89.3, result: 'L', pointsDifference: -12.5, optimalScore: 91.7, efficiencyPercentage: 83.8 },
];

const MOCK_INSIGHTS: TrendInsight[] = [
  {
    id: 'i1',
    type: 'positive',
    title: 'Strong QB Performance',
    description: 'Josh Allen has been consistently outperforming QB average by 6.8 points',
    impact: 'high',
    recommendation: 'Consider leveraging QB strength in trades'
  },
  {
    id: 'i2',
    type: 'negative',
    title: 'RB Inconsistency',
    description: 'Running back position showing high variance with 28% consistency drop',
    impact: 'medium',
    recommendation: 'Target consistent RB2 options on waiver wire'
  },
  {
    id: 'i3',
    type: 'neutral',
    title: 'Optimal Lineup Rate',
    description: 'Setting optimal lineups 82.5% of the time, above league average',
    impact: 'medium',
  },
];

export default function AnalyticsScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = Dimensions.get('window');

  // State management
  const [refreshing, setRefreshing] = useState(false);
  const [currentTab, setCurrentTab] = useState<'overview' | 'players' | 'positions' | 'league' | 'insights'>('overview');
  const [timeRange, setTimeRange] = useState<'season' | 'recent' | 'projected'>('season');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Computed values
  const filteredData = useMemo(() => {
    // Filter data based on time range
    switch (timeRange) {
      case 'recent':
        return {
          weeklyPoints: MOCK_PERFORMANCE.weeklyPoints.slice(-4),
          playerAnalysis: MOCK_PLAYER_ANALYSIS.map(p => ({
            ...p,
            weeklyPerformance: p.weeklyPerformance.slice(-4)
          }))
        };
      case 'projected':
        // Extend with projected values
        return {
          weeklyPoints: [...MOCK_PERFORMANCE.weeklyPoints, 93.2, 88.7, 91.4], // Projected next 3 weeks
          playerAnalysis: MOCK_PLAYER_ANALYSIS
        };
      default:
        return {
          weeklyPoints: MOCK_PERFORMANCE.weeklyPoints,
          playerAnalysis: MOCK_PLAYER_ANALYSIS
        };
    }
  }, [timeRange]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  }, []);

  const getPerformanceColor = (value: number, benchmark: number) => {
    if (value > benchmark * 1.1) return '#10b981'; // Green for good
    if (value < benchmark * 0.9) return '#ef4444'; // Red for bad
    return '#f59e0b'; // Amber for average
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return 'trending-up';
      case 'declining': return 'trending-down';
      case 'stable': return 'remove';
      default: return 'remove';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return '#10b981';
      case 'declining': return '#ef4444';
      case 'stable': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const renderOverviewTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      {/* Performance Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Season Performance</Text>
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{MOCK_PERFORMANCE.seasonTotal}</Text>
            <Text style={styles.metricLabel}>Total Points</Text>
            <Text style={[styles.metricChange, { color: '#10b981' }]}>
              +{MOCK_PERFORMANCE.pointsAboveAverage} vs Avg
            </Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>#{MOCK_PERFORMANCE.currentRank}</Text>
            <Text style={styles.metricLabel}>Current Rank</Text>
            <Text style={[styles.metricChange, { color: '#10b981' }]}>
              Proj: #{MOCK_PERFORMANCE.projectedFinish}
            </Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{MOCK_PERFORMANCE.winRate}%</Text>
            <Text style={styles.metricLabel}>Win Rate</Text>
            <Text style={styles.metricChange}>7-3 Record</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{MOCK_PERFORMANCE.consistency}</Text>
            <Text style={styles.metricLabel}>Consistency</Text>
            <Text style={[styles.metricChange, { color: '#f59e0b' }]}>Above Average</Text>
          </View>
        </View>
      </View>

      {/* Weekly Points Chart Placeholder */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Weekly Performance Trend</Text>
        <View style={styles.chartContainer}>
          <View style={styles.chartPlaceholder}>
            <Ionicons name="bar-chart" size={48} color="#d1d5db" />
            <Text style={styles.chartPlaceholderText}>
              Weekly scoring chart would be rendered here
            </Text>
          </View>
        </View>
      </View>

      {/* Recent Matchups */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Matchups</Text>
        {MOCK_WEEKLY_MATCHUPS.map((matchup) => (
          <View key={matchup.week} style={styles.matchupCard}>
            <View style={styles.matchupHeader}>
              <Text style={styles.matchupWeek}>Week {matchup.week}</Text>
              <View style={[
                styles.resultBadge,
                { backgroundColor: matchup.result === 'W' ? '#10b981' : '#ef4444' }
              ]}>
                <Text style={styles.resultText}>{matchup.result}</Text>
              </View>
            </View>
            <Text style={styles.matchupOpponent}>vs {matchup.opponent}</Text>
            <View style={styles.scoreContainer}>
              <Text style={styles.myScore}>{matchup.myScore}</Text>
              <Text style={styles.scoreSeparator}>-</Text>
              <Text style={styles.opponentScore}>{matchup.opponentScore}</Text>
            </View>
            <Text style={styles.efficiencyText}>
              Efficiency: {matchup.efficiencyPercentage}% (Optimal: {matchup.optimalScore})
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderPlayersTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Player Performance Analysis</Text>
        {MOCK_PLAYER_ANALYSIS.map((player) => (
          <View key={player.playerId} style={styles.playerAnalysisCard}>
            <View style={styles.playerHeader}>
              <View style={styles.playerInfo}>
                <Text style={styles.playerName}>{player.name}</Text>
                <Text style={styles.playerDetails}>{player.position} • {player.team}</Text>
              </View>
              <View style={styles.playerTrend}>
                <Ionicons
                  name={getTrendIcon(player.trend) as any}
                  size={16}
                  color={getTrendColor(player.trend)}
                />
                <Text style={[styles.trendText, { color: getTrendColor(player.trend) }]}>
                  {player.trend.toUpperCase()}
                </Text>
              </View>
            </View>

            <View style={styles.playerMetrics}>
              <View style={styles.playerMetric}>
                <Text style={styles.metricValue}>{player.averagePoints.toFixed(1)}</Text>
                <Text style={styles.metricLabel}>Avg Points</Text>
              </View>
              <View style={styles.playerMetric}>
                <Text style={styles.metricValue}>{player.consistency}</Text>
                <Text style={styles.metricLabel}>Consistency</Text>
              </View>
              <View style={styles.playerMetric}>
                <Text style={styles.metricValue}>+{player.valueOverReplacement.toFixed(1)}</Text>
                <Text style={styles.metricLabel}>VORP</Text>
              </View>
              <View style={styles.playerMetric}>
                <Text style={styles.metricValue}>{player.timesStarted}/{player.timesStarted + player.timesBenched}</Text>
                <Text style={styles.metricLabel}>Starts</Text>
              </View>
            </View>

            <View style={styles.performanceRange}>
              <Text style={styles.rangeLabel}>
                Range: {player.worstPerformance} - {player.bestPerformance}
              </Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderPositionsTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Position Analysis</Text>
        {MOCK_POSITION_ANALYSIS.map((position) => (
          <View key={position.position} style={styles.positionCard}>
            <View style={styles.positionHeader}>
              <Text style={styles.positionTitle}>{position.position}</Text>
              <View style={styles.strengthRank}>
                <Text style={styles.strengthText}>
                  League Rank: #{position.strengthRank}
                </Text>
              </View>
            </View>

            <View style={styles.positionMetrics}>
              <View style={styles.positionMetric}>
                <Text style={styles.metricValue}>{position.totalPoints}</Text>
                <Text style={styles.metricLabel}>Total Points</Text>
              </View>
              <View style={styles.positionMetric}>
                <Text style={styles.metricValue}>{position.averagePoints.toFixed(1)}</Text>
                <Text style={styles.metricLabel}>Avg/Week</Text>
              </View>
              <View style={styles.positionMetric}>
                <Text style={styles.metricValue}>{position.consistency}</Text>
                <Text style={styles.metricLabel}>Consistency</Text>
              </View>
              <View style={styles.positionMetric}>
                <Text style={styles.metricValue}>{position.dropoffToNext.toFixed(1)}</Text>
                <Text style={styles.metricLabel}>Dropoff</Text>
              </View>
            </View>

            <View style={styles.bestPlayer}>
              <Text style={styles.bestPlayerLabel}>Top Performer:</Text>
              <Text style={styles.bestPlayerName}>
                {position.bestPlayer.name} ({position.bestPlayer.averagePoints.toFixed(1)} pts/week)
              </Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderLeagueTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>League Comparison</Text>
        {MOCK_LEAGUE_COMPARISON.map((comparison) => (
          <View key={comparison.metric} style={styles.comparisonCard}>
            <View style={styles.comparisonHeader}>
              <Text style={styles.comparisonMetric}>{comparison.metric}</Text>
              <View style={styles.rankBadge}>
                <Text style={styles.rankText}>#{comparison.rank}</Text>
              </View>
            </View>

            <View style={styles.comparisonValues}>
              <View style={styles.comparisonValue}>
                <Text style={styles.valueNumber}>{comparison.myValue}</Text>
                <Text style={styles.valueLabel}>You</Text>
              </View>
              <View style={styles.comparisonValue}>
                <Text style={styles.valueNumber}>{comparison.leagueAverage}</Text>
                <Text style={styles.valueLabel}>League Avg</Text>
              </View>
              <View style={styles.comparisonValue}>
                <Text style={styles.valueNumber}>{comparison.leagueMedian}</Text>
                <Text style={styles.valueLabel}>Median</Text>
              </View>
            </View>

            <View style={styles.percentileBar}>
              <View style={styles.percentileProgress}>
                <View
                  style={[
                    styles.percentileFill,
                    { width: `${comparison.percentile}%`, backgroundColor: getPerformanceColor(comparison.percentile, 50) }
                  ]}
                />
              </View>
              <Text style={styles.percentileText}>{comparison.percentile}th percentile</Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderInsightsTab = () => (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>AI Insights & Recommendations</Text>
        {MOCK_INSIGHTS.map((insight) => (
          <View key={insight.id} style={[
            styles.insightCard,
            { borderLeftColor: insight.type === 'positive' ? '#10b981' :
                              insight.type === 'negative' ? '#ef4444' : '#6b7280' }
          ]}>
            <View style={styles.insightHeader}>
              <View style={styles.insightTitleContainer}>
                <Ionicons
                  name={insight.type === 'positive' ? 'trending-up' :
                        insight.type === 'negative' ? 'trending-down' : 'information-circle'}
                  size={16}
                  color={insight.type === 'positive' ? '#10b981' :
                         insight.type === 'negative' ? '#ef4444' : '#6b7280'}
                />
                <Text style={styles.insightTitle}>{insight.title}</Text>
              </View>
              <View style={[
                styles.impactBadge,
                { backgroundColor: insight.impact === 'high' ? '#ef4444' :
                                  insight.impact === 'medium' ? '#f59e0b' : '#6b7280' }
              ]}>
                <Text style={styles.impactText}>{insight.impact.toUpperCase()}</Text>
              </View>
            </View>

            <Text style={styles.insightDescription}>{insight.description}</Text>

            {insight.recommendation && (
              <View style={styles.recommendationContainer}>
                <Text style={styles.recommendationLabel}>💡 Recommendation:</Text>
                <Text style={styles.recommendationText}>{insight.recommendation}</Text>
              </View>
            )}
          </View>
        ))}
      </View>
    </ScrollView>
  );

  const renderTabBar = () => (
    <View style={styles.tabBar}>
      {[
        { key: 'overview', label: 'Overview', icon: 'analytics' },
        { key: 'players', label: 'Players', icon: 'people' },
        { key: 'positions', label: 'Positions', icon: 'stats-chart' },
        { key: 'league', label: 'League', icon: 'trophy' },
        { key: 'insights', label: 'Insights', icon: 'bulb' }
      ].map((tab) => (
        <TouchableOpacity
          key={tab.key}
          style={[styles.tab, currentTab === tab.key && styles.activeTab]}
          onPress={() => setCurrentTab(tab.key as any)}
        >
          <Ionicons
            name={tab.icon as any}
            size={18}
            color={currentTab === tab.key ? '#3b82f6' : '#6b7280'}
          />
          <Text style={[
            styles.tabLabel,
            currentTab === tab.key && styles.activeTabLabel
          ]}>
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderContent = () => {
    switch (currentTab) {
      case 'players': return renderPlayersTab();
      case 'positions': return renderPositionsTab();
      case 'league': return renderLeagueTab();
      case 'insights': return renderInsightsTab();
      default: return renderOverviewTab();
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Analytics</Text>
          <Text style={styles.headerSubtitle}>Deep performance insights</Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.timeRangeButton}
            onPress={() => {
              const ranges = ['season', 'recent', 'projected'];
              const currentIndex = ranges.indexOf(timeRange);
              const nextIndex = (currentIndex + 1) % ranges.length;
              setTimeRange(ranges[nextIndex] as any);
            }}
          >
            <Text style={styles.timeRangeText}>
              {timeRange.charAt(0).toUpperCase() + timeRange.slice(1)}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setShowAdvanced(!showAdvanced)}
          >
            <Ionicons
              name={showAdvanced ? "eye" : "eye-outline"}
              size={20}
              color={showAdvanced ? "#3b82f6" : "#6b7280"}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab Bar */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabBarScroll}>
        {renderTabBar()}
      </ScrollView>

      {/* Content */}
      <View style={styles.content}>
        <ScrollView
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          contentContainerStyle={styles.contentContainer}
        >
          {renderContent()}
        </ScrollView>
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
    alignItems: 'center',
    gap: 12,
  },
  timeRangeButton: {
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  timeRangeText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
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
  tabBarScroll: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    flexGrow: 0,
  },
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: 4,
  },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    alignItems: 'center',
    gap: 4,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3b82f6',
  },
  tabLabel: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
  },
  activeTabLabel: {
    color: '#3b82f6',
    fontWeight: '600',
  },

  // Content
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },

  // Sections
  section: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 16,
  },

  // Metrics Grid
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metricCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#f8fafc',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 4,
  },
  metricChange: {
    fontSize: 11,
    fontWeight: '500',
  },

  // Chart
  chartContainer: {
    height: 200,
    borderRadius: 8,
    overflow: 'hidden',
  },
  chartPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
  chartPlaceholderText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },

  // Matchup Cards
  matchupCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  matchupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  matchupWeek: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  resultBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  resultText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: '600',
  },
  matchupOpponent: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 8,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  myScore: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  scoreSeparator: {
    fontSize: 16,
    color: '#6b7280',
    marginHorizontal: 12,
  },
  opponentScore: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#6b7280',
  },
  efficiencyText: {
    fontSize: 11,
    color: '#9ca3af',
    textAlign: 'center',
  },

  // Player Analysis
  playerAnalysisCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  playerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  playerDetails: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
  },
  playerTrend: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: {
    fontSize: 11,
    fontWeight: '600',
  },
  playerMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  playerMetric: {
    alignItems: 'center',
  },
  performanceRange: {
    alignItems: 'center',
  },
  rangeLabel: {
    fontSize: 11,
    color: '#9ca3af',
  },

  // Position Analysis
  positionCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  positionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  strengthRank: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  strengthText: {
    fontSize: 11,
    color: '#ffffff',
    fontWeight: '600',
  },
  positionMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  positionMetric: {
    alignItems: 'center',
  },
  bestPlayer: {
    alignItems: 'center',
  },
  bestPlayerLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  bestPlayerName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },

  // League Comparison
  comparisonCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  comparisonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  comparisonMetric: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  rankBadge: {
    backgroundColor: '#f59e0b',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  rankText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: '600',
  },
  comparisonValues: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  comparisonValue: {
    alignItems: 'center',
  },
  valueNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 2,
  },
  valueLabel: {
    fontSize: 11,
    color: '#6b7280',
  },
  percentileBar: {
    alignItems: 'center',
  },
  percentileProgress: {
    width: '100%',
    height: 6,
    backgroundColor: '#e2e8f0',
    borderRadius: 3,
    marginBottom: 4,
  },
  percentileFill: {
    height: '100%',
    borderRadius: 3,
  },
  percentileText: {
    fontSize: 11,
    color: '#6b7280',
  },

  // Insights
  insightCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    borderLeftWidth: 4,
    padding: 12,
    marginBottom: 12,
  },
  insightHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  insightTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  impactBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  impactText: {
    fontSize: 9,
    color: '#ffffff',
    fontWeight: '600',
  },
  insightDescription: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 8,
    lineHeight: 20,
  },
  recommendationContainer: {
    backgroundColor: '#f0f9ff',
    borderRadius: 6,
    padding: 8,
  },
  recommendationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#0369a1',
    marginBottom: 4,
  },
  recommendationText: {
    fontSize: 13,
    color: '#0c4a6e',
    lineHeight: 18,
  },
});