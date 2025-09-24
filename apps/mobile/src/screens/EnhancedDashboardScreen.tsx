/**
 * Enhanced Mobile Dashboard Screen
 *
 * A comprehensive mobile dashboard with real-time updates, personalized content,
 * and interactive widgets for fantasy sports management.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
  FlatList,
  Modal
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { dashboardUtils, DEFAULT_WIDGETS, type WidgetKey } from '@ultimate-fantasy/shared-logic/utils/dashboard';

// Enhanced widget data interfaces
export interface DashboardWidget {
  id: WidgetKey;
  title: string;
  type: 'chart' | 'list' | 'card' | 'score' | 'news';
  data: any;
  lastUpdated: string;
  refreshing: boolean;
  error?: string;
}

export interface UserMetrics {
  totalLeagues: number;
  activeLineups: number;
  pendingTrades: number;
  waiverClaims: number;
  weeklyRank: number;
  seasonPoints: number;
  winPercentage: number;
}

export interface QuickAction {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  action: () => void;
  color: string;
  urgent?: boolean;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  timestamp: string;
  category: 'injury' | 'trade' | 'waiver' | 'news' | 'analysis';
  impact: 'high' | 'medium' | 'low';
  playerId?: string;
}

export default function EnhancedDashboardScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const { width: screenWidth } = Dimensions.get('window');

  // Dashboard state
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [userMetrics, setUserMetrics] = useState<UserMetrics | null>(null);
  const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [customizationMode, setCustomizationMode] = useState(false);

  // Widget management
  const [widgetOrder, setWidgetOrder] = useState<WidgetKey[]>(DEFAULT_WIDGETS);
  const [visibleWidgets, setVisibleWidgets] = useState<Set<WidgetKey>>(new Set(DEFAULT_WIDGETS));

  // Initialize dashboard data
  useEffect(() => {
    loadDashboardData();
    const savedOrder = dashboardUtils.loadLayout();
    setWidgetOrder(savedOrder);
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!refreshing) {
        refreshData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [refreshing]);

  const loadDashboardData = async () => {
    try {
      // Simulate loading user metrics
      const metrics: UserMetrics = {
        totalLeagues: 3,
        activeLineups: 2,
        pendingTrades: 1,
        waiverClaims: 2,
        weeklyRank: 4,
        seasonPoints: 1247.6,
        winPercentage: 67.3
      };
      setUserMetrics(metrics);

      // Load quick actions
      const actions: QuickAction[] = [
        {
          id: 'lineup',
          title: 'Set Lineup',
          subtitle: '2 players to set',
          icon: '⚡',
          action: () => navigation.navigate('Lineup' as never),
          color: '#ef4444',
          urgent: true
        },
        {
          id: 'waivers',
          title: 'Waiver Wire',
          subtitle: '5 new players',
          icon: '🔄',
          action: () => navigation.navigate('Waivers' as never),
          color: '#3b82f6'
        },
        {
          id: 'trades',
          title: 'Trade Center',
          subtitle: '1 pending offer',
          icon: '🤝',
          action: () => navigation.navigate('Trades' as never),
          color: '#10b981',
          urgent: true
        },
        {
          id: 'research',
          title: 'Player Research',
          subtitle: 'Weekly rankings',
          icon: '📊',
          action: () => navigation.navigate('Research' as never),
          color: '#8b5cf6'
        }
      ];
      setQuickActions(actions);

      // Load news items
      const news: NewsItem[] = [
        {
          id: 'news1',
          title: 'Mahomes questionable for Sunday',
          summary: 'Ankle injury may limit playtime',
          timestamp: '2 hours ago',
          category: 'injury',
          impact: 'high',
          playerId: 'mahomes'
        },
        {
          id: 'news2',
          title: 'Jonathan Taylor activated from IR',
          summary: 'Expected to play significant snaps',
          timestamp: '4 hours ago',
          category: 'news',
          impact: 'medium'
        }
      ];
      setNewsItems(news);

      // Initialize widgets
      const initialWidgets: DashboardWidget[] = DEFAULT_WIDGETS.map(key => ({
        id: key,
        title: getWidgetTitle(key),
        type: getWidgetType(key),
        data: getWidgetData(key),
        lastUpdated: new Date().toISOString(),
        refreshing: false
      }));
      setWidgets(initialWidgets);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    }
  };

  const refreshData = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadDashboardData();
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  }, []);

  const getWidgetTitle = (key: WidgetKey): string => {
    const titles = {
      myLeagues: 'My Leagues',
      upcoming: 'Upcoming Games',
      scoreboard: 'Live Scores',
      waivers: 'Waiver Activity',
      tips: 'Fantasy Tips'
    };
    return titles[key] || key;
  };

  const getWidgetType = (key: WidgetKey): DashboardWidget['type'] => {
    const types = {
      myLeagues: 'list' as const,
      upcoming: 'card' as const,
      scoreboard: 'score' as const,
      waivers: 'list' as const,
      tips: 'news' as const
    };
    return types[key] || 'card';
  };

  const getWidgetData = (key: WidgetKey) => {
    switch (key) {
      case 'myLeagues':
        return [
          { id: '1', name: 'Work League', status: 'active', rank: 3, record: '7-3' },
          { id: '2', name: 'Friends League', status: 'active', rank: 1, record: '8-2' },
          { id: '3', name: 'Family League', status: 'completed', rank: 2, record: '9-5' }
        ];
      case 'upcoming':
        return [
          { player: 'Josh Allen', opponent: 'vs MIA', time: 'Sun 1:00 PM' },
          { player: 'Christian McCaffrey', opponent: '@ SEA', time: 'Sun 4:05 PM' }
        ];
      case 'scoreboard':
        return [
          { matchup: 'You vs Mike', score: '87.4 - 72.1', status: 'winning' },
          { matchup: 'Sarah vs Tom', score: '94.2 - 89.7', status: 'close' }
        ];
      case 'waivers':
        return [
          { player: 'Gus Edwards', status: 'pending', priority: 3 },
          { player: 'Tyler Boyd', status: 'won', priority: 1 }
        ];
      case 'tips':
        return [
          { tip: 'Start players facing weak defenses', category: 'strategy' },
          { tip: 'Monitor injury reports Friday', category: 'lineup' }
        ];
      default:
        return [];
    }
  };

  const toggleWidgetVisibility = (widgetKey: WidgetKey) => {
    const newVisible = new Set(visibleWidgets);
    if (newVisible.has(widgetKey)) {
      newVisible.delete(widgetKey);
    } else {
      newVisible.add(widgetKey);
    }
    setVisibleWidgets(newVisible);
  };

  const saveLayout = () => {
    dashboardUtils.saveLayout(widgetOrder);
    setCustomizationMode(false);
    Alert.alert('Success', 'Dashboard layout saved');
  };

  const resetLayout = () => {
    setWidgetOrder(DEFAULT_WIDGETS);
    setVisibleWidgets(new Set(DEFAULT_WIDGETS));
    Alert.alert('Reset', 'Dashboard layout reset to default');
  };

  const renderQuickActions = () => (
    <View style={styles.quickActionsContainer}>
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickActionsList}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[
              styles.quickActionCard,
              { borderLeftColor: action.color },
              action.urgent && styles.urgentAction
            ]}
            onPress={action.action}
          >
            <Text style={styles.quickActionIcon}>{action.icon}</Text>
            <Text style={styles.quickActionTitle}>{action.title}</Text>
            <Text style={styles.quickActionSubtitle}>{action.subtitle}</Text>
            {action.urgent && <View style={styles.urgentIndicator} />}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  const renderUserMetrics = () => {
    if (!userMetrics) return null;

    return (
      <View style={styles.metricsContainer}>
        <Text style={styles.sectionTitle}>Your Performance</Text>
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{userMetrics.totalLeagues}</Text>
            <Text style={styles.metricLabel}>Leagues</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>#{userMetrics.weeklyRank}</Text>
            <Text style={styles.metricLabel}>Week Rank</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{userMetrics.winPercentage}%</Text>
            <Text style={styles.metricLabel}>Win Rate</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{userMetrics.seasonPoints}</Text>
            <Text style={styles.metricLabel}>Points</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderNews = () => (
    <View style={styles.newsContainer}>
      <Text style={styles.sectionTitle}>Latest News</Text>
      {newsItems.map((item) => (
        <TouchableOpacity key={item.id} style={styles.newsItem}>
          <View style={[styles.newsIndicator, { backgroundColor: getNewsColor(item.impact) }]} />
          <View style={styles.newsContent}>
            <Text style={styles.newsTitle}>{item.title}</Text>
            <Text style={styles.newsSummary}>{item.summary}</Text>
            <Text style={styles.newsTimestamp}>{item.timestamp}</Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const getNewsColor = (impact: NewsItem['impact']) => {
    switch (impact) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const renderWidget = (widget: DashboardWidget) => {
    if (!visibleWidgets.has(widget.id)) return null;

    return (
      <View key={widget.id} style={styles.widget}>
        <View style={styles.widgetHeader}>
          <Text style={styles.widgetTitle}>{widget.title}</Text>
          <Text style={styles.widgetTimestamp}>
            {new Date(widget.lastUpdated).toLocaleTimeString()}
          </Text>
        </View>

        {widget.refreshing ? (
          <ActivityIndicator size="small" color="#3b82f6" style={styles.widgetLoader} />
        ) : (
          <View style={styles.widgetContent}>
            {widget.type === 'list' && renderListWidget(widget)}
            {widget.type === 'card' && renderCardWidget(widget)}
            {widget.type === 'score' && renderScoreWidget(widget)}
            {widget.type === 'news' && renderNewsWidget(widget)}
          </View>
        )}
      </View>
    );
  };

  const renderListWidget = (widget: DashboardWidget) => (
    <View>
      {widget.data.map((item: any, index: number) => (
        <View key={index} style={styles.listItem}>
          <Text style={styles.listItemTitle}>{item.name || item.player}</Text>
          <Text style={styles.listItemSubtitle}>
            {item.record || item.status || item.opponent}
          </Text>
        </View>
      ))}
    </View>
  );

  const renderCardWidget = (widget: DashboardWidget) => (
    <View>
      {widget.data.map((item: any, index: number) => (
        <View key={index} style={styles.cardItem}>
          <Text style={styles.cardTitle}>{item.player || item.title}</Text>
          <Text style={styles.cardSubtitle}>{item.opponent || item.time}</Text>
        </View>
      ))}
    </View>
  );

  const renderScoreWidget = (widget: DashboardWidget) => (
    <View>
      {widget.data.map((item: any, index: number) => (
        <View key={index} style={styles.scoreItem}>
          <Text style={styles.scoreMatchup}>{item.matchup}</Text>
          <Text style={[
            styles.scoreValue,
            { color: item.status === 'winning' ? '#10b981' : '#6b7280' }
          ]}>
            {item.score}
          </Text>
        </View>
      ))}
    </View>
  );

  const renderNewsWidget = (widget: DashboardWidget) => (
    <View>
      {widget.data.map((item: any, index: number) => (
        <Text key={index} style={styles.tipText}>
          💡 {item.tip}
        </Text>
      ))}
    </View>
  );

  const renderCustomizationModal = () => (
    <Modal
      visible={customizationMode}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Customize Dashboard</Text>
          <TouchableOpacity onPress={() => setCustomizationMode(false)}>
            <Text style={styles.modalClose}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          <Text style={styles.modalSectionTitle}>Visible Widgets</Text>
          {DEFAULT_WIDGETS.map((key) => (
            <TouchableOpacity
              key={key}
              style={styles.toggleItem}
              onPress={() => toggleWidgetVisibility(key)}
            >
              <Text style={styles.toggleLabel}>{getWidgetTitle(key)}</Text>
              <View style={[
                styles.toggle,
                visibleWidgets.has(key) && styles.toggleActive
              ]}>
                {visibleWidgets.has(key) && <View style={styles.toggleIndicator} />}
              </View>
            </TouchableOpacity>
          ))}

          <View style={styles.modalButtons}>
            <TouchableOpacity style={styles.primaryButton} onPress={saveLayout}>
              <Text style={styles.primaryButtonText}>Save Layout</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryButton} onPress={resetLayout}>
              <Text style={styles.secondaryButtonText}>Reset to Default</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Dashboard</Text>
          <Text style={styles.subtitle}>
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.customizeButton}
          onPress={() => setCustomizationMode(true)}
        >
          <Text style={styles.customizeButtonText}>⚙️</Text>
        </TouchableOpacity>
      </View>

      {/* Main Content */}
      <ScrollView
        style={styles.scrollContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderUserMetrics()}
        {renderQuickActions()}
        {renderNews()}

        {/* Widgets */}
        <View style={styles.widgetsContainer}>
          <Text style={styles.sectionTitle}>Dashboard Widgets</Text>
          {widgets.filter(w => visibleWidgets.has(w.id)).map(renderWidget)}
        </View>
      </ScrollView>

      {renderCustomizationModal()}
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
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  customizeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  customizeButtonText: {
    fontSize: 18,
  },
  scrollContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
  },

  // User Metrics
  metricsContainer: {
    padding: 20,
    backgroundColor: '#ffffff',
    marginBottom: 8,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#3b82f6',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748b',
  },

  // Quick Actions
  quickActionsContainer: {
    backgroundColor: '#ffffff',
    paddingVertical: 20,
    marginBottom: 8,
  },
  quickActionsList: {
    paddingLeft: 20,
  },
  quickActionCard: {
    width: 140,
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    borderLeftWidth: 4,
    position: 'relative',
  },
  urgentAction: {
    backgroundColor: '#fef2f2',
  },
  urgentIndicator: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ef4444',
  },
  quickActionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  quickActionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  quickActionSubtitle: {
    fontSize: 12,
    color: '#64748b',
  },

  // News
  newsContainer: {
    backgroundColor: '#ffffff',
    padding: 20,
    marginBottom: 8,
  },
  newsItem: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  newsIndicator: {
    width: 4,
    borderRadius: 2,
    marginRight: 12,
  },
  newsContent: {
    flex: 1,
  },
  newsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  newsSummary: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 4,
  },
  newsTimestamp: {
    fontSize: 11,
    color: '#94a3b8',
  },

  // Widgets
  widgetsContainer: {
    padding: 20,
  },
  widget: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  widgetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  widgetTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  widgetTimestamp: {
    fontSize: 11,
    color: '#94a3b8',
  },
  widgetLoader: {
    paddingVertical: 20,
  },
  widgetContent: {
    // Base widget content styles
  },

  // List widget styles
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  listItemTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1e293b',
  },
  listItemSubtitle: {
    fontSize: 13,
    color: '#64748b',
  },

  // Card widget styles
  cardItem: {
    paddingVertical: 8,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1e293b',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#64748b',
  },

  // Score widget styles
  scoreItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  scoreMatchup: {
    fontSize: 14,
    color: '#1e293b',
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '600',
  },

  // Tips widget styles
  tipText: {
    fontSize: 13,
    color: '#64748b',
    lineHeight: 18,
    marginBottom: 8,
  },

  // Modal styles
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
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 16,
  },
  toggleItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  toggleLabel: {
    fontSize: 16,
    color: '#1e293b',
  },
  toggle: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#e2e8f0',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  toggleActive: {
    backgroundColor: '#3b82f6',
  },
  toggleIndicator: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#ffffff',
    alignSelf: 'flex-end',
  },
  modalButtons: {
    marginTop: 32,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#d1d5db',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '500',
  },
});