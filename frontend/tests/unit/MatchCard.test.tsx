import { render, screen, fireEvent } from '@testing-library/react';
import { MatchCard } from '../../src/components/design-system/patterns/MatchCard';
import { ThemeProvider } from '../../src/components/design-system/providers/ThemeProvider';

const mockMatch = {
  homeTeam: {
    id: '1',
    name: 'Team Alpha',
    owner: 'Alice Johnson',
    record: { wins: 8, losses: 4 }
  },
  awayTeam: {
    id: '2',
    name: 'Team Beta',
    owner: 'Bob Smith',
    record: { wins: 6, losses: 6 }
  },
  week: 8,
  status: 'completed' as const,
  actualPoints: {
    home: 120.5,
    away: 95.3
  }
};

const renderWithTheme = (component: React.ReactNode) => {
  return render(
    <ThemeProvider defaultTheme="dark">
      {component}
    </ThemeProvider>
  );
};

describe('MatchCard', () => {
  it('renders match information correctly', () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    expect(screen.getByText('Team Beta')).toBeInTheDocument();
    expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
    expect(screen.getByText('Bob Smith')).toBeInTheDocument();
  });

  it('displays scores for completed match', () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    expect(screen.getByText('120.5')).toBeInTheDocument();
    expect(screen.getByText('95.3')).toBeInTheDocument();
  });

  it('displays team records', () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    expect(screen.getByText('8-4')).toBeInTheDocument();
    expect(screen.getByText('6-6')).toBeInTheDocument();
  });

  it('displays week information', () => {
    renderWithTheme(<MatchCard match={mockMatch} />);

    expect(screen.getByText(/Week 8/)).toBeInTheDocument();
  });

  it('handles click events when onClick is provided', () => {
    const handleClick = vi.fn();
    renderWithTheme(<MatchCard match={mockMatch} onClick={handleClick} />);

    const card = screen.getByText('Team Alpha').closest('div');
    if (card) {
      fireEvent.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1);
    }
  });

  it('shows details button when enabled', () => {
    renderWithTheme(<MatchCard match={mockMatch} showDetailsButton />);

    expect(screen.getByText(/details/i)).toBeInTheDocument();
  });

  it('handles upcoming match correctly', () => {
    const upcomingMatch = {
      ...mockMatch,
      status: 'upcoming' as const,
      actualPoints: undefined,
      projectedPoints: {
        home: 115.2,
        away: 108.7
      }
    };

    renderWithTheme(<MatchCard match={upcomingMatch} />);

    expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    expect(screen.getByText('Team Beta')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = renderWithTheme(
      <MatchCard match={mockMatch} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('displays playoff implications when provided', () => {
    const matchWithImplications = {
      ...mockMatch,
      playoffImplications: 'Winner advances to playoffs'
    };

    renderWithTheme(<MatchCard match={matchWithImplications} />);

    expect(screen.getByText('Winner advances to playoffs')).toBeInTheDocument();
  });
});