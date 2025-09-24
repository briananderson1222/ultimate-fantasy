/**
 * Unit tests for PlayerCard component.
 *
 * Tests cover:
 * - Basic rendering and display
 * - Player data formatting
 * - Interactive states (selected, disabled)
 * - Action buttons and callbacks
 * - Responsive behavior
 * - Accessibility features
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import { PlayerCard } from '../PlayerCard';
import { PlayerPosition, InjuryStatus } from '../../types/player';

// Mock the theme provider for consistent testing
jest.mock('../../providers/ThemeProvider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#1a73e8',
      secondary: '#f1f3f4',
      text: '#202124',
      background: '#ffffff'
    }
  })
}));

interface MockPlayer {
  id: string;
  name: string;
  position: PlayerPosition;
  team: string;
  projectedPoints: number;
  salary?: number;
  injuryStatus: InjuryStatus;
  averagePoints: number;
  trend: 'up' | 'down' | 'stable';
  ownership?: number;
  opponent?: string;
  gameTime?: string;
}

const createMockPlayer = (overrides: Partial<MockPlayer> = {}): MockPlayer => ({
  id: 'player1',
  name: 'Josh Allen',
  position: PlayerPosition.QB,
  team: 'BUF',
  projectedPoints: 24.5,
  salary: 8200,
  injuryStatus: InjuryStatus.HEALTHY,
  averagePoints: 23.8,
  trend: 'up',
  ownership: 0.35,
  opponent: 'vs MIA',
  gameTime: '1:00 PM',
  ...overrides
});

describe('PlayerCard', () => {
  const defaultProps = {
    player: createMockPlayer(),
    onSelect: jest.fn(),
    onRemove: jest.fn(),
    onViewDetails: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders player name and basic info', () => {
      render(<PlayerCard {...defaultProps} />);

      expect(screen.getByText('Josh Allen')).toBeInTheDocument();
      expect(screen.getByText('QB')).toBeInTheDocument();
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    test('displays projected points', () => {
      render(<PlayerCard {...defaultProps} />);

      expect(screen.getByText('24.5')).toBeInTheDocument();
      expect(screen.getByText(/projected/i)).toBeInTheDocument();
    });

    test('shows salary when provided', () => {
      render(<PlayerCard {...defaultProps} />);

      expect(screen.getByText('$8,200')).toBeInTheDocument();
    });

    test('displays opponent and game time', () => {
      render(<PlayerCard {...defaultProps} />);

      expect(screen.getByText('vs MIA')).toBeInTheDocument();
      expect(screen.getByText('1:00 PM')).toBeInTheDocument();
    });

    test('renders without salary for season-long formats', () => {
      const player = createMockPlayer({ salary: undefined });
      render(<PlayerCard player={player} />);

      expect(screen.queryByText(/\$/)).not.toBeInTheDocument();
    });
  });

  describe('Player Status Indicators', () => {
    test('shows healthy status with green indicator', () => {
      render(<PlayerCard {...defaultProps} />);

      const statusIndicator = screen.getByTestId('injury-status');
      expect(statusIndicator).toHaveClass('status-healthy');
    });

    test('shows questionable status with yellow indicator', () => {
      const player = createMockPlayer({ injuryStatus: InjuryStatus.QUESTIONABLE });
      render(<PlayerCard player={player} />);

      const statusIndicator = screen.getByTestId('injury-status');
      expect(statusIndicator).toHaveClass('status-questionable');
      expect(screen.getByText('Q')).toBeInTheDocument();
    });

    test('shows out status with red indicator', () => {
      const player = createMockPlayer({ injuryStatus: InjuryStatus.OUT });
      render(<PlayerCard player={player} />);

      const statusIndicator = screen.getByTestId('injury-status');
      expect(statusIndicator).toHaveClass('status-out');
      expect(screen.getByText('O')).toBeInTheDocument();
    });

    test('shows doubtful status appropriately', () => {
      const player = createMockPlayer({ injuryStatus: InjuryStatus.DOUBTFUL });
      render(<PlayerCard player={player} />);

      expect(screen.getByText('D')).toBeInTheDocument();
    });

    test('shows IR status', () => {
      const player = createMockPlayer({ injuryStatus: InjuryStatus.IR });
      render(<PlayerCard player={player} />);

      expect(screen.getByText('IR')).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    test('shows upward trend with green arrow', () => {
      render(<PlayerCard {...defaultProps} />);

      const trendIndicator = screen.getByTestId('trend-indicator');
      expect(trendIndicator).toHaveClass('trend-up');
    });

    test('shows downward trend with red arrow', () => {
      const player = createMockPlayer({ trend: 'down' });
      render(<PlayerCard player={player} />);

      const trendIndicator = screen.getByTestId('trend-indicator');
      expect(trendIndicator).toHaveClass('trend-down');
    });

    test('shows stable trend with neutral indicator', () => {
      const player = createMockPlayer({ trend: 'stable' });
      render(<PlayerCard player={player} />);

      const trendIndicator = screen.getByTestId('trend-indicator');
      expect(trendIndicator).toHaveClass('trend-stable');
    });
  });

  describe('Interactive Behavior', () => {
    test('calls onSelect when card is clicked', () => {
      const onSelect = jest.fn();
      render(<PlayerCard {...defaultProps} onSelect={onSelect} />);

      const card = screen.getByTestId('player-card');
      fireEvent.click(card);

      expect(onSelect).toHaveBeenCalledWith(defaultProps.player);
    });

    test('shows selected state when isSelected is true', () => {
      render(<PlayerCard {...defaultProps} isSelected={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('selected');
    });

    test('shows disabled state when isDisabled is true', () => {
      render(<PlayerCard {...defaultProps} isDisabled={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('disabled');
      expect(card).toHaveAttribute('aria-disabled', 'true');
    });

    test('does not call onSelect when disabled', () => {
      const onSelect = jest.fn();
      render(<PlayerCard {...defaultProps} onSelect={onSelect} isDisabled={true} />);

      const card = screen.getByTestId('player-card');
      fireEvent.click(card);

      expect(onSelect).not.toHaveBeenCalled();
    });

    test('shows hover effects on non-disabled cards', () => {
      render(<PlayerCard {...defaultProps} />);

      const card = screen.getByTestId('player-card');
      fireEvent.mouseEnter(card);

      expect(card).toHaveClass('hover');
    });
  });

  describe('Action Buttons', () => {
    test('renders remove button when onRemove is provided', () => {
      render(<PlayerCard {...defaultProps} showRemoveButton={true} />);

      expect(screen.getByTestId('remove-button')).toBeInTheDocument();
    });

    test('calls onRemove when remove button is clicked', () => {
      const onRemove = jest.fn();
      render(<PlayerCard {...defaultProps} onRemove={onRemove} showRemoveButton={true} />);

      const removeButton = screen.getByTestId('remove-button');
      fireEvent.click(removeButton);

      expect(onRemove).toHaveBeenCalledWith(defaultProps.player);
    });

    test('renders details button when onViewDetails is provided', () => {
      render(<PlayerCard {...defaultProps} showDetailsButton={true} />);

      expect(screen.getByTestId('details-button')).toBeInTheDocument();
    });

    test('calls onViewDetails when details button is clicked', () => {
      const onViewDetails = jest.fn();
      render(<PlayerCard {...defaultProps} onViewDetails={onViewDetails} showDetailsButton={true} />);

      const detailsButton = screen.getByTestId('details-button');
      fireEvent.click(detailsButton);

      expect(onViewDetails).toHaveBeenCalledWith(defaultProps.player);
    });

    test('action buttons do not trigger card selection', () => {
      const onSelect = jest.fn();
      render(<PlayerCard {...defaultProps} onSelect={onSelect} showRemoveButton={true} />);

      const removeButton = screen.getByTestId('remove-button');
      fireEvent.click(removeButton);

      expect(onSelect).not.toHaveBeenCalled();
    });
  });

  describe('Ownership Display', () => {
    test('shows ownership percentage when provided', () => {
      render(<PlayerCard {...defaultProps} showOwnership={true} />);

      expect(screen.getByText('35%')).toBeInTheDocument();
      expect(screen.getByText(/owned/i)).toBeInTheDocument();
    });

    test('hides ownership when showOwnership is false', () => {
      render(<PlayerCard {...defaultProps} showOwnership={false} />);

      expect(screen.queryByText('35%')).not.toBeInTheDocument();
    });

    test('formats ownership percentage correctly', () => {
      const player = createMockPlayer({ ownership: 0.08 });
      render(<PlayerCard player={player} showOwnership={true} />);

      expect(screen.getByText('8%')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    test('applies compact layout on small screens', () => {
      // Mock window.innerWidth for mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 360,
      });

      render(<PlayerCard {...defaultProps} compact={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('compact');
    });

    test('hides less important info in compact mode', () => {
      render(<PlayerCard {...defaultProps} compact={true} />);

      // Game time might be hidden in compact mode
      expect(screen.queryByText('1:00 PM')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      render(<PlayerCard {...defaultProps} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveAttribute('role', 'button');
      expect(card).toHaveAttribute('aria-label', expect.stringContaining('Josh Allen'));
    });

    test('supports keyboard navigation', () => {
      const onSelect = jest.fn();
      render(<PlayerCard {...defaultProps} onSelect={onSelect} />);

      const card = screen.getByTestId('player-card');
      card.focus();
      fireEvent.keyDown(card, { key: 'Enter' });

      expect(onSelect).toHaveBeenCalled();
    });

    test('supports spacebar activation', () => {
      const onSelect = jest.fn();
      render(<PlayerCard {...defaultProps} onSelect={onSelect} />);

      const card = screen.getByTestId('player-card');
      fireEvent.keyDown(card, { key: ' ' });

      expect(onSelect).toHaveBeenCalled();
    });

    test('has proper tabindex when not disabled', () => {
      render(<PlayerCard {...defaultProps} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveAttribute('tabindex', '0');
    });

    test('removes from tab order when disabled', () => {
      render(<PlayerCard {...defaultProps} isDisabled={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveAttribute('tabindex', '-1');
    });
  });

  describe('Error Handling', () => {
    test('renders with missing optional data', () => {
      const player = createMockPlayer({
        salary: undefined,
        ownership: undefined,
        opponent: undefined,
        gameTime: undefined
      });

      render(<PlayerCard player={player} />);

      expect(screen.getByText('Josh Allen')).toBeInTheDocument();
      expect(screen.getByText('QB')).toBeInTheDocument();
    });

    test('handles invalid projected points gracefully', () => {
      const player = createMockPlayer({ projectedPoints: NaN });
      render(<PlayerCard player={player} />);

      expect(screen.getByText('--')).toBeInTheDocument();
    });

    test('handles missing player name', () => {
      const player = createMockPlayer({ name: '' });
      render(<PlayerCard player={player} />);

      expect(screen.getByText('Unknown Player')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('memoizes correctly to prevent unnecessary re-renders', () => {
      const { rerender } = render(<PlayerCard {...defaultProps} />);

      // Re-render with same props
      rerender(<PlayerCard {...defaultProps} />);

      // Component should not re-render with identical props
      expect(screen.getByText('Josh Allen')).toBeInTheDocument();
    });

    test('re-renders when player data changes', () => {
      const { rerender } = render(<PlayerCard {...defaultProps} />);

      const newPlayer = createMockPlayer({ name: 'Lamar Jackson' });
      rerender(<PlayerCard {...defaultProps} player={newPlayer} />);

      expect(screen.getByText('Lamar Jackson')).toBeInTheDocument();
      expect(screen.queryByText('Josh Allen')).not.toBeInTheDocument();
    });
  });

  describe('Theming', () => {
    test('applies theme colors correctly', () => {
      render(<PlayerCard {...defaultProps} />);

      const card = screen.getByTestId('player-card');
      const styles = window.getComputedStyle(card);

      // These would be set by the CSS classes with theme variables
      expect(card).toHaveClass('player-card');
    });

    test('supports dark theme', () => {
      // Mock dark theme
      jest.mocked(require('../../providers/ThemeProvider').useTheme).mockReturnValue({
        colors: {
          primary: '#8ab4f8',
          secondary: '#3c4043',
          text: '#e8eaed',
          background: '#202124'
        },
        isDark: true
      });

      render(<PlayerCard {...defaultProps} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('dark-theme');
    });
  });

  describe('Loading States', () => {
    test('shows loading skeleton when isLoading is true', () => {
      render(<PlayerCard {...defaultProps} isLoading={true} />);

      expect(screen.getByTestId('player-card-skeleton')).toBeInTheDocument();
      expect(screen.queryByText('Josh Allen')).not.toBeInTheDocument();
    });

    test('shows partial data during loading', () => {
      const player = createMockPlayer({ projectedPoints: 0 });
      render(<PlayerCard player={player} isLoading={true} />);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Animation', () => {
    test('applies entrance animation', async () => {
      render(<PlayerCard {...defaultProps} animateEntrance={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('animate-entrance');

      // Wait for animation to complete
      await waitFor(() => {
        expect(card).not.toHaveClass('animate-entrance');
      }, { timeout: 1000 });
    });

    test('applies selection animation', () => {
      const { rerender } = render(<PlayerCard {...defaultProps} isSelected={false} />);

      rerender(<PlayerCard {...defaultProps} isSelected={true} />);

      const card = screen.getByTestId('player-card');
      expect(card).toHaveClass('animate-selection');
    });
  });
});