import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Modal,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  value: number;
}

interface Trade {
  id: string;
  from_team: string;
  to_team: string;
  offer_players: Player[];
  request_players: Player[];
  status: 'pending' | 'accepted' | 'rejected' | 'countered';
  created_at: Date;
  expires_at: Date;
  fairness_score: number;
}

// Mock data
const MOCK_TRADES: Trade[] = [
  {
    id: 't1',
    from_team: 'Team Alpha',
    to_team: 'My Team',
    offer_players: [
      { id: 'p1', name: 'LeBron James', position: 'SF', team: 'LAL', value: 95 },
    ],
    request_players: [
      { id: 'p2', name: 'Stephen Curry', position: 'PG', team: 'GSW', value: 92 },
    ],
    status: 'pending',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    expires_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000), // 5 days from now
    fairness_score: 88,
  },
  {
    id: 't2',
    from_team: 'My Team',
    to_team: 'Team Beta',
    offer_players: [
      { id: 'p3', name: 'Kevin Durant', position: 'PF', team: 'PHX', value: 90 },
    ],
    request_players: [
      { id: 'p4', name: 'Jayson Tatum', position: 'SF', team: 'BOS', value: 88 },
      { id: 'p5', name: 'Role Player', position: 'PG', team: 'BOS', value: 15 },
    ],
    status: 'countered',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
    expires_at: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000), // 4 days from now
    fairness_score: 72,
  },
];

export default function TradesScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { leagueId } = route.params as { leagueId: string };

  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [showTradeDetail, setShowTradeDetail] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    // Mock refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleTradeAction = async (tradeId: string, action: 'accept' | 'reject' | 'counter') => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    setTrades(prevTrades =>
      prevTrades.map(trade =>
        trade.id === tradeId
          ? { ...trade, status: action === 'accept' ? 'accepted' : action === 'reject' ? 'rejected' : 'countered' }
          : trade
      )
    );

    let message = '';
    switch (action) {
      case 'accept':
        message = 'Trade accepted! Players will be transferred.';
        break;
      case 'reject':
        message = 'Trade rejected.';
        break;
      case 'counter':
        message = 'Counter-offer sent!';
        break;
    }

    Alert.alert('Trade Action', message);
    setShowTradeDetail(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'accepted': return '#059669';
      case 'rejected': return '#ef4444';
      case 'countered': return '#2563eb';
      default: return '#64748b';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return 'time';
      case 'accepted': return 'checkmark-circle';
      case 'rejected': return 'close-circle';
      case 'countered': return 'swap-horizontal';
      default: return 'help-circle';
    }
  };

  const getFairnessColor = (score: number) => {
    if (score >= 85) return '#059669';
    if (score >= 70) return '#f59e0b';
    return '#ef4444';
  };

  const getFairnessLabel = (score: number) => {
    if (score >= 85) return 'Fair';
    if (score >= 70) return 'Uneven';
    return 'Unfair';
  };

  const formatTimeRemaining = (expiresAt: Date) => {
    const now = new Date();
    const diff = expiresAt.getTime() - now.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h`;
    return 'Expiring soon';
  };

  const renderPlayer = (player: Player, isOffering: boolean) => (
    <View key={player.id} style={styles.playerCard}>
      <View style={styles.playerInfo}>
        <Text style={styles.playerName}>{player.name}</Text>
        <Text style={styles.playerDetails}>
          {player.position} • {player.team}
        </Text>
      </View>
      <View style={styles.playerValue}>
        <Text style={styles.playerValueText}>Value: {player.value}</Text>
      </View>
    </View>
  );

  const renderTrade = (trade: Trade) => {
    const isIncoming = trade.to_team === 'My Team';
    const totalOfferValue = trade.offer_players.reduce((sum, p) => sum + p.value, 0);
    const totalRequestValue = trade.request_players.reduce((sum, p) => sum + p.value, 0);

    return (
      <TouchableOpacity
        key={trade.id}
        style={styles.tradeCard}
        onPress={() => {
          setSelectedTrade(trade);
          setShowTradeDetail(true);
        }}
      >
        <View style={styles.tradeHeader}>
          <View style={styles.tradeTitle}>
            <Text style={styles.tradeFromTo}>
              {isIncoming ? trade.from_team : trade.to_team}
            </Text>
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(trade.status) }]}>
              <Ionicons name={getStatusIcon(trade.status)} size={12} color="#fff" />
              <Text style={styles.statusText}>{trade.status.toUpperCase()}</Text>
            </View>
          </View>
          <Text style={styles.timeRemaining}>
            {formatTimeRemaining(trade.expires_at)}
          </Text>
        </View>

        <View style={styles.tradeContent}>
          <View style={styles.tradeSection}>
            <Text style={styles.tradeSectionTitle}>
              {isIncoming ? 'Receiving' : 'Giving'}
            </Text>
            <View style={styles.tradeValue}>
              <Text style={styles.tradeValueText}>
                Value: {isIncoming ? totalOfferValue : totalRequestValue}
              </Text>
            </View>
          </View>

          <View style={styles.tradeArrow}>
            <Ionicons name="arrow-forward" size={20} color="#64748b" />
          </View>

          <View style={styles.tradeSection}>
            <Text style={styles.tradeSectionTitle}>
              {isIncoming ? 'Giving' : 'Receiving'}
            </Text>
            <View style={styles.tradeValue}>
              <Text style={styles.tradeValueText}>
                Value: {isIncoming ? totalRequestValue : totalOfferValue}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.tradeFooter}>
          <View style={[styles.fairnessBadge, { backgroundColor: getFairnessColor(trade.fairness_score) }]}>
            <Text style={styles.fairnessText}>
              {getFairnessLabel(trade.fairness_score)} ({trade.fairness_score}/100)
            </Text>
          </View>
          {trade.status === 'pending' && isIncoming && (
            <Text style={styles.actionHint}>Tap to respond</Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderTradeDetailModal = () => {
    if (!selectedTrade) return null;

    const isIncoming = selectedTrade.to_team === 'My Team';
    const canRespond = selectedTrade.status === 'pending' && isIncoming;

    return (
      <Modal
        visible={showTradeDetail}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowTradeDetail(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Trade Details</Text>
            <TouchableOpacity onPress={() => setShowTradeDetail(false)}>
              <Ionicons name="close" size={24} color="#64748b" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>Trade Overview</Text>
              <Text style={styles.modalTeams}>
                {selectedTrade.from_team} → {selectedTrade.to_team}
              </Text>
              <Text style={styles.modalExpiry}>
                Expires: {formatTimeRemaining(selectedTrade.expires_at)}
              </Text>
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>You Receive</Text>
              {(isIncoming ? selectedTrade.offer_players : selectedTrade.request_players).map(player =>
                renderPlayer(player, false)
              )}
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>You Give</Text>
              {(isIncoming ? selectedTrade.request_players : selectedTrade.offer_players).map(player =>
                renderPlayer(player, true)
              )}
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>Fairness Analysis</Text>
              <View style={[styles.fairnessCard, { borderColor: getFairnessColor(selectedTrade.fairness_score) }]}>
                <Text style={[styles.fairnessScore, { color: getFairnessColor(selectedTrade.fairness_score) }]}>
                  {selectedTrade.fairness_score}/100
                </Text>
                <Text style={styles.fairnessLabel}>
                  {getFairnessLabel(selectedTrade.fairness_score)}
                </Text>
              </View>
            </View>
          </ScrollView>

          {canRespond && (
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.actionButton, styles.rejectButton]}
                onPress={() => handleTradeAction(selectedTrade.id, 'reject')}
              >
                <Ionicons name="close" size={20} color="#fff" />
                <Text style={styles.actionButtonText}>Reject</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.counterButton]}
                onPress={() => handleTradeAction(selectedTrade.id, 'counter')}
              >
                <Ionicons name="swap-horizontal" size={20} color="#fff" />
                <Text style={styles.actionButtonText}>Counter</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.acceptButton]}
                onPress={() => handleTradeAction(selectedTrade.id, 'accept')}
              >
                <Ionicons name="checkmark" size={20} color="#fff" />
                <Text style={styles.actionButtonText}>Accept</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </Modal>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Trade Center</Text>
          <TouchableOpacity style={styles.newTradeButton}>
            <Ionicons name="add" size={20} color="#fff" />
            <Text style={styles.newTradeText}>New Trade</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.content}>
          {trades.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="swap-horizontal" size={60} color="#cbd5e1" />
              <Text style={styles.emptyTitle}>No Trades</Text>
              <Text style={styles.emptyDescription}>
                Start negotiating with other teams to improve your roster!
              </Text>
            </View>
          ) : (
            <View style={styles.tradesList}>
              {trades.map(renderTrade)}
            </View>
          )}
        </View>
      </ScrollView>

      {renderTradeDetailModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  newTradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2563eb',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  newTradeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    padding: 16,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#64748b',
    marginTop: 16,
  },
  emptyDescription: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 40,
  },
  tradesList: {
    gap: 16,
  },
  tradeCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  tradeTitle: {
    flex: 1,
    gap: 8,
  },
  tradeFromTo: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
    alignSelf: 'flex-start',
  },
  statusText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  timeRemaining: {
    fontSize: 12,
    color: '#64748b',
  },
  tradeContent: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  tradeSection: {
    flex: 1,
    alignItems: 'center',
  },
  tradeSectionTitle: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 4,
  },
  tradeValue: {
    backgroundColor: '#f1f5f9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  tradeValueText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1e293b',
  },
  tradeArrow: {
    marginHorizontal: 16,
  },
  tradeFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  fairnessBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  fairnessText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  actionHint: {
    fontSize: 12,
    color: '#2563eb',
    fontWeight: '500',
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  modalSection: {
    marginBottom: 24,
  },
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
  },
  modalTeams: {
    fontSize: 14,
    color: '#64748b',
  },
  modalExpiry: {
    fontSize: 12,
    color: '#f59e0b',
    marginTop: 4,
  },
  playerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  playerDetails: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  playerValue: {
    marginLeft: 8,
  },
  playerValueText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#059669',
  },
  fairnessCard: {
    borderWidth: 2,
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  fairnessScore: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  fairnessLabel: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  modalActions: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 4,
  },
  rejectButton: {
    backgroundColor: '#ef4444',
  },
  counterButton: {
    backgroundColor: '#f59e0b',
  },
  acceptButton: {
    backgroundColor: '#059669',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});