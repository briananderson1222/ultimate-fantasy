import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import { PlayerCard } from '../../src/components/design-system/patterns/PlayerCard';
import { ThemeProvider } from '../../src/components/design-system/providers/ThemeProvider';

const mockPlayer = {
  id: '1',
  name: 'John Smith',
  position: 'QB',
  team: 'Team A',
  points: 24.5,
  projection: 22.3,
  status: 'active' as const,
  isStarter: true,
  injuryStatus: null,
  news: 'Expected to have a big game this week.'
};

const mockBenchPlayer = {
  id: '2',
  name: 'Mike Johnson',
  position: 'RB',
  team: 'Team B',
  points: 18.2,
  projection: 19.5,
  status: 'active' as const,
  isStarter: false,
  injuryStatus: 'Questionable',
  news: 'Dealing with minor ankle injury.'
};

// Mock roster management component
const MockRosterManager = () => {
  const [starters, setStarters] = React.useState([mockPlayer]);
  const [bench, setBench] = React.useState([mockBenchPlayer]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) return;

    const activePlayer = [...starters, ...bench].find(p => p.id === active.id);
    if (!activePlayer) return;

    if (over.id === 'starters' && !activePlayer.isStarter) {
      // Move to starters
      setBench(prev => prev.filter(p => p.id !== activePlayer.id));
      setStarters(prev => [...prev, { ...activePlayer, isStarter: true }]);
    } else if (over.id === 'bench' && activePlayer.isStarter) {
      // Move to bench
      setStarters(prev => prev.filter(p => p.id !== activePlayer.id));
      setBench(prev => [...prev, { ...activePlayer, isStarter: false }]);
    }
  };

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="grid grid-cols-2 gap-4">
        <div data-testid="starters" id="starters">
          <h3>Starters</h3>
          {starters.map(player => (
            <PlayerCard key={player.id} player={player} draggable />
          ))}
        </div>
        <div data-testid="bench" id="bench">
          <h3>Bench</h3>
          {bench.map(player => (
            <PlayerCard key={player.id} player={player} draggable />
          ))}
        </div>
      </div>
    </DndContext>
  );
};

describe('Player Management Integration', () => {
  const renderWithTheme = (component: React.ReactNode) => {
    return render(
      <ThemeProvider defaultTheme="dark">
        {component}
      </ThemeProvider>
    );
  };

  it('should display player cards with correct information', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    // Check player details
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('QB')).toBeInTheDocument();
    expect(screen.getByText('Team A')).toBeInTheDocument();
    expect(screen.getByText('24.5')).toBeInTheDocument();
    expect(screen.getByText('22.3')).toBeInTheDocument();
  });

  it('should show injury status when present', () => {
    renderWithTheme(<PlayerCard player={mockBenchPlayer} />);

    expect(screen.getByText('Questionable')).toBeInTheDocument();
  });

  it('should distinguish between starters and bench players', () => {
    const { container: starterContainer } = renderWithTheme(
      <PlayerCard player={mockPlayer} />
    );
    const { container: benchContainer } = renderWithTheme(
      <PlayerCard player={mockBenchPlayer} />
    );

    // Starter should have different styling
    expect(starterContainer.querySelector('.ring-success')).toBeInTheDocument();
    expect(benchContainer.querySelector('.ring-success')).not.toBeInTheDocument();
  });

  it('should support drag and drop for roster management', async () => {
    renderWithTheme(<MockRosterManager />);

    // Initially, John Smith should be in starters
    const startersSection = screen.getByTestId('starters');
    expect(startersSection).toHaveTextContent('John Smith');

    // Mike Johnson should be in bench
    const benchSection = screen.getByTestId('bench');
    expect(benchSection).toHaveTextContent('Mike Johnson');

    // Test drag and drop (simulation)
    const mikeCard = screen.getByText('Mike Johnson').closest('[draggable="true"]');

    if (mikeCard) {
      fireEvent.dragStart(mikeCard);
      fireEvent.dragEnter(startersSection);
      fireEvent.dragOver(startersSection);
      fireEvent.drop(startersSection);
      fireEvent.dragEnd(mikeCard);
    }

    // Wait for state update
    await waitFor(() => {
      expect(startersSection).toHaveTextContent('Mike Johnson');
    });
  });

  it('should show performance indicators correctly', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    // Should show points vs projection comparison
    expect(screen.getByText('24.5')).toBeInTheDocument(); // Actual points
    expect(screen.getByText('22.3')).toBeInTheDocument(); // Projected points

    // Should indicate outperforming projection (24.5 > 22.3)
    const pointsElement = screen.getByText('24.5');
    expect(pointsElement.closest('div')).toHaveClass('text-success');
  });

  it('should handle different player statuses', () => {
    const injuredPlayer = {
      ...mockPlayer,
      status: 'injured' as const,
      injuryStatus: 'Out'
    };

    renderWithTheme(<PlayerCard player={injuredPlayer} />);

    expect(screen.getByText('Out')).toBeInTheDocument();
  });

  it('should provide visual feedback for drag operations', async () => {
    renderWithTheme(<MockRosterManager />);

    const playerCard = screen.getByText('John Smith').closest('[draggable="true"]');

    if (playerCard) {
      fireEvent.dragStart(playerCard);

      // Should show drag preview or visual feedback
      expect(playerCard).toHaveClass('dragging');

      fireEvent.dragEnd(playerCard);
    }
  });

  it('should be accessible with proper ARIA attributes', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} draggable />);

    const playerCard = screen.getByRole('button');
    expect(playerCard).toHaveAttribute('aria-label');
    expect(playerCard).toHaveAttribute('draggable', 'true');
  });

  it('should show news and updates when available', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    expect(screen.getByText('Expected to have a big game this week.')).toBeInTheDocument();
  });
});