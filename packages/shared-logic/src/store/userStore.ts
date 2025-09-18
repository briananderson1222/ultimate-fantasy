import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storeEvents, STORE_EVENTS } from './storeEvents';

export interface User {
  user_id: string;
  username: string;
  display_name: string;
  avatar?: string;
  email?: string;
  metadata?: {
    team_name?: string;
    phone?: string;
    is_bot?: boolean;
  };
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: {
    trades: boolean;
    waivers: boolean;
    matchups: boolean;
    news: boolean;
  };
  dashboard: {
    widgets: string[];
    layout: Record<string, any>;
  };
}

interface UserState {
  user: User | null;
  authToken: string | null;
  preferences: UserPreferences;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setAuthToken: (token: string | null) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setPreferences: (preferences: Partial<UserPreferences>) => void;
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearState: () => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'system',
  language: 'en',
  timezone: 'America/New_York',
  notifications: {
    trades: true,
    waivers: true,
    matchups: true,
    news: false
  },
  dashboard: {
    widgets: ['myLeagues', 'upcoming', 'scoreboard', 'waivers', 'tips'],
    layout: {}
  }
};

export const createUserStore = () => create<UserState>()(
  persist(
    (set, get) => ({
      user: null,
      authToken: null,
      preferences: defaultPreferences,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => set({
        user,
        isAuthenticated: !!user
      }),

      setAuthToken: (token) => set({ authToken: token }),

      login: (user, token) => {
        set({
          user,
          authToken: token,
          isAuthenticated: true,
          error: null
        });
        // Emit login event for inter-store communication
        storeEvents.emit(STORE_EVENTS.USER_LOGIN, user, token);
      },

      logout: () => set({
        user: null,
        authToken: null,
        isAuthenticated: false,
        preferences: defaultPreferences
      }),

      updateUser: (updates) => set((state) => ({
        user: state.user ? { ...state.user, ...updates } : null
      })),

      setPreferences: (preferences) => set((state) => ({
        preferences: { ...state.preferences, ...preferences }
      })),

      updatePreference: (key, value) => set((state) => ({
        preferences: { ...state.preferences, [key]: value }
      })),

      setAuthenticated: (authenticated) => set({ isAuthenticated: authenticated }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      clearState: () => set({
        user: null,
        authToken: null,
        preferences: defaultPreferences,
        isAuthenticated: false,
        isLoading: false,
        error: null
      })
    }),
    {
      name: 'user-store',
      // Persist user and preferences, but not loading/error states
      partialize: (state) => ({
        user: state.user,
        authToken: state.authToken,
        preferences: state.preferences,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);

// Export singleton instance for easy usage
export const useUserStore = createUserStore();

// Helper functions for user operations
export const userStoreHelpers = {
  isUserLoggedIn: (user: User | null) => !!user,

  getUserDisplayName: (user: User | null) =>
    user?.display_name || user?.username || 'Anonymous',

  getUserInitials: (user: User | null) => {
    const name = userStoreHelpers.getUserDisplayName(user);
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  },

  hasUserAvatar: (user: User | null) => !!user?.avatar,

  isThemeDark: (preferences: UserPreferences) => {
    if (preferences.theme === 'dark') return true;
    if (preferences.theme === 'light') return false;
    // system - detect from browser/OS
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  },

  getNotificationCount: (preferences: UserPreferences) =>
    Object.values(preferences.notifications).filter(Boolean).length,

  isNotificationEnabled: (preferences: UserPreferences, type: keyof UserPreferences['notifications']) =>
    preferences.notifications[type],

  formatUserTimezone: (preferences: UserPreferences, date: Date) => {
    try {
      return date.toLocaleString('en-US', {
        timeZone: preferences.timezone,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    } catch {
      return date.toLocaleString();
    }
  }
};