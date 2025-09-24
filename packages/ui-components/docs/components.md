# Component Library Reference

This document provides comprehensive documentation for all components in the Ultimate Fantasy Design System.

## Layout Components

### Container

Provides consistent spacing and alignment across the application with responsive behavior.

#### Usage

```tsx
import { Container } from '@ultimate-fantasy/ui-components';

<Container maxWidth="lg" padding="medium">
  <YourContent />
</Container>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `maxWidth` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl' \| 'fluid'` | `'lg'` | Maximum width of the container |
| `padding` | `'none' \| 'small' \| 'medium' \| 'large'` | `'medium'` | Internal padding |
| `centered` | `boolean` | `true` | Whether to center the container |
| `children` | `ReactNode` | - | Content to be contained |

#### Examples

```tsx
// Fluid width container with no padding
<Container maxWidth="fluid" padding="none">
  <FullWidthComponent />
</Container>

// Centered container with large padding
<Container maxWidth="md" padding="large" centered>
  <CenteredContent />
</Container>
```

---

### Grid

Flexible grid system based on CSS Grid with responsive breakpoints.

#### Usage

```tsx
import { Grid } from '@ultimate-fantasy/ui-components';

<Grid container spacing={2}>
  <Grid item xs={12} md={6} lg={4}>
    <Card>Item 1</Card>
  </Grid>
  <Grid item xs={12} md={6} lg={4}>
    <Card>Item 2</Card>
  </Grid>
</Grid>
```

#### Container Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `container` | `boolean` | `false` | Creates a grid container |
| `spacing` | `number \| object` | `0` | Spacing between grid items |
| `direction` | `'row' \| 'column'` | `'row'` | Grid direction |
| `wrap` | `'nowrap' \| 'wrap'` | `'wrap'` | Grid wrapping behavior |

#### Item Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `item` | `boolean` | `false` | Creates a grid item |
| `xs` | `number \| 'auto'` | - | Columns on extra small screens |
| `sm` | `number \| 'auto'` | - | Columns on small screens |
| `md` | `number \| 'auto'` | - | Columns on medium screens |
| `lg` | `number \| 'auto'` | - | Columns on large screens |
| `xl` | `number \| 'auto'` | - | Columns on extra large screens |

---

### Stack

Vertical or horizontal stacking with consistent spacing between elements.

#### Usage

```tsx
import { Stack } from '@ultimate-fantasy/ui-components';

<Stack direction="column" spacing={3} align="center">
  <PlayerCard player={player1} />
  <PlayerCard player={player2} />
  <PlayerCard player={player3} />
</Stack>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `direction` | `'row' \| 'column'` | `'column'` | Stack direction |
| `spacing` | `number` | `2` | Spacing between items |
| `align` | `'start' \| 'center' \| 'end' \| 'stretch'` | `'stretch'` | Cross-axis alignment |
| `justify` | `'start' \| 'center' \| 'end' \| 'between' \| 'around'` | `'start'` | Main-axis alignment |
| `wrap` | `boolean` | `false` | Allow items to wrap |

## Input Components

### Button

Consistent button component with multiple variants and states.

#### Usage

```tsx
import { Button } from '@ultimate-fantasy/ui-components';

<Button
  variant="primary"
  size="large"
  onClick={handleClick}
  loading={isLoading}
>
  Submit Lineup
</Button>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'danger'` | `'primary'` | Button style variant |
| `size` | `'small' \| 'medium' \| 'large'` | `'medium'` | Button size |
| `loading` | `boolean` | `false` | Shows loading spinner |
| `disabled` | `boolean` | `false` | Disables the button |
| `fullWidth` | `boolean` | `false` | Makes button full width |
| `startIcon` | `ReactNode` | - | Icon before text |
| `endIcon` | `ReactNode` | - | Icon after text |
| `onClick` | `() => void` | - | Click handler |

#### Examples

```tsx
// Primary action button
<Button variant="primary" size="large">
  Draft Player
</Button>

// Danger button for destructive actions
<Button variant="danger" onClick={handleDelete}>
  Drop Player
</Button>

// Loading state
<Button loading onClick={handleSubmit}>
  Submitting...
</Button>

// With icons
<Button startIcon={<AddIcon />}>
  Add Player
</Button>
```

---

### SearchInput

Optimized search input with debouncing, suggestions, and filtering.

#### Usage

```tsx
import { SearchInput } from '@ultimate-fantasy/ui-components';

<SearchInput
  placeholder="Search players..."
  value={searchQuery}
  onChange={setSearchQuery}
  onSearch={handleSearch}
  suggestions={playerSuggestions}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `placeholder` | `string` | - | Input placeholder text |
| `value` | `string` | - | Current search value |
| `onChange` | `(value: string) => void` | - | Value change handler |
| `onSearch` | `(query: string) => void` | - | Search submission handler |
| `suggestions` | `Suggestion[]` | `[]` | Auto-complete suggestions |
| `debounceMs` | `number` | `300` | Debounce delay in milliseconds |
| `loading` | `boolean` | `false` | Shows loading state |
| `clearable` | `boolean` | `true` | Shows clear button |

#### Suggestion Interface

```tsx
interface Suggestion {
  id: string;
  label: string;
  value: string;
  category?: string;
  metadata?: Record<string, any>;
}
```

---

### SelectInput

Dropdown selection component with filtering and multi-select capabilities.

#### Usage

```tsx
import { SelectInput } from '@ultimate-fantasy/ui-components';

<SelectInput
  label="Position"
  options={positionOptions}
  value={selectedPosition}
  onChange={setSelectedPosition}
  searchable
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Field label |
| `options` | `Option[]` | `[]` | Available options |
| `value` | `string \| string[]` | - | Selected value(s) |
| `onChange` | `(value: string \| string[]) => void` | - | Selection change handler |
| `multiple` | `boolean` | `false` | Allow multiple selections |
| `searchable` | `boolean` | `false` | Enable option filtering |
| `clearable` | `boolean` | `false` | Show clear button |
| `disabled` | `boolean` | `false` | Disable the input |
| `placeholder` | `string` | - | Placeholder text |

#### Option Interface

```tsx
interface Option {
  value: string;
  label: string;
  disabled?: boolean;
  group?: string;
}
```

## Data Display Components

### PlayerCard

Displays player information with stats, projections, and interactive elements.

#### Usage

```tsx
import { PlayerCard } from '@ultimate-fantasy/ui-components';

<PlayerCard
  player={player}
  showProjections
  showNews
  onSelect={handlePlayerSelect}
  onToggleFavorite={handleToggleFavorite}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `player` | `Player` | - | Player data object |
| `variant` | `'default' \| 'compact' \| 'detailed'` | `'default'` | Card layout variant |
| `showProjections` | `boolean` | `true` | Display fantasy projections |
| `showNews` | `boolean` | `false` | Show news indicator |
| `showTrends` | `boolean` | `false` | Display trend indicators |
| `interactive` | `boolean` | `true` | Enable click interactions |
| `selected` | `boolean` | `false` | Show selected state |
| `favorited` | `boolean` | `false` | Show favorited state |
| `onSelect` | `(player: Player) => void` | - | Selection handler |
| `onToggleFavorite` | `(playerId: string) => void` | - | Favorite toggle handler |

#### Player Interface

```tsx
interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  projectedPoints?: number;
  recentForm?: 'hot' | 'cold' | 'average';
  injuryStatus?: 'healthy' | 'questionable' | 'doubtful' | 'out';
  trends?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
  news?: {
    hasUpdate: boolean;
    impact: 'positive' | 'negative' | 'neutral';
  };
}
```

#### Examples

```tsx
// Compact card for lists
<PlayerCard
  player={player}
  variant="compact"
  showProjections={false}
/>

// Detailed card with all features
<PlayerCard
  player={player}
  variant="detailed"
  showProjections
  showNews
  showTrends
  onSelect={handleDraft}
/>
```

---

### StatCard

Displays statistical information with trends and comparisons.

#### Usage

```tsx
import { StatCard } from '@ultimate-fantasy/ui-components';

<StatCard
  title="Fantasy Points"
  value={125.7}
  trend="+12.3"
  trendDirection="up"
  subtitle="This week"
  format="decimal"
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Stat title/label |
| `value` | `number \| string` | - | Primary stat value |
| `subtitle` | `string` | - | Additional context |
| `trend` | `string` | - | Trend indicator text |
| `trendDirection` | `'up' \| 'down' \| 'neutral'` | - | Trend direction |
| `format` | `'number' \| 'decimal' \| 'percentage' \| 'currency'` | `'number'` | Value formatting |
| `size` | `'small' \| 'medium' \| 'large'` | `'medium'` | Card size |
| `color` | `'primary' \| 'success' \| 'warning' \| 'error'` | `'primary'` | Color theme |

---

### LeaderboardItem

Displays ranking information with team/player details and statistics.

#### Usage

```tsx
import { LeaderboardItem } from '@ultimate-fantasy/ui-components';

<LeaderboardItem
  rank={1}
  team={team}
  stats={teamStats}
  isCurrentUser
  onSelect={handleTeamSelect}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rank` | `number` | - | Current ranking position |
| `team` | `Team` | - | Team information |
| `stats` | `TeamStats` | - | Team statistics |
| `isCurrentUser` | `boolean` | `false` | Highlight as current user |
| `interactive` | `boolean` | `true` | Enable click interactions |
| `showTrend` | `boolean` | `false` | Show ranking trend |
| `onSelect` | `(team: Team) => void` | - | Selection handler |

#### Team Interface

```tsx
interface Team {
  id: string;
  name: string;
  owner: string;
  avatar?: string;
  record: {
    wins: number;
    losses: number;
    ties?: number;
  };
}

interface TeamStats {
  pointsFor: number;
  pointsAgainst: number;
  averagePoints: number;
  streak?: {
    type: 'W' | 'L';
    length: number;
  };
}
```

## Fantasy-Specific Components

### DraftBoard

Interactive draft board showing all picks with real-time updates.

#### Usage

```tsx
import { DraftBoard } from '@ultimate-fantasy/ui-components';

<DraftBoard
  picks={draftPicks}
  teams={teams}
  currentPick={currentPickNumber}
  userTeam={userTeamId}
  isLive
  onPickSelect={handlePickSelect}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `picks` | `DraftPick[]` | `[]` | All draft picks |
| `teams` | `Team[]` | `[]` | Draft teams |
| `currentPick` | `number` | - | Current pick number |
| `userTeam` | `string` | - | User's team ID |
| `isLive` | `boolean` | `false` | Real-time draft mode |
| `showTimer` | `boolean` | `true` | Display pick timer |
| `compact` | `boolean` | `false` | Compact view mode |
| `onPickSelect` | `(pick: DraftPick) => void` | - | Pick selection handler |

#### DraftPick Interface

```tsx
interface DraftPick {
  pickNumber: number;
  round: number;
  teamId: string;
  playerId?: string;
  playerName?: string;
  position?: string;
  pickedAt?: Date;
  timeUsed?: number;
}
```

---

### LineupBuilder

Drag-and-drop interface for constructing lineups with position validation.

#### Usage

```tsx
import { LineupBuilder } from '@ultimate-fantasy/ui-components';

<LineupBuilder
  roster={playerRoster}
  lineup={currentLineup}
  positionRequirements={positionReqs}
  onChange={handleLineupChange}
  optimizationSuggestions={suggestions}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `roster` | `Player[]` | `[]` | Available players |
| `lineup` | `LineupSlot[]` | `[]` | Current lineup |
| `positionRequirements` | `PositionRequirement[]` | `[]` | League position rules |
| `onChange` | `(lineup: LineupSlot[]) => void` | - | Lineup change handler |
| `optimizationSuggestions` | `OptimizationSuggestion[]` | `[]` | AI suggestions |
| `dragEnabled` | `boolean` | `true` | Enable drag-and-drop |
| `showProjections` | `boolean` | `true` | Display projections |
| `readOnly` | `boolean` | `false` | Disable editing |

#### LineupSlot Interface

```tsx
interface LineupSlot {
  position: string;
  playerId?: string;
  player?: Player;
  isFlexible?: boolean;
  eligiblePositions?: string[];
}

interface PositionRequirement {
  position: string;
  count: number;
  eligiblePositions?: string[];
}

interface OptimizationSuggestion {
  type: 'swap' | 'start' | 'bench';
  reason: string;
  expectedImprovement: number;
  confidence: number;
  fromSlot?: number;
  toSlot?: number;
  playerId: string;
}
```

---

### TradeAnalyzer

Comprehensive trade evaluation with fairness analysis and recommendations.

#### Usage

```tsx
import { TradeAnalyzer } from '@ultimate-fantasy/ui-components';

<TradeAnalyzer
  trade={tradeProposal}
  analysis={aiAnalysis}
  userTeam={userTeamId}
  onAccept={handleAccept}
  onReject={handleReject}
  onCounter={handleCounter}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `trade` | `Trade` | - | Trade proposal data |
| `analysis` | `TradeAnalysis` | - | AI analysis results |
| `userTeam` | `string` | - | Current user's team ID |
| `showDetailed` | `boolean` | `true` | Show detailed analysis |
| `allowActions` | `boolean` | `true` | Enable action buttons |
| `onAccept` | `() => void` | - | Accept handler |
| `onReject` | `() => void` | - | Reject handler |
| `onCounter` | `() => void` | - | Counter-offer handler |

#### Trade Interface

```tsx
interface Trade {
  id: string;
  proposer: {
    teamId: string;
    teamName: string;
    players: Player[];
  };
  recipient: {
    teamId: string;
    teamName: string;
    players: Player[];
  };
  status: 'proposed' | 'accepted' | 'rejected' | 'expired';
  expiresAt: Date;
}

interface TradeAnalysis {
  fairnessRating: 'heavily_favors_proposer' | 'favors_proposer' | 'fair' | 'favors_recipient' | 'heavily_favors_recipient';
  valueGap: number;
  confidence: number;
  recommendation: 'accept' | 'reject' | 'consider' | 'counter';
  factors: string[];
  rosterImpact: {
    proposer: RosterImpact;
    recipient: RosterImpact;
  };
}
```

---

### MatchupPreview

Head-to-head matchup display with live scoring and projections.

#### Usage

```tsx
import { MatchupPreview } from '@ultimate-fantasy/ui-components';

<MatchupPreview
  matchup={weeklyMatchup}
  isLive={isGameDay}
  showProjections
  onTeamSelect={handleTeamView}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `matchup` | `Matchup` | - | Matchup data |
| `isLive` | `boolean` | `false` | Live scoring mode |
| `showProjections` | `boolean` | `true` | Display projections |
| `showDetails` | `boolean` | `false` | Expanded view |
| `interactive` | `boolean` | `true` | Enable interactions |
| `onTeamSelect` | `(teamId: string) => void` | - | Team selection handler |

#### Matchup Interface

```tsx
interface Matchup {
  id: string;
  week: number;
  teams: [MatchupTeam, MatchupTeam];
  status: 'upcoming' | 'live' | 'completed';
  winProbability?: [number, number];
}

interface MatchupTeam {
  teamId: string;
  teamName: string;
  owner: string;
  score: number;
  projectedScore: number;
  lineup: LineupSlot[];
  isUser?: boolean;
}
```

## Feedback Components

### Toast

Displays temporary notification messages with different severity levels.

#### Usage

```tsx
import { useToast } from '@ultimate-fantasy/ui-components';

const { showToast } = useToast();

// Show success message
showToast({
  title: 'Lineup Submitted',
  message: 'Your lineup has been successfully submitted for Week 12',
  type: 'success',
  duration: 5000
});
```

#### Toast Options

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Toast title |
| `message` | `string` | - | Toast message |
| `type` | `'success' \| 'error' \| 'warning' \| 'info'` | `'info'` | Toast type |
| `duration` | `number` | `4000` | Auto-dismiss time (ms) |
| `action` | `ToastAction` | - | Optional action button |
| `persistent` | `boolean` | `false` | Prevent auto-dismiss |

---

### Modal

Overlay dialog for complex interactions and forms.

#### Usage

```tsx
import { Modal } from '@ultimate-fantasy/ui-components';

<Modal
  isOpen={isModalOpen}
  onClose={closeModal}
  title="Trade Proposal"
  size="large"
>
  <TradeForm onSubmit={handleTradeSubmit} />
</Modal>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `isOpen` | `boolean` | `false` | Modal visibility |
| `onClose` | `() => void` | - | Close handler |
| `title` | `string` | - | Modal title |
| `size` | `'small' \| 'medium' \| 'large' \| 'fullscreen'` | `'medium'` | Modal size |
| `closeOnOverlay` | `boolean` | `true` | Close on backdrop click |
| `closeOnEscape` | `boolean` | `true` | Close on escape key |
| `showHeader` | `boolean` | `true` | Show header with title |
| `actions` | `ReactNode` | - | Footer action buttons |

## Styling and Theming

### CSS-in-JS with Styled Components

All components use styled-components for styling with theme support.

```tsx
import styled from 'styled-components';
import { theme } from '@ultimate-fantasy/design-tokens';

const StyledButton = styled.button<{ variant: string }>`
  padding: ${theme.spacing[3]} ${theme.spacing[4]};
  font-family: ${theme.fonts.primary};
  font-size: ${theme.fontSizes.base};
  border-radius: ${theme.borderRadius.md};

  background-color: ${props =>
    props.variant === 'primary'
      ? theme.colors.primary[500]
      : theme.colors.gray[100]
  };

  &:hover {
    background-color: ${props =>
      props.variant === 'primary'
        ? theme.colors.primary[600]
        : theme.colors.gray[200]
    };
  }
`;
```

### Dark Mode Support

All components automatically support dark mode through the theme provider.

```tsx
import { ThemeProvider } from '@ultimate-fantasy/ui-components';

function App() {
  const [darkMode, setDarkMode] = useState(false);

  return (
    <ThemeProvider theme={darkMode ? 'dark' : 'light'}>
      <YourApp />
    </ThemeProvider>
  );
}
```

---

*For the latest component APIs and examples, visit our [Storybook documentation](https://storybook.ultimatefantasy.com)*