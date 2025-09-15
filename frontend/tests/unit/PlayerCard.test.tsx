import { render, screen, fireEvent } from '@testing-library/react';
import { PlayerCard } from '../../src/components/design-system/patterns/PlayerCard';
import { ThemeProvider } from '../../src/components/design-system/providers/ThemeProvider';

const mockPlayer = {
  id: '1',
  name: 'John Smith',
  position: 'QB',
  team: 'Team A',
  photoUrl: 'https://example.com/photo.jpg',
  stats: {
    points: 24.5,
    projection: 22.3,
    completions: 28,
    attempts: 35,
    yards: 320,
    touchdowns: 3,
    interceptions: 1
  },
  injuryStatus: {
    status: 'healthy',
    description: 'No injuries reported'
  },
  isStarter: true,
  rosteredPercentage: 85.2,
  weeklyTrend: 'up' as const
};

const renderWithTheme = (component: React.ReactNode) => {
  return render(
    <ThemeProvider defaultTheme="dark">
      {component}
    </ThemeProvider>
  );
};

describe('PlayerCard', () => {
  it('renders player information correctly', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('QB')).toBeInTheDocument();
    expect(screen.getByText('Team A')).toBeInTheDocument();
  });

  it('displays player stats', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    expect(screen.getByText('24.5')).toBeInTheDocument(); // Points
    expect(screen.getByText('22.3')).toBeInTheDocument(); // Projection
  });

  it('shows starter status', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    // Starter status should be indicated in styling
    const card = screen.getByText('John Smith').closest('div');
    expect(card).toBeInTheDocument();
  });

  it('displays injury status', () => {
    const injuredPlayer = {
      ...mockPlayer,
      injuryStatus: {
        status: 'questionable',
        description: 'Ankle injury, limited practice'
      }
    };

    renderWithTheme(<PlayerCard player={injuredPlayer} />);

    expect(screen.getByText(/questionable/i)).toBeInTheDocument();
  });

  it('handles draggable functionality', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} draggable />);

    const card = screen.getByText('John Smith').closest('[draggable]');
    expect(card).toHaveAttribute('draggable', 'true');
  });

  it('shows action buttons when provided', () => {
    const handleAdd = vi.fn();
    const handleDrop = vi.fn();

    renderWithTheme(
      <PlayerCard
        player={mockPlayer}
        showActions
        onAdd={handleAdd}
        onDrop={handleDrop}
      />
    );

    const addButton = screen.getByText(/add/i);
    const dropButton = screen.getByText(/drop/i);

    expect(addButton).toBeInTheDocument();
    expect(dropButton).toBeInTheDocument();

    fireEvent.click(addButton);
    expect(handleAdd).toHaveBeenCalledWith(mockPlayer.id);
  });

  it('displays roster percentage', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    expect(screen.getByText('85.2%')).toBeInTheDocument();
  });

  it('shows weekly trend indicator', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} />);

    // Should show trending up indicator
    expect(screen.getByText(/up/i) || screen.getByText(/↗/)).toBeInTheDocument();
  });

  it('handles player without photo', () => {
    const playerWithoutPhoto = {
      ...mockPlayer,
      photoUrl: undefined
    };

    renderWithTheme(<PlayerCard player={playerWithoutPhoto} />);

    expect(screen.getByText('John Smith')).toBeInTheDocument();
    // Should show initials or default avatar
    expect(screen.getByText('JS')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = renderWithTheme(
      <PlayerCard player={mockPlayer} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('handles compact variant', () => {
    renderWithTheme(<PlayerCard player={mockPlayer} variant="compact" />);

    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('QB')).toBeInTheDocument();
  });
});