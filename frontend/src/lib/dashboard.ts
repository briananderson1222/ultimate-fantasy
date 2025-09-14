export type WidgetKey = 'myLeagues' | 'upcoming' | 'scoreboard' | 'waivers' | 'tips';

export const DEFAULT_WIDGETS: WidgetKey[] = [
  'myLeagues',
  'upcoming',
  'scoreboard',
  'waivers',
  'tips',
];

const KEY = 'uf_dashboard_layout';
const SIZE_KEY = 'uf_dashboard_sizes';
const SETTINGS_KEY = 'uf_widget_settings';

export function loadLayout(): WidgetKey[] {
  try {
    const raw = localStorage.getItem(KEY);
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

export function saveLayout(order: WidgetKey[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(order));
  } catch {}
}

export type WidgetSizes = Record<WidgetKey, 1 | 2 | 3>;

export function loadSizes(): WidgetSizes {
  try {
    const raw = localStorage.getItem(SIZE_KEY);
    if (!raw) throw new Error('no sizes');
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

export function saveSizes(sizes: WidgetSizes): void {
  try {
    localStorage.setItem(SIZE_KEY, JSON.stringify(sizes));
  } catch {}
}

export type WidgetSettings = Partial<
  Record<
    WidgetKey,
    {
      leagueId?: string;
      notes?: string;
    }
  >
>;

export function loadWidgetSettings(): WidgetSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as WidgetSettings;
  } catch {
    return {};
  }
}

export function saveWidgetSettings(settings: WidgetSettings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {}
}
