# Migration Guide: Design System

This guide helps you migrate from the old component structure to the new Ultimate Fantasy Design System.

## Overview

The new design system provides:

- Centralized theme management
- Consistent component APIs
- Better TypeScript support
- Improved accessibility
- Enhanced performance

## Component Migrations

### Button Components

#### Before (Legacy UI)

```tsx
import { Button } from "../components/ui/button";

<Button className="btn-primary" size="large">
  Click me
</Button>;
```

#### After (Design System)

```tsx
import { Button } from "../components/design-system";

<Button variant="primary" size="lg">
  Click me
</Button>;
```

**Changes:**

- `className="btn-primary"` → `variant="primary"`
- `size="large"` → `size="lg"`
- Automatic theme support

### Card Components

#### Before (Legacy UI)

```tsx
import { Card } from "../components/ui/card";

<Card>
  <div className="card-header">
    <h3>Title</h3>
  </div>
  <div className="card-content">Content here</div>
</Card>;
```

#### After (Design System)

```tsx
import { Card } from "../components/design-system";

<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>Content here</Card.Content>
</Card>;
```

**Changes:**

- Structured sub-components (Card.Header, Card.Content)
- Built-in typography components (Card.Title)
- Automatic spacing and theming

### Progress Indicators

#### Before (Custom Implementation)

```tsx
<div className="progress-bar">
  <div className="progress-fill" style={{ width: `${percentage}%` }} />
</div>
```

#### After (Design System)

```tsx
import { ProgressBar } from "../components/design-system";

<ProgressBar value={75} max={100} variant="success" aria-label="Win percentage" />;
```

**Changes:**

- Accessible by default
- Built-in variants and sizing
- Proper ARIA attributes

## Theme Migration

### Before (CSS Variables)

```css
:root {
  --primary-color: #0066cc;
  --background-color: #ffffff;
  --text-color: #333333;
}

.dark {
  --primary-color: #3399ff;
  --background-color: #1a1a1a;
  --text-color: #ffffff;
}
```

### After (Theme Provider)

```tsx
import { ThemeProvider } from "../components/design-system";

function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <YourApp />
    </ThemeProvider>
  );
}

// Use theme in components
import { useTheme } from "../components/design-system";

function Component() {
  const { theme, setTheme, tokens } = useTheme();

  return <div style={{ color: tokens.colors.primary }}>Current theme: {theme}</div>;
}
```

**Benefits:**

- Runtime theme switching
- Type-safe color tokens
- Automatic localStorage persistence
- Better React integration

## Import Structure Changes

### Before

```tsx
// Scattered imports
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { ProgressBar } from "../components/custom/progress";
import { PlayerCard } from "../components/players/PlayerCard";
```

### After

```tsx
// Centralized design system imports
import {
  Button,
  Card,
  ProgressBar,
  PlayerCard,
  ThemeProvider,
  useTheme,
} from "../components/design-system";
```

**Benefits:**

- Single import location
- Tree-shaking friendly
- Better IDE autocomplete
- Consistent API surface

## Styling Changes

### Before (Manual CSS)

```css
.custom-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

### After (Design Tokens)

```css
.custom-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-card);
  box-shadow: var(--shadow-card);
}
```

**Benefits:**

- Semantic token names
- Automatic theme switching
- Consistent spacing scale
- Responsive values

## Fantasy-Specific Components

### New Components Available

These components are specifically designed for fantasy sports:

#### MatchCard

```tsx
import { MatchCard } from "../components/design-system";

<MatchCard
  match={{
    homeTeam: { name: "Warriors", owner: "John", record: { wins: 8, losses: 4 } },
    awayTeam: { name: "Dragons", owner: "Jane", record: { wins: 6, losses: 6 } },
    week: 13,
    actualPoints: { home: 118.7, away: 105.3 },
    status: "completed",
  }}
  onClick={() => navigate("/match/123")}
/>;
```

#### PlayerCard

```tsx
import { PlayerCard } from "../components/design-system";

<PlayerCard
  player={{
    name: "Patrick Mahomes",
    position: "QB",
    team: "KC",
    stats: { points: 24.5, projected: 22.1 },
    injuryStatus: { status: "healthy" },
  }}
  draggable
  showActions
  onAdd={() => addPlayer()}
/>;
```

#### TrendingPlayers

```tsx
import { TrendingPlayers } from "../components/design-system";

<TrendingPlayers players={trendingData} showActions onAddPlayer={handleAdd} />;
```

## Migration Steps

### 1. Install Theme Provider

Wrap your app with the ThemeProvider:

```tsx
// In your root App component
import { ThemeProvider } from "../components/design-system";

function App() {
  return <ThemeProvider defaultTheme="dark">{/* Your existing app */}</ThemeProvider>;
}
```

### 2. Update Imports (Gradual)

Replace imports one component at a time:

```tsx
// Week 1: Update buttons
import { Button } from "../components/design-system";

// Week 2: Update cards
import { Card } from "../components/design-system";

// Week 3: Add new fantasy components
import { MatchCard, PlayerCard } from "../components/design-system";
```

### 3. Update Styling

Replace hardcoded values with design tokens:

```bash
# Find and replace
# Old: color: #00e5ff
# New: color: var(--color-primary)

# Old: padding: 16px
# New: padding: var(--space-md)
```

### 4. Test Theme Switching

Ensure your components work in both themes:

```tsx
function TestThemes() {
  const { setTheme } = useTheme();

  return (
    <div>
      <Button onClick={() => setTheme("light")}>Light</Button>
      <Button onClick={() => setTheme("dark")}>Dark</Button>
    </div>
  );
}
```

### 5. Update Tests

Update component tests for new APIs:

```tsx
// Before
expect(screen.getByRole("button")).toHaveClass("btn-primary");

// After
expect(screen.getByRole("button")).toHaveAttribute("data-variant", "primary");
```

## Breaking Changes

### Component Props

- `Button`: `variant` replaces `className` styling
- `Card`: Structured sub-components required
- `ProgressBar`: `value`/`max` instead of `percentage`

### CSS Classes

- Theme classes automatically applied
- Manual theme toggling no longer needed
- Design token CSS variables renamed

### TypeScript

- Stricter prop types
- Required theme context
- New component interfaces

## Troubleshooting

### Common Issues

#### Theme Not Applied

**Problem**: Components don't show proper styling
**Solution**: Ensure ThemeProvider wraps your app

```tsx
// Fix: Add ThemeProvider
<ThemeProvider defaultTheme="dark">
  <App />
</ThemeProvider>
```

#### Import Errors

**Problem**: Cannot find component exports
**Solution**: Check import path and component name

```tsx
// Correct import structure
import { Button, Card } from "../components/design-system";
```

#### CSS Conflicts

**Problem**: Old styles interfering with new components
**Solution**: Gradually remove legacy CSS

```css
/* Remove legacy styles */
/* .btn-primary { ... } */

/* Keep design system tokens */
.custom-component {
  color: var(--color-primary);
}
```

### Performance Issues

#### Large Bundle Size

**Solution**: Use tree-shaking imports

```tsx
// Good: Tree-shakable
import { Button } from "../components/design-system";

// Avoid: Imports everything
import * as DS from "../components/design-system";
```

#### Slow Theme Switching

**Solution**: Use CSS custom properties instead of inline styles

```tsx
// Good: Uses CSS variables
<div className="bg-surface text-primary">

// Avoid: Inline styles
<div style={{ background: tokens.colors.surface }}>
```

## Testing Migration

### Test Checklist

- [ ] All components render correctly
- [ ] Theme switching works
- [ ] Accessibility features work
- [ ] Performance is acceptable
- [ ] Tests pass
- [ ] Bundle size is reasonable

### Automated Tests

```bash
# Run full test suite
npm run test

# Visual regression tests
npm run test:visual

# Accessibility tests
npm run test:a11y

# Bundle analysis
npm run build:analyze
```

## Support

### Getting Help

1. Check [design system documentation](./design-system.md)
2. Browse [component examples](/design-system)
3. Review [Storybook documentation](http://localhost:61000)
4. Search [existing issues](https://github.com/project/issues)

### Migration Assistance

For complex migrations:

1. Create a migration issue
2. Provide example code
3. Describe expected behavior
4. Include error messages

## Timeline Recommendations

### Phase 1 (Week 1-2): Foundation

- Install ThemeProvider
- Migrate Button components
- Update basic styling

### Phase 2 (Week 3-4): Core Components

- Migrate Card components
- Add ProgressBar usage
- Update forms and inputs

### Phase 3 (Week 5-6): Fantasy Components

- Implement MatchCard
- Add PlayerCard usage
- Integrate TrendingPlayers

### Phase 4 (Week 7-8): Polish

- Remove legacy code
- Optimize performance
- Complete testing

This gradual approach minimizes risk and allows for thorough testing at each stage.
