# Accessibility Guidelines

The Ultimate Fantasy Design System is committed to creating inclusive experiences that work for everyone, regardless of their abilities or assistive technologies used.

## Accessibility Standards

### WCAG 2.1 Compliance

Our components are designed to meet **WCAG 2.1 Level AA** standards, ensuring:

- **Perceivable**: Information and UI components are presentable to users in ways they can perceive
- **Operable**: UI components and navigation are operable by all users
- **Understandable**: Information and operation of UI are understandable
- **Robust**: Content can be interpreted reliably by a wide variety of assistive technologies

### Legal Compliance

Components meet requirements for:
- **ADA (Americans with Disabilities Act)**
- **Section 508** of the Rehabilitation Act
- **EN 301 549** (European accessibility standard)
- **AODA** (Accessibility for Ontarians with Disabilities Act)

## Core Accessibility Features

### Keyboard Navigation

**Full Keyboard Support**
All interactive elements are keyboard accessible using standard navigation patterns:

```tsx
// Example: Button component with keyboard support
<Button
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  }}
>
  Draft Player
</Button>
```

**Navigation Patterns**
- **Tab**: Move forward through interactive elements
- **Shift + Tab**: Move backward through interactive elements
- **Enter/Space**: Activate buttons and links
- **Arrow Keys**: Navigate within lists, menus, and grids
- **Escape**: Close modals, dropdowns, and overlays

**Focus Management**
- Clear focus indicators with 3:1 contrast ratio
- Logical tab order following visual layout
- Focus trapping in modals and overlays
- Focus restoration after modal close

```tsx
// Focus indicator styling
const focusStyles = css`
  &:focus {
    outline: 2px solid ${theme.colors.primary[500]};
    outline-offset: 2px;
  }
`;
```

### Screen Reader Support

**Semantic HTML**
Components use appropriate semantic elements for better screen reader interpretation:

```tsx
// Semantic structure example
<main>
  <section aria-labelledby="standings-title">
    <h2 id="standings-title">League Standings</h2>
    <table role="table">
      <thead>
        <tr>
          <th scope="col">Rank</th>
          <th scope="col">Team</th>
          <th scope="col">Record</th>
        </tr>
      </thead>
      <tbody>
        {teams.map(team => (
          <tr key={team.id}>
            <td>{team.rank}</td>
            <td>{team.name}</td>
            <td>{team.record}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
</main>
```

**ARIA Labels and Descriptions**
Comprehensive labeling for complex interactions:

```tsx
// PlayerCard with descriptive labels
<div
  role="button"
  tabIndex={0}
  aria-labelledby={`${player.id}-name`}
  aria-describedby={`${player.id}-stats ${player.id}-status`}
  onClick={onSelect}
>
  <h3 id={`${player.id}-name`}>{player.name}</h3>
  <div id={`${player.id}-stats`}>
    {player.position} - {player.team}
    Projected: {player.projectedPoints} points
  </div>
  <div id={`${player.id}-status`}>
    Status: {player.injuryStatus}
  </div>
</div>
```

**Live Regions**
Dynamic content updates announced to screen readers:

```tsx
// Live scoring updates
<div
  role="status"
  aria-live="polite"
  aria-label="Live scoring updates"
>
  {scoreUpdate && `${playerName} scored, new total: ${newScore} points`}
</div>

// Urgent notifications
<div
  role="alert"
  aria-live="assertive"
>
  {errorMessage}
</div>
```

### Visual Accessibility

**Color Contrast**
All text meets WCAG contrast requirements:
- **Normal text**: 4.5:1 contrast ratio minimum
- **Large text** (18pt+): 3:1 contrast ratio minimum
- **Interactive elements**: 3:1 contrast ratio for non-text content

```tsx
// Color combinations meeting contrast requirements
const colorPairings = {
  // 4.51:1 ratio
  primaryText: { color: '#1976D2', background: '#FFFFFF' },
  // 7.12:1 ratio
  bodyText: { color: '#2E2E2E', background: '#FFFFFF' },
  // 4.56:1 ratio
  secondaryText: { color: '#616161', background: '#FFFFFF' }
};
```

**Color Independence**
Information is never conveyed through color alone:

```tsx
// Status indicators with icons and text
<StatusIndicator status="injured">
  <WarningIcon aria-hidden="true" />
  <span>Injured</span>
</StatusIndicator>

// Trend indicators with arrows and text
<TrendIndicator direction="up">
  <ArrowUpIcon aria-hidden="true" />
  <span>Trending up (+15%)</span>
</TrendIndicator>
```

**Text Scaling**
Components remain functional at 200% zoom level:

```tsx
// Responsive text sizing
const responsiveText = css`
  font-size: clamp(
    ${theme.fontSizes.sm},
    2.5vw,
    ${theme.fontSizes.lg}
  );
  line-height: 1.5;
`;
```

### Motor Accessibility

**Touch Targets**
Minimum 44px touch targets for mobile interfaces:

```tsx
const TouchTarget = styled.button`
  min-height: 44px;
  min-width: 44px;
  padding: ${theme.spacing[2]} ${theme.spacing[3]};

  // Ensure spacing between adjacent targets
  margin: ${theme.spacing[1]};
`;
```

**Gesture Alternatives**
Complex gestures have simple alternatives:

```tsx
// Drag-and-drop with keyboard alternative
<LineupBuilder
  roster={roster}
  onDrop={handleDrop}
  // Keyboard-accessible move buttons
  onMoveUp={handleMoveUp}
  onMoveDown={handleMoveDown}
  onMoveToPosition={handleMoveToPosition}
/>
```

## Component-Specific Guidelines

### Form Components

**Label Association**
Every form control has an associated label:

```tsx
<FormField>
  <Label htmlFor="team-name">Team Name</Label>
  <Input
    id="team-name"
    value={teamName}
    onChange={setTeamName}
    required
    aria-describedby="team-name-help"
  />
  <HelpText id="team-name-help">
    Choose a unique name for your fantasy team
  </HelpText>
</FormField>
```

**Error Handling**
Clear error communication with proper ARIA attributes:

```tsx
<FormField error={!!errors.email}>
  <Label htmlFor="email">Email Address</Label>
  <Input
    id="email"
    type="email"
    value={email}
    onChange={setEmail}
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-error" : undefined}
  />
  {errors.email && (
    <ErrorMessage id="email-error" role="alert">
      {errors.email}
    </ErrorMessage>
  )}
</FormField>
```

**Required Field Indication**
Required fields clearly indicated visually and programmatically:

```tsx
<Label htmlFor="league-name">
  League Name
  <RequiredIndicator aria-label="required">*</RequiredIndicator>
</Label>
<Input
  id="league-name"
  required
  aria-required="true"
/>
```

### Data Tables

**Table Structure**
Proper table markup with headers and scope:

```tsx
<Table>
  <caption>League Standings - Week 12</caption>
  <thead>
    <tr>
      <th scope="col">Rank</th>
      <th scope="col">Team</th>
      <th scope="col">Record</th>
      <th scope="col">Points For</th>
    </tr>
  </thead>
  <tbody>
    {standings.map(team => (
      <tr key={team.id}>
        <th scope="row">{team.rank}</th>
        <td>{team.name}</td>
        <td>{team.wins}-{team.losses}</td>
        <td>{team.pointsFor}</td>
      </tr>
    ))}
  </tbody>
</Table>
```

**Sortable Tables**
Clear indication of sort state and controls:

```tsx
<th scope="col">
  <button
    onClick={() => handleSort('points')}
    aria-label={`Sort by points ${sortDirection === 'asc' ? 'descending' : 'ascending'}`}
  >
    Points For
    <SortIcon direction={sortDirection} aria-hidden="true" />
  </button>
</th>
```

### Modal Dialogs

**Focus Management**
Proper focus trapping and restoration:

```tsx
const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef();
  const previousFocus = useRef();

  useEffect(() => {
    if (isOpen) {
      previousFocus.current = document.activeElement;
      modalRef.current?.focus();
    } else {
      previousFocus.current?.focus();
    }
  }, [isOpen]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <ModalOverlay
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      ref={modalRef}
      tabIndex={-1}
      onKeyDown={handleKeyDown}
    >
      {children}
    </ModalOverlay>
  );
};
```

### Live Data

**Status Updates**
Real-time updates announced appropriately:

```tsx
// Polite updates for regular scoring
<div role="status" aria-live="polite">
  {lastUpdate && `${playerName}: ${action} - Total: ${totalPoints} points`}
</div>

// Assertive alerts for critical changes
<div role="alert" aria-live="assertive">
  {criticalUpdate && `Alert: ${message}`}
</div>
```

## Testing Guidelines

### Automated Testing

**Jest + Testing Library**
Accessibility tests integrated into component tests:

```tsx
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('PlayerCard Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<PlayerCard player={mockPlayer} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should be keyboard navigable', () => {
    render(<PlayerCard player={mockPlayer} onSelect={mockSelect} />);

    const card = screen.getByRole('button');
    card.focus();

    fireEvent.keyDown(card, { key: 'Enter' });
    expect(mockSelect).toHaveBeenCalled();
  });

  it('should have proper ARIA labels', () => {
    render(<PlayerCard player={mockPlayer} />);

    expect(screen.getByLabelText(/Mike Trout.*OF.*LAA/)).toBeInTheDocument();
  });
});
```

**ESLint Plugin**
Automated linting for accessibility issues:

```json
{
  "extends": ["plugin:jsx-a11y/recommended"],
  "rules": {
    "jsx-a11y/no-autofocus": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/no-static-element-interactions": "error"
  }
}
```

### Manual Testing

**Screen Reader Testing**
Regular testing with:
- **VoiceOver** (macOS/iOS)
- **NVDA** (Windows)
- **JAWS** (Windows)
- **TalkBack** (Android)

**Keyboard Testing Checklist**
- [ ] All interactive elements reachable via Tab
- [ ] Focus indicators visible and clear
- [ ] Logical tab order follows visual layout
- [ ] All actions available via keyboard
- [ ] Escape key works to close overlays
- [ ] Arrow keys work in menus/lists

**Color/Contrast Testing**
- [ ] All text meets contrast requirements
- [ ] Information not conveyed by color alone
- [ ] High contrast mode supported
- [ ] Color blind simulation testing

### Browser Testing

**Assistive Technology Support**
Components tested across:
- Screen readers (NVDA, JAWS, VoiceOver)
- Voice control software (Dragon NaturallySpeaking)
- Switch navigation devices
- Eye-tracking systems

**Browser Compatibility**
Accessibility features verified in:
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Implementation Examples

### Accessible PlayerCard

```tsx
const PlayerCard = ({ player, onSelect, selected = false }) => {
  const cardId = `player-card-${player.id}`;
  const nameId = `${cardId}-name`;
  const statsId = `${cardId}-stats`;
  const statusId = `${cardId}-status`;

  return (
    <Card
      role="button"
      tabIndex={0}
      aria-labelledby={nameId}
      aria-describedby={`${statsId} ${statusId}`}
      aria-pressed={selected}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(player);
        }
      }}
    >
      <PlayerName id={nameId}>
        {player.name}
      </PlayerName>

      <PlayerStats id={statsId}>
        {player.position} - {player.team}
        {player.projectedPoints && (
          <span>Projected: {player.projectedPoints} points</span>
        )}
      </PlayerStats>

      <PlayerStatus id={statusId}>
        <StatusIcon
          status={player.injuryStatus}
          aria-hidden="true"
        />
        <span className="sr-only">
          Injury status: {player.injuryStatus}
        </span>
        {player.injuryStatus !== 'healthy' && (
          <span>{player.injuryStatus}</span>
        )}
      </PlayerStatus>
    </Card>
  );
};
```

### Accessible Data Table

```tsx
const StandingsTable = ({ standings, onSort, sortColumn, sortDirection }) => {
  const getSortLabel = (column) => {
    if (sortColumn === column) {
      return `Sort by ${column} ${sortDirection === 'asc' ? 'descending' : 'ascending'}`;
    }
    return `Sort by ${column}`;
  };

  return (
    <Table>
      <caption>
        League Standings - Current Week
        <VisuallyHidden>
          Table shows team rankings with wins, losses, and points
        </VisuallyHidden>
      </caption>

      <thead>
        <tr>
          <th scope="col">
            <SortButton
              onClick={() => onSort('rank')}
              aria-label={getSortLabel('rank')}
            >
              Rank
              <SortIcon
                direction={sortColumn === 'rank' ? sortDirection : null}
                aria-hidden="true"
              />
            </SortButton>
          </th>
          <th scope="col">Team</th>
          <th scope="col">Record</th>
          <th scope="col">
            <SortButton
              onClick={() => onSort('points')}
              aria-label={getSortLabel('points')}
            >
              Points For
              <SortIcon
                direction={sortColumn === 'points' ? sortDirection : null}
                aria-hidden="true"
              />
            </SortButton>
          </th>
        </tr>
      </thead>

      <tbody>
        {standings.map((team, index) => (
          <tr key={team.id}>
            <th scope="row">{team.rank}</th>
            <td>
              <TeamName>
                {team.name}
                <OwnerName>({team.owner})</OwnerName>
              </TeamName>
            </td>
            <td>{team.wins}-{team.losses}</td>
            <td>{team.pointsFor}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
```

## Resources and Tools

### Testing Tools

**Automated Testing**
- [axe-core](https://github.com/dequelabs/axe-core) - Accessibility testing engine
- [jest-axe](https://github.com/nickcolley/jest-axe) - Jest integration for axe
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) - ESLint rules

**Browser Extensions**
- [axe DevTools](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd) - Chrome/Firefox extension
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Built into Chrome DevTools
- [WAVE](https://wave.webaim.org/extension/) - Web accessibility evaluation

**Color/Contrast Tools**
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)
- [Stark](https://www.getstark.co/) - Design tool plugin

### Documentation

**Standards and Guidelines**
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/resources/)
- [A11Y Project](https://www.a11yproject.com/)

**Component Patterns**
- [ARIA Design Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [Inclusive Components](https://inclusive-components.design/)
- [GOV.UK Design System](https://design-system.service.gov.uk/)

---

*Accessibility is an ongoing commitment. If you discover accessibility issues or have suggestions for improvement, please [report them](https://github.com/ultimate-fantasy/ui-components/issues) so we can address them promptly.*