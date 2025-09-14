# Iconography

This app adopts lucide-react for general UI icons and adds a small set of custom football icons. Icons are accessible, consistent in sizing, and theme-friendly.

## Libraries

- Primary: `lucide-react`
  - Use for generic UI (navigation, actions, feedback)
  - Always set `aria-hidden` on decorative icons; add accessible names for meaningful icons

## Custom Football Icons

Location: `src/components/icons/`

Available names:
- `football-ball`
- `football-field`
- `goal-posts`
- `helmet`

Usage via factory map:

```tsx
import { ICONS } from '@/components/icons';

export function Example() {
  return (
    <div className="flex items-center gap-3">
      {ICONS['football-ball']({ size: 16, title: 'Football' })}
      {ICONS['football-field']({ size: 16, title: 'Field' })}
      {ICONS['goal-posts']({ size: 16, title: 'Goal posts' })}
      {ICONS['helmet']({ size: 16, title: 'Helmet' })}
    </div>
  );
}
```

Each custom icon is an inline SVG with `currentColor` so it responds to text color and theming.

## Sizing & Styling

- Default size is 16px; use 14–20px for inline UI, 24–32px for headers or tiles.
- Prefer utility classes for color (e.g., `text-[var(--color-muted)]`) or pass `color` to the `Icon` wrapper.
- Keep icons visually aligned to the text baseline (`className="inline align-middle"` when needed).

## Accessibility

- Decorative: set `aria-hidden` or omit `title`.
- Meaningful: include a `title` or `aria-label` via the `Icon` wrapper.
- Ensure sufficient contrast against backgrounds (tokens already tuned for AA/AAA).

## When to create custom icons

- Domain-specific symbols not covered by lucide-react (e.g., fantasy sports concepts) should live under `src/components/icons/`.
- Keep SVGs minimal with consistent stroke widths to match lucide style.

