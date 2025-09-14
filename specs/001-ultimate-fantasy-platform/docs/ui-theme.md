# Fantasy Football Theme — Design Direction

This document outlines the initial brand and theming direction for a professional Fantasy Football experience. It complements the ThemeProvider and Theme Studio already in the app.

## Brand & Tone

- Energetic, competitive, modern sports feel
- Clean UI with strong contrast and accessible focus states
- Subtle motion; avoid distracting animations during live interactions

## Color System (Tokens)

Semantic scales (light/dark):
- `--color-bg`, `--color-surface`, `--color-elevated`
- `--color-text`, `--color-muted`
- `--color-primary`, `--color-primary-contrast`
- `--color-accent`, `--color-accent-contrast`
- `--color-success`, `--color-warning`, `--color-destructive`
- `--ring`, `--ring-offset`, `--border`

Fantasy Football default palette (Light):
- Turf Green: `--color-primary: #17803A` (or `rgb(23,128,58)`)
- Gold Accent: `--color-accent: #FFC94D`
- Surfaces: `--color-bg: #F7F8FA`, `--color-surface: #FFFFFF`, `--color-elevated: #FBFBFD`
- Text: `--color-text: #0F172A`, `--color-muted: #475569`
- Status: `--color-success: #16A34A`, `--color-warning: #EAB308`, `--color-destructive: #DC2626`
- Borders: `--border: rgba(15, 23, 42, 0.12)`, `--ring: #2563EB`

Dark mode adjustments:
- Backgrounds shift to graphite (`#0B1220`, `#111827`), text to `#E5E7EB`
- Preserve contrast (AA minimum, AAA preferred for body text)

## Typography

- Headings: Inter or similar (variable weight); 28/24/20 scale
- Body: Inter 14–16px depending on density
- Emphasis: numeric tabs/buttons use medium–semibold weights for clarity

## Spacing & Radius

- `--radius-sm: 6px`, `--radius-md: 10px`, `--radius-lg: 14px`
- `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--space-6: 24px`

## Shadows

- `--shadow-sm: 0 1px 2px rgba(0,0,0,0.04)`
- `--shadow-md: 0 4px 16px rgba(0,0,0,0.08)`

## Tokens Example (JSON)

```json
{
  "--color-bg": "#F7F8FA",
  "--color-surface": "#FFFFFF",
  "--color-text": "#0F172A",
  "--color-muted": "#475569",
  "--color-primary": "#17803A",
  "--color-primary-contrast": "#FFFFFF",
  "--color-accent": "#FFC94D",
  "--color-success": "#16A34A",
  "--color-warning": "#EAB308",
  "--color-destructive": "#DC2626",
  "--border": "rgba(15, 23, 42, 0.12)",
  "--ring": "#2563EB",
  "--radius-md": "10px"
}
```

## Implementation Notes

- ThemeProvider already supports JSON variable maps; Theme Studio can load these.
- Use Tailwind utility classes in tandem with CSS variables by referencing variables in style attributes or custom classes where necessary.
- Add a `brand` theme preset under `/settings/theme` as a quick-start.
- Consider adding textures (subtle noise field) via `background-image` overlays for cards or hero sections.

## Pages To Apply (see tasks T200–T215)

- Landing page hero, themed illustrations
- League public: scoreboard tiles with badges (Leader, Streak), members grid with avatars
- Draft Room MVP: picks queue, timers, chat
- Waivers & trades: activity feed with status badges, card styles
- Player search & stats: sticky filter bar, responsive table/cards

