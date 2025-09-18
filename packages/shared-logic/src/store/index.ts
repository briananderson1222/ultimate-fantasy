// Export all stores and utilities
export * from './appStore';
export * from './userStore';
export * from './leagueStore';

// Re-export create for convenience
import { create } from 'zustand';
export { create };

// Combined store instance for global access
import { useUserStore } from './userStore';
import { useLeagueStore } from './leagueStore';
import { useAppStore } from './appStore';

// Global store accessor that combines all stores
export const useStore = () => {
  const userState = useUserStore.getState();
  const leagueState = useLeagueStore.getState();
  const appState = useAppStore.getState();

  return {
    // User store properties
    currentUser: userState.user,
    setCurrentUser: userState.setUser,

    // League store properties
    leagues: leagueState.leagues,
    currentLeague: leagueState.currentLeague,
    setCurrentLeague: leagueState.setCurrentLeague,

    // App store properties
    theme: appState.theme,
    setTheme: appState.setTheme,
    isOnline: appState.isOnline,
    setOnlineStatus: appState.setOnlineStatus
  };
};

// Generic createStore function
export const createStore = create;