# Ultimate Fantasy Design System

## Overview

The Ultimate Fantasy Design System is a comprehensive component library built for modern fantasy sports applications. It features a dark-first approach with cyan/green accents, card-based layouts, and full TypeScript support.

## Key Features

- **Dark-first theming** with light mode support
- **Runtime theme switching** with localStorage persistence
- **Fantasy sports-specific components** (MatchCard, PlayerCard, etc.)
- **Comprehensive component library** with 15+ components
- **Type-safe** with full TypeScript support
- **Accessible** with ARIA labels and keyboard navigation
- **Responsive** with mobile-first approach

## Getting Started

### Installation

The design system is already included in this project. To use components:

```tsx
import { Button, Card, ThemeProvider } from "../components/design-system";

// Wrap your app with ThemeProvider
<ThemeProvider>
  <Card>
    <Card.Header>
      <Card.Title>My Component</Card.Title>
    </Card.Header>
    <Card.Content>
      <Button variant="primary">Click me</Button>
    </Card.Content>
  </Card>
</ThemeProvider>;
```

### Theme Usage

```tsx
import { useTheme } from "../components/design-system";

function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      Toggle to {theme === "dark" ? "Light" : "Dark"}
    </Button>
  );
}
```

## Design Tokens

### Colors

The design system uses a carefully crafted color palette optimized for fantasy sports:

- **Primary**: Cyan (#00e5ff) - Main brand color
- **Success**: Green (#00e676) - Positive actions, wins
- **Warning**: Amber (#ffb74d) - Alerts, questionable players
- **Surface**: Card backgrounds with subtle gradients

### Typography

Responsive typography scale with three breakpoints:

- **Mobile**: Optimized for small screens
- **Base**: Default scale for tablets
- **Desktop**: Enhanced scale for large screens

### Spacing & Layout

- Consistent spacing scale (4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px)
- Card-based layouts with subtle shadows
- Mobile-first responsive design

## Components

### Primitive Components

#### Button

Versatile button component with multiple variants and states.

```tsx
<Button variant="primary" size="lg" leftIcon={<Plus />}>
  Add Player
</Button>
```

**Variants**: `primary`, `secondary`, `outline`, `ghost`, `destructive`
**Sizes**: `sm`, `md`, `lg`, `xl`

#### Card

Flexible card component with sub-components for structured content.

```tsx
<Card>
  <Card.Header>
    <Card.Title>Team Statistics</Card.Title>
    <Card.Description>Season performance overview</Card.Description>
  </Card.Header>
  <Card.Content>
    <p>Your content here</p>
  </Card.Content>
  <Card.Footer>
    <Button>View Details</Button>
  </Card.Footer>
</Card>
```

#### ProgressBar

Visual progress indicator perfect for stats and completion tracking.

```tsx
<ProgressBar value={75} max={100} variant="success" showLabel label="Win Percentage" />
```

#### Avatar

User and team avatars with fallback support.

```tsx
<Avatar src="/user-photo.jpg" alt="John Doe" fallback="JD" size="lg" />
```

#### Badge

Status indicators and labels.

```tsx
<Badge variant="success">Active</Badge>
<Badge variant="warning" icon={<AlertIcon />} removable>
  Questionable
</Badge>
```

### Pattern Components

#### MatchCard

Display fantasy matchups with team info, scores, and projections.

```tsx
<MatchCard
  match={{
    homeTeam: { name: "Team Warriors", owner: "John", record: { wins: 8, losses: 4 } },
    awayTeam: { name: "Team Dragons", owner: "Jane", record: { wins: 6, losses: 6 } },
    week: 13,
    actualPoints: { home: 118.7, away: 105.3 },
    status: "completed",
  }}
  onClick={() => navigate("/match/123")}
/>
```

#### PlayerCard

Comprehensive player information with stats and actions.

```tsx
<PlayerCard
  player={{
    name: "Patrick Mahomes",
    position: "QB",
    team: "KC",
    stats: { points: 24.5, projected: 22.1 },
    status: "active",
  }}
  actions={[
    { label: "Start", action: () => startPlayer() },
    { label: "Bench", action: () => benchPlayer() },
  ]}
  draggable
/>
```

#### TrendingPlayers

Show trending players with performance data and add/drop percentages.

```tsx
<TrendingPlayers
  players={trendingData}
  showActions
  onAddPlayer={handleAddPlayer}
  filters={{ position: ["QB", "RB", "WR"] }}
/>
```

#### SettingsGrid

Configurable settings interface for league management.

```tsx
<SettingsGrid
  settings={[
    {
      id: "scoring",
      title: "Scoring System",
      description: "How points are calculated",
      value: "PPR",
      type: "select",
      options: ["Standard", "PPR", "Half PPR"],
    },
  ]}
  onChange={handleSettingChange}
/>
```

#### LeagueChat

Real-time chat with transaction notifications.

```tsx
<LeagueChat
  messages={chatMessages}
  showComposer
  showTypingIndicator
  onSendMessage={handleSendMessage}
  currentUserId="user123"
/>
```

## Accessibility

The design system follows WCAG 2.1 AA guidelines:

- **Keyboard Navigation**: All interactive elements are keyboard accessible
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: High contrast ratios for all text
- **Focus Management**: Clear focus indicators
- **Reduced Motion**: Respects user preferences

### Accessibility Features

- Semantic HTML structures
- ARIA labels for complex components
- Keyboard shortcuts for common actions
- Screen reader-friendly descriptions
- High contrast mode support

## Performance

### Optimization Features

- **Tree Shaking**: Only import components you use
- **Lazy Loading**: Components load on demand
- **Efficient Animations**: 60fps performance with Framer Motion
- **Minimal Bundle Size**: Optimized for fast loading

### Bundle Analysis

```bash
npm run build:analyze
```

## Testing

### Component Testing

Each component includes comprehensive tests:

```bash
# Run all tests
npm run test

# Run component-specific tests
npm run test -- ProgressBar

# Visual regression tests
npm run test:visual
```

### Test Coverage

- Unit tests for all components
- Integration tests for complex patterns
- Visual regression tests for UI consistency
- Accessibility tests for compliance

## Migration Guide

### From Legacy Components

Replace old components with new design system equivalents:

```tsx
// Old
<div className="card">
  <h3>Title</h3>
  <p>Content</p>
</div>

// New
<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>
    <p>Content</p>
  </Card.Content>
</Card>
```

### Breaking Changes

- Button `iconOnly` prop renamed to `isIconOnly`
- Card components now use dot notation (Card.Header, Card.Content)
- Theme provider required for proper styling

## Storybook Documentation

View all components in Ladle:

```bash
npm run play:ui
```

Browse to `http://localhost:61000` to see:

- Component examples
- Interactive props
- Usage documentation
- Code snippets

## Contributing

### Adding New Components

1. Create component in appropriate directory (`primitives/` or `patterns/`)
2. Add comprehensive TypeScript types
3. Include Ladle story
4. Write unit tests
5. Add accessibility features
6. Update documentation

### Design Tokens

When modifying design tokens:

1. Update token files in `tokens/` directory
2. Regenerate CSS custom properties
3. Test theme switching
4. Update related components
5. Run visual regression tests

## Best Practices

### Component Design

- Use composition over inheritance
- Provide sensible defaults
- Support both controlled and uncontrolled usage
- Include proper TypeScript types
- Follow accessibility guidelines

### Theme Usage

- Use design tokens instead of hardcoded values
- Support both light and dark themes
- Test theme switching thoroughly
- Respect user preferences

### Performance

- Use React.memo for expensive components
- Implement proper key props for lists
- Lazy load heavy components
- Optimize images and assets

## Future Roadmap

### Planned Features

- Animation presets library
- Advanced drag-and-drop patterns
- Data visualization components
- Mobile-specific optimizations
- Theme customization tools

### Community

- Contribution guidelines
- Issue templates
- Feature request process
- Code review standards

---

For more information, see the [component showcase](/design-system) or browse the [Ladle documentation](http://localhost:61000).
