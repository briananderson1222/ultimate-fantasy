import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { LeaguesService, httpClient } from '@ultimate-fantasy/api-client';

export default function LeaguesScreen() {
  const [inviteLink, setInviteLink] = useState('');

  const leaguesService = LeaguesService.create(httpClient);

  const leagues = useQuery({
    queryKey: ['myLeagues'],
    queryFn: () => leaguesService.getMyLeagues(),
  });

  const handleJoinLeague = () => {
    const v = inviteLink.trim();
    if (!v) return;

    try {
      let leagueId = '';
      if (/^https?:\/\//i.test(v)) {
        // Extract league ID from URL
        const url = new URL(v);
        const parts = url.pathname.split('/').filter(Boolean);
        const idx = parts.indexOf('leagues');
        if (idx >= 0 && parts[idx + 1]) leagueId = parts[idx + 1];
      } else if (/^[0-9a-fA-F-]{8,}$/.test(v)) {
        // Direct league ID
        leagueId = v;
      }

      if (!leagueId) {
        Alert.alert('Error', 'Please enter a valid invite link or league ID');
        return;
      }

      // Navigate to league details (would need navigation prop)
      Alert.alert('Success', `Would navigate to league: ${leagueId}`);
      setInviteLink('');
    } catch (e: any) {
      Alert.alert('Error', String(e?.message || e));
    }
  };

  if (leagues.isLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading leagues...</Text>
        </View>
      </View>
    );
  }

  if (leagues.isError) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            {(leagues.error as Error)?.message || 'Failed to load leagues'}
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => leagues.refetch()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        {/* My Leagues Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Leagues</Text>

          {leagues.data && leagues.data.items.length > 0 ? (
            <View style={styles.leaguesList}>
              {leagues.data.items.map((league: any) => (
                <TouchableOpacity key={league.team_id} style={styles.leagueItem}>
                  <View style={styles.leagueInfo}>
                    <Text style={styles.leagueName}>{league.name}</Text>
                    <Text style={styles.leagueSeason}>Season {league.season}</Text>
                  </View>
                  <Text style={styles.viewLink}>View League</Text>
                </TouchableOpacity>
              ))}
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateTitle}>No leagues yet</Text>
              <Text style={styles.emptyStateDescription}>
                Create your first league or join one using an invite link.
              </Text>
            </View>
          )}
        </View>

        {/* Join League Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Join a League</Text>
          <Text style={styles.sectionDescription}>
            Have an invite link? Paste it here to join the league.
          </Text>

          <View style={styles.joinForm}>
            <TextInput
              style={styles.textInput}
              value={inviteLink}
              onChangeText={setInviteLink}
              placeholder="https://ultimatefantasy.app/leagues/abc-123 or league-id"
              placeholderTextColor="#9ca3af"
              multiline={false}
            />
            <TouchableOpacity
              style={[styles.joinButton, !inviteLink.trim() && styles.joinButtonDisabled]}
              onPress={handleJoinLeague}
              disabled={!inviteLink.trim()}
            >
              <Text style={styles.joinButtonText}>Join League</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContainer: {
    padding: 16,
    gap: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#64748b',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#dc2626',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 16,
  },
  leaguesList: {
    gap: 12,
  },
  leagueItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  leagueInfo: {
    flex: 1,
  },
  leagueName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1e293b',
  },
  leagueSeason: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  viewLink: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  emptyStateTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 8,
  },
  emptyStateDescription: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
  },
  joinForm: {
    gap: 12,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 6,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: '#374151',
    backgroundColor: '#ffffff',
  },
  joinButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    alignItems: 'center',
  },
  joinButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  joinButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});