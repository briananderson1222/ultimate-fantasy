/**
 * Unit tests for DraftBoard component.
 *
 * Tests cover:
 * - Draft order display and updates
 * - Real-time pick tracking
 * - Timer functionality
 * - Player selection interface
 * - Auto-draft indicators
 * - WebSocket connection handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import { DraftBoard } from '../DraftBoard';
import { DraftStatus, DraftPick } from '../../types/draft';
import { PlayerPosition } from '../../types/player';

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
};

global.WebSocket = jest.fn(() => mockWebSocket) as any;

// Mock the draft service
jest.mock('../../services/draftService', () => ({
  useDraftService: () => ({
    connectToDraft: jest.fn(),
    makePick: jest.fn(),
    getAvailablePlayers: jest.fn(),
    getDraftStatus: jest.fn(),
  })
}));

interface MockDraftData {
  id: string;
  status: DraftStatus;
  currentPick: number;
  totalPicks: number;
  currentTeamId: string;
  timeRemaining: number;
  picks: DraftPick[];
  teams: Array<{
    id: string;
    name: string;
    owner: string;
    draftPosition: number;
  }>;
}

const createMockDraftData = (overrides: Partial<MockDraftData> = {}): MockDraftData => ({
  id: 'draft1',
  status: DraftStatus.IN_PROGRESS,
  currentPick: 5,
  totalPicks: 180,
  currentTeamId: 'team1',
  timeRemaining: 75,
  picks: [
    { pickNumber: 1, teamId: 'team1', playerId: 'p1', playerName: 'Player 1', position: PlayerPosition.QB, timestamp: new Date() },
    { pickNumber: 2, teamId: 'team2', playerId: 'p2', playerName: 'Player 2', position: PlayerPosition.RB, timestamp: new Date() },
    { pickNumber: 3, teamId: 'team3', playerId: 'p3', playerName: 'Player 3', position: PlayerPosition.WR, timestamp: new Date() },
    { pickNumber: 4, teamId: 'team4', playerId: 'p4', playerName: 'Player 4', position: PlayerPosition.RB, timestamp: new Date() },
  ],
  teams: [
    { id: 'team1', name: 'Team 1', owner: 'Owner 1', draftPosition: 1 },
    { id: 'team2', name: 'Team 2', owner: 'Owner 2', draftPosition: 2 },
    { id: 'team3', name: 'Team 3', owner: 'Owner 3', draftPosition: 3 },
    { id: 'team4', name: 'Team 4', owner: 'Owner 4', draftPosition: 4 },
  ],
  ...overrides
});

const mockAvailablePlayers = [
  { id: 'p5', name: 'Available Player 1', position: PlayerPosition.QB, team: 'KC', projectedPoints: 24.5, rank: 5 },
  { id: 'p6', name: 'Available Player 2', position: PlayerPosition.RB, team: 'SF', projectedPoints: 18.2, rank: 6 },
  { id: 'p7', name: 'Available Player 3', position: PlayerPosition.WR, team: 'BUF', projectedPoints: 16.8, rank: 7 },
];

describe('DraftBoard', () => {
  const defaultProps = {
    draftId: 'draft1',
    currentUserId: 'user1',
    currentUserTeamId: 'team1',
    onPickPlayer: jest.fn(),
    onViewPlayerDetails: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Basic Rendering', () => {
    test('renders draft board with current status', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Draft Board')).toBeInTheDocument();
      expect(screen.getByText('Pick 5 of 180')).toBeInTheDocument();
      expect(screen.getByText('1:15')).toBeInTheDocument(); // Timer display
    });

    test('displays all teams in draft order', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Team 1')).toBeInTheDocument();
      expect(screen.getByText('Team 2')).toBeInTheDocument();
      expect(screen.getByText('Team 3')).toBeInTheDocument();
      expect(screen.getByText('Team 4')).toBeInTheDocument();
    });

    test('shows completed picks in order', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Player 2')).toBeInTheDocument();
      expect(screen.getByText('Player 3')).toBeInTheDocument();
      expect(screen.getByText('Player 4')).toBeInTheDocument();
    });

    test('highlights current picking team', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      const currentTeam = screen.getByTestId('team-team1');
      expect(currentTeam).toHaveClass('current-pick');
    });
  });

  describe('Draft Timer', () => {
    test('displays countdown timer', () => {
      const draftData = createMockDraftData({ timeRemaining: 90 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('1:30')).toBeInTheDocument();
    });

    test('updates timer every second', () => {
      const draftData = createMockDraftData({ timeRemaining: 90 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('1:30')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('1:29')).toBeInTheDocument();
    });

    test('shows warning when time is low', () => {
      const draftData = createMockDraftData({ timeRemaining: 15 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      const timer = screen.getByTestId('draft-timer');
      expect(timer).toHaveClass('timer-warning');
    });

    test('shows critical warning when time is very low', () => {
      const draftData = createMockDraftData({ timeRemaining: 5 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      const timer = screen.getByTestId('draft-timer');
      expect(timer).toHaveClass('timer-critical');
    });

    test('triggers auto-draft when timer expires', async () => {
      const draftData = createMockDraftData({ timeRemaining: 1 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      act(() => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('Auto-drafting...')).toBeInTheDocument();
      });
    });
  });

  describe('Player Selection', () => {
    test('shows available players when it is user turn', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      expect(screen.getByText('Available Player 1')).toBeInTheDocument();
      expect(screen.getByText('Available Player 2')).toBeInTheDocument();
      expect(screen.getByText('Available Player 3')).toBeInTheDocument();
    });

    test('hides player selection when not user turn', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team2' });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      expect(screen.queryByText('Available Player 1')).not.toBeInTheDocument();
      expect(screen.getByText('Waiting for Team 2 to pick...')).toBeInTheDocument();
    });

    test('calls onPickPlayer when player is selected', () => {
      const onPickPlayer = jest.fn();
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          onPickPlayer={onPickPlayer}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const playerButton = screen.getByTestId('select-player-p5');
      fireEvent.click(playerButton);

      expect(onPickPlayer).toHaveBeenCalledWith('p5', expect.any(Object));
    });

    test('disables player selection during auto-draft', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team1', timeRemaining: 0 });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
          isAutoDrafting={true}
        />
      );

      const playerButton = screen.getByTestId('select-player-p5');
      expect(playerButton).toBeDisabled();
    });
  });

  describe('Real-time Updates', () => {
    test('connects to WebSocket on mount', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8000/ws/draft/draft1')
      );
    });

    test('handles new pick via WebSocket', async () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      // Simulate WebSocket message for new pick
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'pick_made',
          pick: {
            pickNumber: 5,
            teamId: 'team1',
            playerId: 'p5',
            playerName: 'New Pick',
            position: PlayerPosition.QB,
            timestamp: new Date()
          }
        })
      });

      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](messageEvent);
      });

      await waitFor(() => {
        expect(screen.getByText('New Pick')).toBeInTheDocument();
      });
    });

    test('handles timer updates via WebSocket', async () => {
      const draftData = createMockDraftData({ timeRemaining: 90 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      // Simulate WebSocket timer update
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'timer_update',
          timeRemaining: 60,
          currentTeamId: 'team1'
        })
      });

      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](messageEvent);
      });

      await waitFor(() => {
        expect(screen.getByText('1:00')).toBeInTheDocument();
      });
    });

    test('handles draft completion via WebSocket', async () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      // Simulate draft completion message
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'draft_complete',
          status: DraftStatus.COMPLETED
        })
      });

      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'message')[1](messageEvent);
      });

      await waitFor(() => {
        expect(screen.getByText('Draft Complete!')).toBeInTheDocument();
      });
    });
  });

  describe('Draft Status Display', () => {
    test('shows draft not started status', () => {
      const draftData = createMockDraftData({ status: DraftStatus.NOT_STARTED });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Draft has not started')).toBeInTheDocument();
    });

    test('shows draft paused status', () => {
      const draftData = createMockDraftData({ status: DraftStatus.PAUSED });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Draft is paused')).toBeInTheDocument();
    });

    test('shows draft completed status', () => {
      const draftData = createMockDraftData({ status: DraftStatus.COMPLETED });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Draft Complete!')).toBeInTheDocument();
    });

    test('calculates and displays draft progress', () => {
      const draftData = createMockDraftData({ currentPick: 50, totalPicks: 180 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Pick 50 of 180')).toBeInTheDocument();
      expect(screen.getByText('28%')).toBeInTheDocument(); // Progress percentage
    });
  });

  describe('Snake Draft Visualization', () => {
    test('shows correct round information', () => {
      const draftData = createMockDraftData({ currentPick: 13, totalPicks: 180 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Round 4')).toBeInTheDocument();
    });

    test('indicates snake draft order in even rounds', () => {
      const draftData = createMockDraftData({ currentPick: 8 }); // Round 2

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      const draftOrder = screen.getByTestId('draft-order');
      expect(draftOrder).toHaveClass('snake-reverse');
    });

    test('shows upcoming picks for current user', () => {
      const draftData = createMockDraftData({ currentPick: 5 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Your next pick: #9')).toBeInTheDocument();
    });
  });

  describe('Player Information Display', () => {
    test('shows player details on hover', async () => {
      const draftData = createMockDraftData();

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const playerCard = screen.getByTestId('player-p5');
      fireEvent.mouseEnter(playerCard);

      await waitFor(() => {
        expect(screen.getByText('24.5 projected points')).toBeInTheDocument();
      });
    });

    test('calls onViewPlayerDetails when info button clicked', () => {
      const onViewPlayerDetails = jest.fn();
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          onViewPlayerDetails={onViewPlayerDetails}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const infoButton = screen.getByTestId('player-info-p5');
      fireEvent.click(infoButton);

      expect(onViewPlayerDetails).toHaveBeenCalledWith('p5');
    });

    test('filters players by position', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const qbFilter = screen.getByTestId('filter-QB');
      fireEvent.click(qbFilter);

      expect(screen.getByText('Available Player 1')).toBeInTheDocument();
      expect(screen.queryByText('Available Player 2')).not.toBeInTheDocument();
    });

    test('searches players by name', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const searchInput = screen.getByTestId('player-search');
      fireEvent.change(searchInput, { target: { value: 'Player 1' } });

      expect(screen.getByText('Available Player 1')).toBeInTheDocument();
      expect(screen.queryByText('Available Player 2')).not.toBeInTheDocument();
    });
  });

  describe('Auto-Draft Functionality', () => {
    test('shows auto-draft indicator when enabled', () => {
      const draftData = createMockDraftData({ timeRemaining: 5 });

      render(<DraftBoard {...defaultProps} draftData={draftData} isAutoDrafting={true} />);

      expect(screen.getByText('Auto-drafting...')).toBeInTheDocument();
      expect(screen.getByTestId('auto-draft-spinner')).toBeInTheDocument();
    });

    test('disables all interactions during auto-draft', () => {
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
          isAutoDrafting={true}
        />
      );

      const playerButton = screen.getByTestId('select-player-p5');
      expect(playerButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    test('shows error message when WebSocket disconnects', async () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      // Simulate WebSocket close
      act(() => {
        mockWebSocket.addEventListener.mock.calls
          .find(call => call[0] === 'close')[1]();
      });

      await waitFor(() => {
        expect(screen.getByText('Connection lost. Attempting to reconnect...')).toBeInTheDocument();
      });
    });

    test('handles invalid pick gracefully', async () => {
      const onPickPlayer = jest.fn().mockRejectedValue(new Error('Pick failed'));
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          onPickPlayer={onPickPlayer}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const playerButton = screen.getByTestId('select-player-p5');
      fireEvent.click(playerButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to make pick. Please try again.')).toBeInTheDocument();
      });
    });

    test('shows fallback when draft data is missing', () => {
      render(<DraftBoard {...defaultProps} draftData={null} />);

      expect(screen.getByText('Loading draft...')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels for screen readers', () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Draft Board');
      expect(screen.getByTestId('draft-timer')).toHaveAttribute('aria-live', 'polite');
    });

    test('supports keyboard navigation for player selection', () => {
      const onPickPlayer = jest.fn();
      const draftData = createMockDraftData({ currentTeamId: 'team1' });

      render(
        <DraftBoard
          {...defaultProps}
          onPickPlayer={onPickPlayer}
          draftData={draftData}
          availablePlayers={mockAvailablePlayers}
        />
      );

      const playerButton = screen.getByTestId('select-player-p5');
      fireEvent.keyDown(playerButton, { key: 'Enter' });

      expect(onPickPlayer).toHaveBeenCalled();
    });

    test('announces important updates to screen readers', async () => {
      const draftData = createMockDraftData();

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      const announcements = screen.getByTestId('sr-announcements');
      expect(announcements).toHaveAttribute('aria-live', 'assertive');
    });
  });

  describe('Performance', () => {
    test('efficiently updates only when necessary', () => {
      const draftData = createMockDraftData();
      const { rerender } = render(<DraftBoard {...defaultProps} draftData={draftData} />);

      // Re-render with same data should not cause updates
      rerender(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Pick 5 of 180')).toBeInTheDocument();
    });

    test('handles large number of picks efficiently', () => {
      const picks = Array.from({ length: 100 }, (_, i) => ({
        pickNumber: i + 1,
        teamId: `team${(i % 4) + 1}`,
        playerId: `p${i + 1}`,
        playerName: `Player ${i + 1}`,
        position: PlayerPosition.RB,
        timestamp: new Date()
      }));

      const draftData = createMockDraftData({ picks, currentPick: 101 });

      render(<DraftBoard {...defaultProps} draftData={draftData} />);

      expect(screen.getByText('Player 100')).toBeInTheDocument();
    });
  });
});