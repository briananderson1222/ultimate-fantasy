// Dashboard widget types and utilities extracted from frontend
export type WidgetKey = "myLeagues" | "upcoming" | "scoreboard" | "waivers" | "tips";

export const DEFAULT_WIDGETS: WidgetKey[] = [
  "myLeagues",
  "upcoming",
  "scoreboard",
  "waivers",
  "tips",
];

export type WidgetSizes = Record<WidgetKey, 1 | 2 | 3>;

export type WidgetSettings = Partial<
  Record<
    WidgetKey,
    {
      leagueId?: string;
      notes?: string;
    }
  >
>;

// Storage interface for platform abstraction
export interface StorageAdapter {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

// Browser localStorage adapter
export class BrowserStorageAdapter implements StorageAdapter {
  getItem(key: string): string | null {
    try {
      return typeof window !== "undefined" ? localStorage.getItem(key) : null;
    } catch {
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem(key, value);
      }
    } catch {}
  }

  removeItem(key: string): void {
    try {
      if (typeof window !== "undefined") {
        localStorage.removeItem(key);
      }
    } catch {}
  }
}

// React Native AsyncStorage adapter
export class NativeStorageAdapter implements StorageAdapter {
  private asyncStorage: any;

  constructor() {
    try {
      this.asyncStorage = require('@react-native-async-storage/async-storage').default;
    } catch {
      // AsyncStorage not available, fall back to memory storage
      this.asyncStorage = new Map();
    }
  }

  getItem(key: string): string | null {
    try {
      if (this.asyncStorage instanceof Map) {
        return this.asyncStorage.get(key) || null;
      }
      // AsyncStorage is async, but for compatibility we'll try sync access
      // In real implementation, this should be async
      return null; // Placeholder - would need async implementation
    } catch {
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      if (this.asyncStorage instanceof Map) {
        this.asyncStorage.set(key, value);
        return;
      }
      // AsyncStorage is async, but for compatibility we'll try sync access
      // In real implementation, this should be async
      this.asyncStorage.setItem(key, value);
    } catch {}
  }

  removeItem(key: string): void {
    try {
      if (this.asyncStorage instanceof Map) {
        this.asyncStorage.delete(key);
        return;
      }
      // AsyncStorage is async, but for compatibility we'll try sync access
      // In real implementation, this should be async
      this.asyncStorage.removeItem(key);
    } catch {}
  }
}

// Platform-aware storage adapter factory
function createPlatformStorageAdapter(): StorageAdapter {
  // Check for React Native environment
  if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
    return new NativeStorageAdapter();
  }

  // Check for React Native runtime (Expo)
  if (typeof global !== 'undefined' && (global as any).expo) {
    return new NativeStorageAdapter();
  }

  // Check for Metro bundler (React Native) using environment variables
  if (typeof (globalThis as any).__DEV__ !== 'undefined' &&
      typeof process !== 'undefined' &&
      process.env &&
      (process.env.RN_PLATFORM || process.env.EXPO_PUBLIC_PLATFORM)) {
    return new NativeStorageAdapter();
  }

  // Default to browser storage
  return new BrowserStorageAdapter();
}

// Dashboard utilities class for cross-platform compatibility
export class DashboardUtils {
  private storage: StorageAdapter;
  private readonly LAYOUT_KEY = "uf_dashboard_layout";
  private readonly SIZE_KEY = "uf_dashboard_sizes";
  private readonly SETTINGS_KEY = "uf_widget_settings";

  constructor(storage?: StorageAdapter) {
    this.storage = storage || createPlatformStorageAdapter();
  }

  // Layout management
  loadLayout(): WidgetKey[] {
    try {
      const raw = this.storage.getItem(this.LAYOUT_KEY);
      if (!raw) return DEFAULT_WIDGETS;
      const arr = JSON.parse(raw) as WidgetKey[];
      // Validate keys
      const valid = arr.filter((k) => DEFAULT_WIDGETS.includes(k));
      if (valid.length) return valid as WidgetKey[];
      return DEFAULT_WIDGETS;
    } catch {
      return DEFAULT_WIDGETS;
    }
  }

  saveLayout(order: WidgetKey[]): void {
    try {
      this.storage.setItem(this.LAYOUT_KEY, JSON.stringify(order));
    } catch {}
  }

  // Widget sizes management
  loadSizes(): WidgetSizes {
    try {
      const raw = this.storage.getItem(this.SIZE_KEY);
      if (!raw) throw new Error("no sizes");
      const parsed = JSON.parse(raw) as Partial<WidgetSizes>;
      return {
        myLeagues: parsed.myLeagues || 1,
        upcoming: parsed.upcoming || 1,
        scoreboard: parsed.scoreboard || 2,
        waivers: parsed.waivers || 1,
        tips: parsed.tips || 1,
      };
    } catch {
      return { myLeagues: 1, upcoming: 1, scoreboard: 2, waivers: 1, tips: 1 };
    }
  }

  saveSizes(sizes: WidgetSizes): void {
    try {
      this.storage.setItem(this.SIZE_KEY, JSON.stringify(sizes));
    } catch {}
  }

  // Widget settings management
  loadWidgetSettings(): WidgetSettings {
    try {
      const raw = this.storage.getItem(this.SETTINGS_KEY);
      if (!raw) return {};
      return JSON.parse(raw) as WidgetSettings;
    } catch {
      return {};
    }
  }

  saveWidgetSettings(settings: WidgetSettings): void {
    try {
      this.storage.setItem(this.SETTINGS_KEY, JSON.stringify(settings));
    } catch {}
  }

  // Additional utility methods for fantasy sports
  calculateTeamScore(teamData: { players: Array<{ points: number; position: string }> }): number {
    return teamData.players.reduce((total, player) => total + player.points, 0);
  }

  getUpcomingMatchups(leagues: Array<{ league_id: string; name: string }>): Array<{ league_id: string; name: string; next_game?: string }> {
    // Placeholder implementation - would be enhanced with real matchup data
    return leagues.map(league => ({
      ...league,
      next_game: 'TBD' // This would come from actual API data
    }));
  }

  getWeeklyHighlights(scoreboards: Array<{ league_id: string; items: Array<{ team_id: string; total_points: number }> }>): Array<{ league_id: string; top_score: number; team_id: string }> {
    return scoreboards.map(scoreboard => {
      const topTeam = scoreboard.items.reduce((top, current) =>
        current.total_points > top.total_points ? current : top
      );
      return {
        league_id: scoreboard.league_id,
        top_score: topTeam.total_points,
        team_id: topTeam.team_id
      };
    });
  }

  formatGameTime(gameTime: Date, timezone: string = 'America/New_York'): string {
    try {
      return gameTime.toLocaleTimeString('en-US', {
        timeZone: timezone,
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return gameTime.toLocaleTimeString();
    }
  }

  getWeekNumber(date: Date = new Date()): number {
    // Simple week calculation - would be enhanced with NFL/fantasy season logic
    const startOfYear = new Date(date.getFullYear(), 0, 1);
    const msPerWeek = 7 * 24 * 60 * 60 * 1000;
    return Math.ceil((date.getTime() - startOfYear.getTime()) / msPerWeek);
  }

  isGameActive(gameTime: Date, duration: number = 3 * 60 * 60 * 1000): boolean {
    const now = new Date();
    const gameEnd = new Date(gameTime.getTime() + duration);
    return now >= gameTime && now <= gameEnd;
  }

  calculateFantasyPoints(playerStats: {
    passingYards?: number;
    passingTDs?: number;
    rushingYards?: number;
    receptions?: number;
    receivingYards?: number;
    receivingTDs?: number;
    interceptions?: number;
    fumbles?: number;
  }, position: string): number {
    let points = 0;

    // Standard fantasy scoring - would be configurable
    if (position === 'QB') {
      points += (playerStats.passingYards || 0) * 0.04; // 1 point per 25 yards
      points += (playerStats.passingTDs || 0) * 4; // 4 points per TD
      points += (playerStats.rushingYards || 0) * 0.1; // 1 point per 10 yards
      points -= (playerStats.interceptions || 0) * 2; // -2 points per INT
    } else if (position === 'RB' || position === 'WR' || position === 'TE') {
      points += (playerStats.rushingYards || 0) * 0.1; // 1 point per 10 yards
      points += (playerStats.receivingYards || 0) * 0.1; // 1 point per 10 yards
      points += (playerStats.receptions || 0) * 0.5; // 0.5 points per reception
      points += (playerStats.receivingTDs || 0) * 6; // 6 points per TD
    }

    // Common penalties
    points -= (playerStats.fumbles || 0) * 2; // -2 points per fumble

    return Math.round(points * 100) / 100; // Round to 2 decimal places
  }

  handleApiError(error: any): { message: string; timestamp: string; platform: string } {
    const platform = typeof window !== 'undefined' ? 'web' : 'mobile';

    return {
      message: error?.message || 'An unknown error occurred',
      timestamp: new Date().toISOString(),
      platform
    };
  }

  formatError(error: Error): { message: string; timestamp: string; platform: string } {
    return this.handleApiError(error);
  }

  // Widget management helpers
  reorderWidgets(currentOrder: WidgetKey[], fromIndex: number, toIndex: number): WidgetKey[] {
    const newOrder = [...currentOrder];
    const [movedWidget] = newOrder.splice(fromIndex, 1);
    newOrder.splice(toIndex, 0, movedWidget);
    return newOrder;
  }

  toggleWidget(currentWidgets: WidgetKey[], widget: WidgetKey): WidgetKey[] {
    if (currentWidgets.includes(widget)) {
      return currentWidgets.filter(w => w !== widget);
    } else {
      return [...currentWidgets, widget];
    }
  }

  resetToDefaults(): { layout: WidgetKey[]; sizes: WidgetSizes; settings: WidgetSettings } {
    return {
      layout: [...DEFAULT_WIDGETS],
      sizes: { myLeagues: 1, upcoming: 1, scoreboard: 2, waivers: 1, tips: 1 },
      settings: {}
    };
  }
}

// Export singleton instance for easy usage
export const dashboardUtils = new DashboardUtils();

// Export factory function for custom storage
export function createDashboardUtils(storage: StorageAdapter): DashboardUtils {
  return new DashboardUtils(storage);
}