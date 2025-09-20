import { create } from 'zustand';
import { persist } from 'zustand/middleware';

function resolveDefaultApiBaseUrl(): string {
  if (typeof process !== 'undefined' && process?.env) {
    const env = process.env as Record<string, string | undefined>;
    const candidates = [
      env.NEXT_PUBLIC_API_BASE_URL,
      env.EXPO_PUBLIC_API_BASE_URL,
      env.API_BASE_URL,
      env.REACT_NATIVE_API_BASE_URL,
    ];

    for (const value of candidates) {
      if (typeof value === 'string' && value.trim().length > 0) {
        return value.trim();
      }
    }
  }

  return '/api';
}

export interface AppSettings {
  apiBaseUrl: string;
  timeout: number;
  retryAttempts: number;
  debugMode: boolean;
  enableAnalytics: boolean;
  enablePushNotifications: boolean;
  maintenanceMode: boolean;
  version: string;
}

export interface ConnectionState {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingRequests: number;
  serverStatus: 'healthy' | 'degraded' | 'down' | 'unknown';
}

export interface NavigationState {
  currentRoute: string;
  previousRoute: string;
  routeHistory: string[];
  isNavigating: boolean;
}

interface AppState {
  theme: 'light' | 'dark';
  settings: AppSettings;
  connection: ConnectionState;
  navigation: NavigationState;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
  isOnline: boolean;
  notifications: Array<{
    id: string;
    type: 'info' | 'warning' | 'error' | 'success';
    title: string;
    message: string;
    timestamp: Date;
    read: boolean;
  }>;

  // Actions
  setTheme: (theme: 'light' | 'dark') => void;
  setSettings: (settings: Partial<AppSettings>) => void;
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
  setConnectionState: (connection: Partial<ConnectionState>) => void;
  setOnlineStatus: (isOnline: boolean) => void;
  setServerStatus: (status: ConnectionState['serverStatus']) => void;
  updateLastSync: () => void;
  incrementPendingRequests: () => void;
  decrementPendingRequests: () => void;
  setNavigation: (navigation: Partial<NavigationState>) => void;
  navigateTo: (route: string) => void;
  setInitialized: (initialized: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  clearState: () => void;
}

const defaultSettings: AppSettings = {
  apiBaseUrl: resolveDefaultApiBaseUrl(),
  timeout: 30000,
  retryAttempts: 3,
  debugMode: process.env.NODE_ENV === 'development',
  enableAnalytics: true,
  enablePushNotifications: true,
  maintenanceMode: false,
  version: '1.0.0'
};

const defaultConnection: ConnectionState = {
  isOnline: true,
  lastSyncTime: null,
  pendingRequests: 0,
  serverStatus: 'unknown'
};

const defaultNavigation: NavigationState = {
  currentRoute: '/',
  previousRoute: '/',
  routeHistory: ['/'],
  isNavigating: false
};

export const createAppStore = () => create<AppState>()(
  persist(
    (set, get) => ({
      theme: 'light',
      settings: defaultSettings,
      connection: defaultConnection,
      navigation: defaultNavigation,
      isInitialized: false,
      isLoading: false,
      error: null,
      isOnline: true,
      notifications: [],

      setTheme: (theme) => set({ theme }),

      setSettings: (settings) => set((state) => ({
        settings: { ...state.settings, ...settings }
      })),

      updateSetting: (key, value) => set((state) => ({
        settings: { ...state.settings, [key]: value }
      })),

      setConnectionState: (connection) => set((state) => ({
        connection: { ...state.connection, ...connection }
      })),

      setOnlineStatus: (isOnline) => set((state) => ({
        isOnline,
        connection: { ...state.connection, isOnline }
      })),

      setServerStatus: (serverStatus) => set((state) => ({
        connection: { ...state.connection, serverStatus }
      })),

      updateLastSync: () => set((state) => ({
        connection: { ...state.connection, lastSyncTime: new Date() }
      })),

      incrementPendingRequests: () => set((state) => ({
        connection: {
          ...state.connection,
          pendingRequests: state.connection.pendingRequests + 1
        }
      })),

      decrementPendingRequests: () => set((state) => ({
        connection: {
          ...state.connection,
          pendingRequests: Math.max(0, state.connection.pendingRequests - 1)
        }
      })),

      setNavigation: (navigation) => set((state) => ({
        navigation: { ...state.navigation, ...navigation }
      })),

      navigateTo: (route) => set((state) => ({
        navigation: {
          ...state.navigation,
          previousRoute: state.navigation.currentRoute,
          currentRoute: route,
          routeHistory: [...state.navigation.routeHistory, route].slice(-10) // Keep last 10 routes
        }
      })),

      setInitialized: (initialized) => set({ isInitialized: initialized }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      addNotification: (notification) => {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        set((state) => ({
          notifications: [...state.notifications, {
            ...notification,
            id,
            timestamp: new Date(),
            read: false
          }]
        }));
      },

      markNotificationRead: (id) => set((state) => ({
        notifications: state.notifications.map(notif =>
          notif.id === id ? { ...notif, read: true } : notif
        )
      })),

      removeNotification: (id) => set((state) => ({
        notifications: state.notifications.filter(notif => notif.id !== id)
      })),

      clearAllNotifications: () => set({ notifications: [] }),

      clearState: () => set({
        settings: defaultSettings,
        connection: defaultConnection,
        navigation: defaultNavigation,
        isInitialized: false,
        isLoading: false,
        error: null,
        notifications: []
      })
    }),
    {
      name: 'app-store',
      // Persist settings and some navigation state
      partialize: (state) => ({
        settings: state.settings,
        navigation: {
          currentRoute: state.navigation.currentRoute,
          routeHistory: state.navigation.routeHistory.slice(-5) // Only persist last 5 routes
        },
        isInitialized: state.isInitialized
      })
    }
  )
);

// Export singleton instance for easy usage
export const useAppStore = createAppStore();

// Helper functions for app operations
export const appStoreHelpers = {
  isAppOnline: (connection: ConnectionState) => connection.isOnline,

  hasActivePendingRequests: (connection: ConnectionState) =>
    connection.pendingRequests > 0,

  getTimeSinceLastSync: (connection: ConnectionState) => {
    if (!connection.lastSyncTime) return null;
    return Date.now() - connection.lastSyncTime.getTime();
  },

  isServerHealthy: (connection: ConnectionState) =>
    connection.serverStatus === 'healthy',

  getUnreadNotificationCount: (notifications: AppState['notifications']) =>
    notifications.filter(notif => !notif.read).length,

  getNotificationsByType: (notifications: AppState['notifications'], type: string) =>
    notifications.filter(notif => notif.type === type),

  getRecentNotifications: (notifications: AppState['notifications'], limit = 5) =>
    notifications
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit),

  canNavigateBack: (navigation: NavigationState) =>
    navigation.routeHistory.length > 1,

  getPreviousRoute: (navigation: NavigationState) =>
    navigation.routeHistory[navigation.routeHistory.length - 2] || '/',

  isCurrentRoute: (navigation: NavigationState, route: string) =>
    navigation.currentRoute === route,

  shouldShowMaintenance: (settings: AppSettings) =>
    settings.maintenanceMode,

  isDebugEnabled: (settings: AppSettings) =>
    settings.debugMode || process.env.NODE_ENV === 'development'
};
