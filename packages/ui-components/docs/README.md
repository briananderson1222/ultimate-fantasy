# Ultimate Fantasy Design System Documentation

Welcome to the Ultimate Fantasy Design System - a comprehensive component library and design system for building consistent, accessible, and high-performance fantasy sports applications.

## Overview

The Ultimate Fantasy Design System provides:

- **Reusable Components**: Pre-built React components for web and React Native for mobile
- **Design Tokens**: Consistent colors, typography, spacing, and elevation
- **Accessibility Standards**: WCAG 2.1 AA compliant components
- **Performance Optimized**: 60fps target for mobile, fast rendering for web
- **Cross-Platform**: Shared design language across web and mobile apps

## Quick Start

### Installation

```bash
# For web applications
npm install @ultimate-fantasy/ui-components

# For React Native applications
npm install @ultimate-fantasy/ui-components-native
```

### Basic Usage

```tsx
import { Button, Card, PlayerCard } from '@ultimate-fantasy/ui-components';
import { theme } from '@ultimate-fantasy/design-tokens';

function MyComponent() {
  return (
    <Card>
      <PlayerCard
        player={{
          name: "Mike Trout",
          position: "OF",
          team: "LAA",
          projectedPoints: 12.5
        }}
      />
      <Button variant="primary" size="large">
        Draft Player
      </Button>
    </Card>
  );
}
```

## Design Principles

### 1. Fantasy Sports First
Every component is designed specifically for fantasy sports applications:
- Player-centric data display
- Real-time score updates
- Draft and lineup interfaces
- Trade and waiver workflows

### 2. Performance by Design
All components are optimized for performance:
- Minimal re-renders through React.memo
- Efficient list virtualization
- Optimized animations at 60fps
- Lazy loading for large datasets

### 3. Accessibility Excellence
Built-in accessibility features:
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Motor accessibility considerations

### 4. Mobile-First Responsive
Designed for touch interfaces:
- Large touch targets (44px minimum)
- Swipe gestures and interactions
- Responsive breakpoints
- Adaptive layouts

## Core Components

### Layout Components

#### Container
Provides consistent spacing and alignment across the application.

```tsx
<Container maxWidth="lg" padding="medium">
  <content />
</Container>
```

#### Grid
Flexible grid system for responsive layouts.

```tsx
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>
    <Card>Content 1</Card>
  </Grid>
  <Grid item xs={12} md={6}>
    <Card>Content 2</Card>
  </Grid>
</Grid>
```

#### Stack
Vertical or horizontal stacking with consistent spacing.

```tsx
<Stack direction="column" spacing={3}>
  <PlayerCard player={player1} />
  <PlayerCard player={player2} />
  <PlayerCard player={player3} />
</Stack>
```

### Data Display Components

#### PlayerCard
Displays player information with stats and projections.

```tsx
<PlayerCard
  player={{
    id: "player_123",
    name: "Aaron Judge",
    position: "OF",
    team: "NYY",
    projectedPoints: 15.2,
    recentForm: "hot"
  }}
  showProjections={true}
  showNews={true}
  onSelect={handlePlayerSelect}
/>
```

#### StatCard
Shows statistical information with trends.

```tsx
<StatCard
  title="Fantasy Points"
  value={125.7}
  trend="+12.3"
  trendDirection="up"
  subtitle="This week"
/>
```

#### LeaderboardItem
Displays ranking information with team/player details.

```tsx
<LeaderboardItem
  rank={1}
  team={{
    name: "Team Name",
    owner: "Owner Name",
    record: "8-4",
    points: 1450.5
  }}
  isCurrentUser={false}
/>
```

### Input Components

#### Button
Consistent button styling with multiple variants.

```tsx
<Button
  variant="primary"
  size="large"
  onClick={handleClick}
  loading={isLoading}
  disabled={isDisabled}
>
  Submit Lineup
</Button>
```

#### SearchInput
Optimized search input with debouncing and suggestions.

```tsx
<SearchInput
  placeholder="Search players..."
  onSearch={handleSearch}
  suggestions={playerSuggestions}
  debounceMs={300}
/>
```

#### SelectInput
Dropdown selection with filtering capabilities.

```tsx
<SelectInput
  label="Position"
  options={[
    { value: "all", label: "All Positions" },
    { value: "QB", label: "Quarterback" },
    { value: "RB", label: "Running Back" }
  ]}
  value={selectedPosition}
  onChange={setSelectedPosition}
/>
```

### Fantasy-Specific Components

#### DraftBoard
Interactive draft board for live drafts.

```tsx
<DraftBoard
  picks={draftPicks}
  currentPick={currentPickNumber}
  teams={teams}
  onPickSelect={handlePickSelect}
  isLive={isDraftLive}
/>
```

#### LineupBuilder
Drag-and-drop lineup construction interface.

```tsx
<LineupBuilder
  roster={playerRoster}
  lineup={currentLineup}
  onChange={handleLineupChange}
  positionRequirements={leagueSettings.positions}
/>
```

#### TradeAnalyzer
Trade evaluation and comparison tool.

```tsx
<TradeAnalyzer
  trade={{
    teamA: { players: [...], projectedValue: 45.2 },
    teamB: { players: [...], projectedValue: 47.8 }
  }}
  analysis={tradeAnalysis}
  onAccept={handleTradeAccept}
  onReject={handleTradeReject}
/>
```

#### MatchupPreview
Head-to-head matchup display with projections.

```tsx
<MatchupPreview
  teamA={userTeam}
  teamB={opponentTeam}
  week={currentWeek}
  projections={weeklyProjections}
  isLive={isMatchupLive}
/>
```

## Design Tokens

### Color System

```typescript
const colors = {
  // Primary brand colors
  primary: {
    50: '#E3F2FD',
    100: '#BBDEFB',
    500: '#2196F3',
    700: '#1976D2',
    900: '#0D47A1'
  },

  // Status colors
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3',

  // Fantasy-specific colors
  hot: '#FF5722',      // Hot player/trending up
  cold: '#607D8B',     // Cold player/trending down
  injured: '#F44336',  // Injured status
  questionable: '#FF9800', // Questionable status

  // Position colors
  QB: '#9C27B0',
  RB: '#4CAF50',
  WR: '#2196F3',
  TE: '#FF9800',
  K: '#795548',
  DEF: '#424242'
};
```

### Typography

```typescript
const typography = {
  fonts: {
    primary: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    mono: 'Fira Code, Monaco, Consolas, monospace'
  },

  fontSizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem'  // 36px
  },

  fontWeights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },

  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75
  }
};
```

### Spacing

```typescript
const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem'      // 96px
};
```

### Breakpoints

```typescript
const breakpoints = {
  xs: '0px',
  sm: '600px',
  md: '960px',
  lg: '1280px',
  xl: '1920px'
};
```

## Component Guidelines

### Naming Conventions

**Component Names**
- Use PascalCase for component names
- Be descriptive and specific: `PlayerCard` not `Card`
- Include purpose: `DraftTimer` not `Timer`

**Props**
- Use camelCase for prop names
- Boolean props should start with `is`, `has`, or `should`
- Event handlers should start with `on`

```tsx
interface PlayerCardProps {
  player: Player;
  isSelected?: boolean;
  hasNews?: boolean;
  shouldShowProjections?: boolean;
  onSelect?: (player: Player) => void;
  onToggleFavorite?: (playerId: string) => void;
}
```

### Performance Guidelines

**React Best Practices**
- Use React.memo for pure components
- Implement useMemo and useCallback for expensive operations
- Avoid inline objects and functions in render
- Use keys properly in lists

```tsx
const PlayerCard = React.memo<PlayerCardProps>(({
  player,
  onSelect
}) => {
  const handleClick = useCallback(() => {
    onSelect?.(player);
  }, [player, onSelect]);

  const projectionText = useMemo(() => {
    return `${player.projectedPoints.toFixed(1)} pts`;
  }, [player.projectedPoints]);

  return (
    <Card onClick={handleClick}>
      <Text>{player.name}</Text>
      <Text>{projectionText}</Text>
    </Card>
  );
});
```

**Animation Performance**
- Use transform and opacity for animations
- Avoid animating layout properties
- Use will-change sparingly
- Target 60fps on mobile devices

```tsx
const slideIn = keyframes`
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

const AnimatedCard = styled(Card)`
  animation: ${slideIn} 0.3s ease-out;
  will-change: transform, opacity;
`;
```

### Accessibility Guidelines

**Keyboard Navigation**
- All interactive elements must be keyboard accessible
- Provide clear focus indicators
- Implement logical tab order
- Support arrow key navigation for lists

**Screen Readers**
- Use semantic HTML elements
- Provide descriptive alt text for images
- Use aria-labels for complex interactions
- Announce dynamic content changes

```tsx
<Button
  aria-label={`Draft ${player.name}, ${player.position} for ${player.team}`}
  onClick={handleDraft}
>
  Draft
</Button>

<img
  src={player.headshot}
  alt={`${player.name} headshot`}
/>

<div
  role="status"
  aria-live="polite"
  aria-label="Live scoring updates"
>
  {scoreUpdate}
</div>
```

## Testing Guidelines

### Component Testing

**Unit Tests**
- Test component rendering
- Test prop handling
- Test user interactions
- Test accessibility features

```tsx
describe('PlayerCard', () => {
  it('renders player information correctly', () => {
    const player = {
      name: 'Test Player',
      position: 'QB',
      team: 'TEST',
      projectedPoints: 20.5
    };

    render(<PlayerCard player={player} />);

    expect(screen.getByText('Test Player')).toBeInTheDocument();
    expect(screen.getByText('QB')).toBeInTheDocument();
    expect(screen.getByText('20.5 pts')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const handleSelect = jest.fn();
    const player = { /* ... */ };

    render(<PlayerCard player={player} onSelect={handleSelect} />);

    fireEvent.click(screen.getByRole('button'));

    expect(handleSelect).toHaveBeenCalledWith(player);
  });
});
```

**Visual Regression Tests**
- Capture component screenshots
- Test different states and props
- Verify responsive behavior
- Check dark/light theme variations

**Performance Tests**
- Measure component render time
- Test with large datasets
- Verify memory usage
- Check for memory leaks

### Storybook Integration

All components include Storybook stories for:
- Visual documentation
- Interactive testing
- Design review
- Accessibility testing

```tsx
export default {
  title: 'Components/PlayerCard',
  component: PlayerCard,
  parameters: {
    docs: {
      description: {
        component: 'Displays player information with stats and projections'
      }
    }
  }
};

export const Default = {
  args: {
    player: {
      name: 'Mike Trout',
      position: 'OF',
      team: 'LAA',
      projectedPoints: 12.5
    }
  }
};

export const HotPlayer = {
  args: {
    player: {
      ...Default.args.player,
      recentForm: 'hot'
    }
  }
};
```

## Contributing

### Design Process

1. **Design Review**: All new components require design review
2. **Accessibility Audit**: Components must pass accessibility tests
3. **Performance Review**: Components must meet performance targets
4. **Documentation**: Components require complete documentation

### Code Review Checklist

- [ ] Component follows naming conventions
- [ ] Props are properly typed with TypeScript
- [ ] Component is accessible (keyboard navigation, screen readers)
- [ ] Performance optimizations implemented
- [ ] Unit tests with good coverage
- [ ] Storybook stories provided
- [ ] Documentation updated

### Release Process

1. **Development**: Create feature branch from main
2. **Testing**: Run full test suite including visual regression
3. **Review**: Code review and design review
4. **Documentation**: Update component documentation
5. **Release**: Semantic versioning with changelog

## Resources

- [Component Library Storybook](https://storybook.ultimatefantasy.com)
- [Design Figma Files](https://figma.com/ultimate-fantasy-design)
- [Accessibility Guidelines](./accessibility.md)
- [Performance Standards](./performance.md)
- [Contributing Guide](./contributing.md)

---

*This design system is actively maintained and updated. For the latest component documentation and examples, visit our Storybook at storybook.ultimatefantasy.com*