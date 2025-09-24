import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { ApiClient } from './ApiClient';

export interface SyncableData {
  id: string;
  type: 'league' | 'lineup' | 'player' | 'scoring' | 'trade';
  data: any;
  lastModified: number;
  priority: 'high' | 'medium' | 'low';
  requiresSync: boolean;
}

export interface SyncStatus {
  isOnline: boolean;
  lastSyncTime: number;
  pendingSync: number;
  syncInProgress: boolean;
  syncErrors: string[];
}

export interface SyncConfig {
  maxRetries: number;
  retryDelay: number;
  syncInterval: number;
  maxOfflineData: number;
  enableBackgroundSync: boolean;
}

export class OfflineSync {
  private static instance: OfflineSync;
  private apiClient: ApiClient;
  private config: SyncConfig;
  private syncStatus: SyncStatus;
  private syncQueue: SyncableData[] = [];
  private syncTimer?: NodeJS.Timeout;

  private constructor() {
    this.apiClient = ApiClient.getInstance();
    this.config = {
      maxRetries: 3,
      retryDelay: 5000,
      syncInterval: 30000,
      maxOfflineData: 1000,
      enableBackgroundSync: true
    };
    this.syncStatus = {
      isOnline: true,
      lastSyncTime: 0,
      pendingSync: 0,
      syncInProgress: false,
      syncErrors: []
    };
    this.initialize();
  }

  public static getInstance(): OfflineSync {
    if (!OfflineSync.instance) {
      OfflineSync.instance = new OfflineSync();
    }
    return OfflineSync.instance;
  }

  private async initialize(): Promise<void> {
    await this.loadSyncQueue();
    await this.loadSyncStatus();
    this.setupNetworkListener();
    if (this.config.enableBackgroundSync) {
      this.startBackgroundSync();
    }
  }

  private setupNetworkListener(): void {
    NetInfo.addEventListener(state => {
      const wasOffline = !this.syncStatus.isOnline;
      this.syncStatus.isOnline = state.isConnected ?? false;

      if (wasOffline && this.syncStatus.isOnline) {
        this.triggerSync();
      }
    });
  }

  private startBackgroundSync(): void {
    this.syncTimer = setInterval(() => {
      if (this.syncStatus.isOnline && !this.syncStatus.syncInProgress && this.syncQueue.length > 0) {
        this.triggerSync();
      }
    }, this.config.syncInterval);
  }

  public async queueForSync(data: Omit<SyncableData, 'id' | 'lastModified' | 'requiresSync'>): Promise<void> {
    const syncData: SyncableData = {
      id: `${data.type}_${Date.now()}_${Math.random()}`,
      ...data,
      lastModified: Date.now(),
      requiresSync: true
    };

    this.syncQueue.push(syncData);
    this.syncStatus.pendingSync = this.syncQueue.filter(item => item.requiresSync).length;

    await this.saveSyncQueue();
    await this.saveSyncStatus();

    if (this.syncStatus.isOnline && !this.syncStatus.syncInProgress) {
      this.triggerSync();
    }
  }

  public async triggerSync(): Promise<void> {
    if (this.syncStatus.syncInProgress || !this.syncStatus.isOnline) {
      return;
    }

    this.syncStatus.syncInProgress = true;
    this.syncStatus.syncErrors = [];

    try {
      const prioritySorted = this.syncQueue
        .filter(item => item.requiresSync)
        .sort((a, b) => {
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority] || a.lastModified - b.lastModified;
        });

      for (const item of prioritySorted) {
        await this.syncItem(item);
      }

      this.syncStatus.lastSyncTime = Date.now();
      this.syncStatus.pendingSync = this.syncQueue.filter(item => item.requiresSync).length;

    } catch (error) {
      console.error('Sync failed:', error);
      this.syncStatus.syncErrors.push(error instanceof Error ? error.message : 'Unknown sync error');
    } finally {
      this.syncStatus.syncInProgress = false;
      await this.saveSyncStatus();
    }
  }

  private async syncItem(item: SyncableData, retryCount = 0): Promise<void> {
    try {
      switch (item.type) {
        case 'league':
          await this.syncLeague(item);
          break;
        case 'lineup':
          await this.syncLineup(item);
          break;
        case 'player':
          await this.syncPlayer(item);
          break;
        case 'scoring':
          await this.syncScoring(item);
          break;
        case 'trade':
          await this.syncTrade(item);
          break;
      }

      item.requiresSync = false;
      await this.saveSyncQueue();

    } catch (error) {
      if (retryCount < this.config.maxRetries) {
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
        return this.syncItem(item, retryCount + 1);
      }

      console.error(`Failed to sync ${item.type} after ${this.config.maxRetries} retries:`, error);
      this.syncStatus.syncErrors.push(`${item.type}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async syncLeague(item: SyncableData): Promise<void> {
    const { action, leagueData } = item.data;

    switch (action) {
      case 'create':
        await this.apiClient.post('/leagues', leagueData);
        break;
      case 'update':
        await this.apiClient.put(`/leagues/${leagueData.id}`, leagueData);
        break;
      case 'join':
        await this.apiClient.post(`/leagues/${leagueData.id}/join`, { userId: leagueData.userId });
        break;
      case 'leave':
        await this.apiClient.post(`/leagues/${leagueData.id}/leave`, { userId: leagueData.userId });
        break;
    }
  }

  private async syncLineup(item: SyncableData): Promise<void> {
    const { action, lineupData } = item.data;

    switch (action) {
      case 'update':
        await this.apiClient.put(`/lineups/${lineupData.id}`, lineupData);
        break;
      case 'submit':
        await this.apiClient.post(`/lineups/${lineupData.id}/submit`, lineupData);
        break;
    }
  }

  private async syncPlayer(item: SyncableData): Promise<void> {
    const { action, playerData } = item.data;

    switch (action) {
      case 'add':
        await this.apiClient.post(`/teams/${playerData.teamId}/players`, playerData);
        break;
      case 'remove':
        await this.apiClient.delete(`/teams/${playerData.teamId}/players/${playerData.playerId}`);
        break;
      case 'trade':
        await this.apiClient.post('/trades', playerData);
        break;
    }
  }

  private async syncScoring(item: SyncableData): Promise<void> {
    const { action, scoringData } = item.data;

    switch (action) {
      case 'update':
        await this.apiClient.put(`/scoring/${scoringData.id}`, scoringData);
        break;
      case 'calculate':
        await this.apiClient.post('/scoring/calculate', scoringData);
        break;
    }
  }

  private async syncTrade(item: SyncableData): Promise<void> {
    const { action, tradeData } = item.data;

    switch (action) {
      case 'propose':
        await this.apiClient.post('/trades', tradeData);
        break;
      case 'accept':
        await this.apiClient.post(`/trades/${tradeData.id}/accept`, { userId: tradeData.userId });
        break;
      case 'reject':
        await this.apiClient.post(`/trades/${tradeData.id}/reject`, { userId: tradeData.userId });
        break;
      case 'cancel':
        await this.apiClient.delete(`/trades/${tradeData.id}`);
        break;
    }
  }

  public async getOfflineData<T>(type: string, id?: string): Promise<T | T[] | null> {
    try {
      const key = id ? `offline_${type}_${id}` : `offline_${type}`;
      const data = await AsyncStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Failed to get offline data:', error);
      return null;
    }
  }

  public async setOfflineData(type: string, data: any, id?: string): Promise<void> {
    try {
      const key = id ? `offline_${type}_${id}` : `offline_${type}`;
      await AsyncStorage.setItem(key, JSON.stringify({
        ...data,
        _offline: true,
        _lastUpdated: Date.now()
      }));
    } catch (error) {
      console.error('Failed to set offline data:', error);
    }
  }

  public async clearOfflineData(type?: string, id?: string): Promise<void> {
    try {
      if (type && id) {
        await AsyncStorage.removeItem(`offline_${type}_${id}`);
      } else if (type) {
        const keys = await AsyncStorage.getAllKeys();
        const typeKeys = keys.filter(key => key.startsWith(`offline_${type}`));
        await AsyncStorage.multiRemove(typeKeys);
      } else {
        const keys = await AsyncStorage.getAllKeys();
        const offlineKeys = keys.filter(key => key.startsWith('offline_'));
        await AsyncStorage.multiRemove(offlineKeys);
      }
    } catch (error) {
      console.error('Failed to clear offline data:', error);
    }
  }

  public getSyncStatus(): SyncStatus {
    return { ...this.syncStatus };
  }

  public async forceSyncAll(): Promise<void> {
    this.syncQueue.forEach(item => {
      item.requiresSync = true;
    });
    await this.saveSyncQueue();
    await this.triggerSync();
  }

  public async clearSyncQueue(): Promise<void> {
    this.syncQueue = [];
    this.syncStatus.pendingSync = 0;
    await this.saveSyncQueue();
    await this.saveSyncStatus();
  }

  private async loadSyncQueue(): Promise<void> {
    try {
      const data = await AsyncStorage.getItem('sync_queue');
      if (data) {
        this.syncQueue = JSON.parse(data);
        this.syncStatus.pendingSync = this.syncQueue.filter(item => item.requiresSync).length;
      }
    } catch (error) {
      console.error('Failed to load sync queue:', error);
    }
  }

  private async saveSyncQueue(): Promise<void> {
    try {
      if (this.syncQueue.length > this.config.maxOfflineData) {
        this.syncQueue = this.syncQueue
          .sort((a, b) => b.lastModified - a.lastModified)
          .slice(0, this.config.maxOfflineData);
      }
      await AsyncStorage.setItem('sync_queue', JSON.stringify(this.syncQueue));
    } catch (error) {
      console.error('Failed to save sync queue:', error);
    }
  }

  private async loadSyncStatus(): Promise<void> {
    try {
      const data = await AsyncStorage.getItem('sync_status');
      if (data) {
        const savedStatus = JSON.parse(data);
        this.syncStatus = { ...this.syncStatus, ...savedStatus, syncInProgress: false };
      }
    } catch (error) {
      console.error('Failed to load sync status:', error);
    }
  }

  private async saveSyncStatus(): Promise<void> {
    try {
      await AsyncStorage.setItem('sync_status', JSON.stringify(this.syncStatus));
    } catch (error) {
      console.error('Failed to save sync status:', error);
    }
  }

  public updateConfig(newConfig: Partial<SyncConfig>): void {
    this.config = { ...this.config, ...newConfig };

    if (this.syncTimer && newConfig.syncInterval) {
      clearInterval(this.syncTimer);
      this.startBackgroundSync();
    }
  }

  public dispose(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }
  }
}

export default OfflineSync.getInstance();