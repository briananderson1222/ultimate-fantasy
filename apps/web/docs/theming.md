# Theming Guide

This frontend uses CSS variables for theme tokens and a lightweight runtime theme manager. You can switch between light/dark/system or apply a custom theme JSON, and even override branding per league.

## Tokens

- Source: `src/styles/theme.css`
- Categories: surfaces, text, brand, semantic, borders/focus, radii, spacing, shadows
- Variables:
  - Surfaces: `--color-bg`, `--color-surface`, `--color-elevated`, `--color-overlay`
  - Text: `--color-text`, `--color-muted`
  - Brand: `--color-primary`, `--color-primary-contrast`, `--color-secondary`, `--color-secondary-contrast`, `--color-accent`, `--color-accent-contrast`
  - Semantic: `--color-success`, `--color-warning`, `--color-destructive`
  - Borders/Focus: `--border`, `--ring`, `--ring-offset`
  - Radius: `--radius-sm|md|lg`
  - Spacing: `--space-1..6`
  - Shadows: `--shadow-sm|md`

Dark mode overrides live under `[data-theme="dark"]` in the same file and set surface, text, semantic, and focus tokens to maintain AA/AAA contrast.

## Applying Themes

Runtime theming is powered by `ThemeProvider` (`src/app/theme.tsx`). It manages:

- `theme`: `light | dark | custom` (persisted at `localStorage.uf_theme`)
- `custom`: a partial map of CSS variables (persisted at `localStorage.uf_theme_custom`)

Usage example:

```tsx
import { useTheme } from "@/app/theme";

export default function Example() {
  const { theme, setTheme, custom, setCustom } = useTheme();
  return (
    <div>
      <button onClick={() => setTheme("dark")}>Dark</button>
      <button onClick={() => setTheme("light")}>Light</button>
      <button
        onClick={() => {
          setCustom({ "--color-primary": "#7c3aed" });
          setTheme("custom");
        }}
      >
        Purple Primary
      </button>
    </div>
  );
}
```

Under the hood, `ThemeProvider` sets `document.documentElement.dataset.theme` and applies `custom` variables as inline CSS vars.

## Theme Studio

Interactive editor at `/settings/theme` for live token editing.

- Switch between light/dark/custom
- Paste/Edit a JSON object of CSS var overrides
- Persisted in localStorage and applied globally

Presets:

- Fantasy Football Pack: available at `/themes/fantasy-football.json` and loadable via the “Load Fantasy Pack” button in Theme Settings. It includes Turf Green primary, Honey Gold accent, and subtle gradient/texture variables (`--gradient-*`, `--texture-noise`). Add an optional noise image at `public/brand/textures/noise.png` to enable textured backgrounds via `.hero-gradient` and `.surface-textured` classes.

Example custom theme JSON:

```json
{
  "--color-primary": "#0f766e",
  "--color-primary-contrast": "#ffffff",
  "--radius-md": "10px"
}
```

## Tailwind Integration

Tailwind utilities can reference CSS variables for consistency. Prefer using semantic classes and minimal custom CSS; where required, use `var(--token)` in styles.

Example:

```css
.btn-primary {
  background: var(--color-primary);
  color: var(--color-primary-contrast);
  border-radius: var(--radius-md);
}
```

## Per‑League Branding (optional)

When available, the public league payload may include branding with theme variables:

- Contract type: `LeagueBranding` → `{ theme?: Record<string, string>, name?: string, logo_url?: string }`
- The League page loads branding and can apply variables on top of the active theme:

```tsx
import { LeagueBranding } from "@/components/LeagueBranding";

// Wrap page content to scope overrides if desired
<LeagueBranding themeVars={league.branding?.theme}>{/* page content */}</LeagueBranding>;
```

Alternatively, merge league theme into `ThemeProvider` custom vars if you want global overrides while viewing the league.

## Recipes

- Change primary color:
  - Set `custom` with `{ "--color-primary": "#2563eb", "--color-primary-contrast": "#fff" }`, then `setTheme('custom')`.
- Adjust density:
  - Use spacing variables like `--space-1..6` and component paddings linked to vars.
- Darker dark mode:
  - Extend `[data-theme="dark"]` in `theme.css` with more aggressive `--color-*` values.

## Tips

- Prefer CSS variables over Tailwind color names for themable properties.
- Test themes for contrast and a11y (see a11y tasks) and ensure focus styles remain visible.
- For persisted preferences, the Preferences store can sync `theme` to the server once `/me/preferences` is available.
