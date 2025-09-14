# Customization Guide

Ultimate Fantasy frontend supports flexible customization for layout, widgets, saved views, filters, and sharing. This guide explains the built-in controls and how to persist them.

## Dashboard Layout & Widgets

- Entry point: `src/app/(dashboard)/page.tsx`
- Widgets are modular components with optional per-widget settings.
- Drag & resize: implemented with lightweight CSS/grid + pointer events.
- Persistence: layout is stored in localStorage (see `usePreferences` for server sync once available).

Common actions:
- Reorder: drag widgets by their header.
- Resize: grab resize handles (where available) to change width/height.
- Configure: open a widget’s settings modal to set defaults (e.g., default league).
- Save/Reset: use the dashboard’s Save/Reset actions to write/read layout state.

## Preferences Store

- Source: `src/lib/preferences.ts`
- Fields: `theme`, `density`, `locale`, optional `layouts`
- Behavior:
  - Persists to `localStorage` immediately on change.
  - Debounced server sync via `/me/preferences` when authenticated.
  - Conflict handling on startup merges last server snapshot and local edits.

Use it via context:
```tsx
import { usePreferences } from '@/lib/preferences';

const { preferences, setDensity, setLocale, setLayouts } = usePreferences();
```

## DataTable: Saved Views, Filters, and Sharing

- Component: `src/components/ui/data-table.tsx`
- Features:
  - Show/hide columns
  - Sorting (ascending/descending)
  - Saved views in localStorage by `storageKey`
  - Filter chips with basic operators
  - Share current view: encodes view state as URL param via `shareKey`

Example usage:
```tsx
<DataTable
  columns={[
    { key: 'name', header: 'Name', sortable: true },
    { key: 'pos', header: 'Pos', sortable: true },
    { key: 'points', header: 'PTS', sortable: true },
  ]}
  data={rows}
  initialSort={{ key: 'points', dir: 'desc' }}
  pageSize={10}
  storageKey="players"
  shareKey="v"
/>
```

Tips:
- Encourage semantic column keys to maintain stable saved views.
- Consider scoping `storageKey` by page/league for per-context defaults.

## Theming & Branding

- See `docs/theming.md` for token controls and Theme Studio usage.
- Per-league branding can apply a CSS var map on top of the current theme.

## i18n & Density

- Locale switcher component: `src/components/LocaleSwitcher.tsx` (backed by `src/app/i18n.tsx`)
- Density toggles are applied globally by PreferencesProvider, which sets `document.documentElement.dataset.density` to `comfortable | compact`. CSS variables in `src/styles/theme.css` adjust spacing, radius, and body font sizes under `[data-density="compact"]`.

## Server Sync Recommendations

- Keep local-first UX. Attempt server PUTs in the background.
- Use a stable schema on `/me/preferences` to capture layout and defaults.
- On 409/merge conflicts, prefer the server snapshot, mark conflict, and expose a “Reapply my changes” action.
