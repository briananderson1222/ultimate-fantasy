/**
 * Unit tests for TradeAnalyzer component.
 *
 * Tests cover:
 * - Trade fairness evaluation display
 * - Player value comparisons
 * - Interactive trade adjustments
 * - AI recommendation integration
 * - Visual trade balance indicators
 * - Multi-team trade support
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import { TradeAnalyzer } from '../TradeAnalyzer';
import { PlayerPosition } from '../../types/player';
import { TradeStatus, FairnessRating } from '../../types/trade';

// Mock the trade evaluation service
jest.mock('../../services/tradeService', () => ({
  useTradeService: () => ({
    evaluateTrade: jest.fn(),
    getPlayerValues: jest.fn(),
    getTradeRecommendations: jest.fn(),
  })
}));

interface MockPlayer {
  id: string;
  name: string;
  position: PlayerPosition;
  team: string;
  value: number;
  projectedPoints: number;
  riskLevel: 'low' | 'medium' | 'high';
  trend: 'up' | 'down' | 'stable';
}

interface MockTradeAnalysis {
  fairnessRating: FairnessRating;
  valueGap: number;
  team1Advantage: number;
  team2Advantage: number;
  confidence: number;
  recommendation: 'accept' | 'reject' | 'negotiate';
  reasoning: string[];
  riskAssessment: {
    team1Risk: number;
    team2Risk: number;
  };
}

const createMockPlayer = (overrides: Partial<MockPlayer> = {}): MockPlayer => ({
  id: 'player1',
  name: 'Josh Allen',
  position: PlayerPosition.QB,
  team: 'BUF',
  value: 85,
  projectedPoints: 24.5,
  riskLevel: 'low',
  trend: 'stable',
  ...overrides
});

const createMockAnalysis = (overrides: Partial<MockTradeAnalysis> = {}): MockTradeAnalysis => ({
  fairnessRating: FairnessRating.FAIR,
  valueGap: 0,
  team1Advantage: 0,
  team2Advantage: 0,
  confidence: 0.85,
  recommendation: 'accept',
  reasoning: ['Both teams receive fair value', 'Addresses positional needs'],
  riskAssessment: {
    team1Risk: 0.2,
    team2Risk: 0.25
  },
  ...overrides
});

describe('TradeAnalyzer', () => {
  const defaultProps = {
    team1Players: [
      createMockPlayer({ id: 'p1', name: 'Elite QB', value: 90, position: PlayerPosition.QB }),
      createMockPlayer({ id: 'p2', name: 'Good WR', value: 75, position: PlayerPosition.WR }),
    ],
    team2Players: [
      createMockPlayer({ id: 'p3', name: 'Top RB', value: 88, position: PlayerPosition.RB }),
      createMockPlayer({ id: 'p4', name: 'Solid TE', value: 65, position: PlayerPosition.TE }),
    ],
    onTradeUpdate: jest.fn(),
    onAcceptTrade: jest.fn(),
    onRejectTrade: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders trade analyzer with player lists', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('Trade Analyzer')).toBeInTheDocument();
      expect(screen.getByText('Elite QB')).toBeInTheDocument();
      expect(screen.getByText('Good WR')).toBeInTheDocument();
      expect(screen.getByText('Top RB')).toBeInTheDocument();
      expect(screen.getByText('Solid TE')).toBeInTheDocument();
    });

    test('displays trade fairness rating', () => {
      const analysis = createMockAnalysis({ fairnessRating: FairnessRating.FAIR });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('Fair Trade')).toBeInTheDocument();
    });

    test('shows overall trade value', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      // Team 1 total: 90 + 75 = 165
      // Team 2 total: 88 + 65 = 153
      expect(screen.getByText('165')).toBeInTheDocument();
      expect(screen.getByText('153')).toBeInTheDocument();
    });

    test('displays confidence score', () => {
      const analysis = createMockAnalysis({ confidence: 0.85 });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText(/confidence/i)).toBeInTheDocument();
    });
  });

  describe('Fairness Rating Display', () => {
    test('shows fair trade with balanced colors', () => {
      const analysis = createMockAnalysis({ fairnessRating: FairnessRating.FAIR });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const ratingElement = screen.getByTestId('fairness-rating');
      expect(ratingElement).toHaveClass('rating-fair');
    });

    test('shows lopsided trade with warning colors', () => {
      const analysis = createMockAnalysis({
        fairnessRating: FairnessRating.HEAVILY_FAVORS_TEAM1,
        valueGap: 25
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const ratingElement = screen.getByTestId('fairness-rating');
      expect(ratingElement).toHaveClass('rating-heavily-favors');
      expect(screen.getByText('Heavily Favors Team 1')).toBeInTheDocument();
    });

    test('displays appropriate warning for unfair trades', () => {
      const analysis = createMockAnalysis({
        fairnessRating: FairnessRating.HEAVILY_FAVORS_TEAM2,
        recommendation: 'reject'
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText(/not recommended/i)).toBeInTheDocument();
    });
  });

  describe('Player Value Visualization', () => {
    test('shows individual player values', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('90')).toBeInTheDocument(); // Elite QB value
      expect(screen.getByText('75')).toBeInTheDocument(); // Good WR value
      expect(screen.getByText('88')).toBeInTheDocument(); // Top RB value
      expect(screen.getByText('65')).toBeInTheDocument(); // Solid TE value
    });

    test('highlights highest value player', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const eliteQB = screen.getByTestId('player-p1');
      expect(eliteQB).toHaveClass('highest-value');
    });

    test('shows value difference visualization', () => {
      const analysis = createMockAnalysis({ valueGap: 12 });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('+12')).toBeInTheDocument();
      const balanceBar = screen.getByTestId('value-balance-bar');
      expect(balanceBar).toBeInTheDocument();
    });

    test('displays player trends correctly', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const trendIndicators = screen.getAllByTestId(/trend-indicator/);
      expect(trendIndicators).toHaveLength(4);
    });
  });

  describe('Risk Assessment', () => {
    test('displays risk levels for both teams', () => {
      const analysis = createMockAnalysis({
        riskAssessment: { team1Risk: 0.3, team2Risk: 0.7 }
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('30%')).toBeInTheDocument(); // Team 1 risk
      expect(screen.getByText('70%')).toBeInTheDocument(); // Team 2 risk
    });

    test('highlights high-risk players', () => {
      const props = {
        ...defaultProps,
        team1Players: [
          createMockPlayer({ id: 'p1', riskLevel: 'high', name: 'Risky Player' })
        ]
      };

      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...props} analysis={analysis} />);

      const riskyPlayer = screen.getByTestId('player-p1');
      expect(riskyPlayer).toHaveClass('high-risk');
    });

    test('shows risk warning for high-risk trades', () => {
      const analysis = createMockAnalysis({
        riskAssessment: { team1Risk: 0.8, team2Risk: 0.2 }
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText(/high risk/i)).toBeInTheDocument();
    });
  });

  describe('AI Recommendations', () => {
    test('displays AI reasoning', () => {
      const analysis = createMockAnalysis({
        reasoning: ['Addresses RB shortage', 'QB depth is adequate', 'Fair value exchange']
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('Addresses RB shortage')).toBeInTheDocument();
      expect(screen.getByText('QB depth is adequate')).toBeInTheDocument();
      expect(screen.getByText('Fair value exchange')).toBeInTheDocument();
    });

    test('shows accept recommendation with green styling', () => {
      const analysis = createMockAnalysis({ recommendation: 'accept' });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const recommendation = screen.getByTestId('ai-recommendation');
      expect(recommendation).toHaveClass('recommend-accept');
      expect(screen.getByText(/recommended/i)).toBeInTheDocument();
    });

    test('shows reject recommendation with red styling', () => {
      const analysis = createMockAnalysis({ recommendation: 'reject' });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const recommendation = screen.getByTestId('ai-recommendation');
      expect(recommendation).toHaveClass('recommend-reject');
      expect(screen.getByText(/not recommended/i)).toBeInTheDocument();
    });

    test('shows negotiate recommendation with yellow styling', () => {
      const analysis = createMockAnalysis({ recommendation: 'negotiate' });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const recommendation = screen.getByTestId('ai-recommendation');
      expect(recommendation).toHaveClass('recommend-negotiate');
      expect(screen.getByText(/consider negotiating/i)).toBeInTheDocument();
    });
  });

  describe('Interactive Features', () => {
    test('allows removing players from trade', () => {
      const onTradeUpdate = jest.fn();
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} onTradeUpdate={onTradeUpdate} analysis={analysis} />);

      const removeButton = screen.getByTestId('remove-player-p1');
      fireEvent.click(removeButton);

      expect(onTradeUpdate).toHaveBeenCalledWith({
        team1Players: expect.arrayContaining([
          expect.not.objectContaining({ id: 'p1' })
        ]),
        team2Players: defaultProps.team2Players
      });
    });

    test('enables adding additional players', () => {
      const onTradeUpdate = jest.fn();
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} onTradeUpdate={onTradeUpdate} analysis={analysis} />);

      const addPlayerButton = screen.getByTestId('add-player-team1');
      fireEvent.click(addPlayerButton);

      expect(screen.getByText('Select Player to Add')).toBeInTheDocument();
    });

    test('calls onAcceptTrade when accept button clicked', () => {
      const onAcceptTrade = jest.fn();
      const analysis = createMockAnalysis({ recommendation: 'accept' });

      render(<TradeAnalyzer {...defaultProps} onAcceptTrade={onAcceptTrade} analysis={analysis} />);

      const acceptButton = screen.getByTestId('accept-trade-button');
      fireEvent.click(acceptButton);

      expect(onAcceptTrade).toHaveBeenCalled();
    });

    test('calls onRejectTrade when reject button clicked', () => {
      const onRejectTrade = jest.fn();
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} onRejectTrade={onRejectTrade} analysis={analysis} />);

      const rejectButton = screen.getByTestId('reject-trade-button');
      fireEvent.click(rejectButton);

      expect(onRejectTrade).toHaveBeenCalled();
    });

    test('shows confirmation dialog for risky accepts', async () => {
      const analysis = createMockAnalysis({
        recommendation: 'reject',
        riskAssessment: { team1Risk: 0.8, team2Risk: 0.2 }
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const acceptButton = screen.getByTestId('accept-trade-button');
      fireEvent.click(acceptButton);

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });
  });

  describe('Advanced Features', () => {
    test('supports multi-team trades', () => {
      const multiTeamProps = {
        ...defaultProps,
        team3Players: [
          createMockPlayer({ id: 'p5', name: 'Team 3 Player', value: 70 })
        ]
      };

      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...multiTeamProps} analysis={analysis} />);

      expect(screen.getByText('Team 3')).toBeInTheDocument();
      expect(screen.getByText('Team 3 Player')).toBeInTheDocument();
    });

    test('shows detailed player statistics on hover', async () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const player = screen.getByTestId('player-p1');
      fireEvent.mouseEnter(player);

      await waitFor(() => {
        expect(screen.getByText('24.5 PPG')).toBeInTheDocument();
        expect(screen.getByText('Low Risk')).toBeInTheDocument();
      });
    });

    test('provides alternative trade suggestions', () => {
      const analysis = createMockAnalysis({
        recommendation: 'negotiate',
        reasoning: ['Consider adding a mid-tier WR to balance the trade']
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByTestId('alternative-suggestions')).toBeInTheDocument();
    });

    test('shows historical trade comparisons', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} showComparisons={true} />);

      expect(screen.getByText('Similar Trades')).toBeInTheDocument();
    });
  });

  describe('Loading and Error States', () => {
    test('shows loading state while analyzing', () => {
      render(<TradeAnalyzer {...defaultProps} isAnalyzing={true} />);

      expect(screen.getByText('Analyzing trade...')).toBeInTheDocument();
      expect(screen.getByTestId('analysis-spinner')).toBeInTheDocument();
    });

    test('displays error when analysis fails', () => {
      const error = new Error('Analysis failed');

      render(<TradeAnalyzer {...defaultProps} error={error} />);

      expect(screen.getByText('Failed to analyze trade')).toBeInTheDocument();
      expect(screen.getByText('Analysis failed')).toBeInTheDocument();
    });

    test('shows retry button on error', () => {
      const onRetry = jest.fn();
      const error = new Error('Network error');

      render(<TradeAnalyzer {...defaultProps} error={error} onRetry={onRetry} />);

      const retryButton = screen.getByTestId('retry-analysis');
      fireEvent.click(retryButton);

      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe('Responsive Design', () => {
    test('adapts layout for mobile screens', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} isMobile={true} />);

      const container = screen.getByTestId('trade-analyzer');
      expect(container).toHaveClass('mobile-layout');
    });

    test('stacks player cards vertically on small screens', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} isMobile={true} />);

      const playerGrid = screen.getByTestId('player-grid');
      expect(playerGrid).toHaveClass('vertical-stack');
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels for screen readers', () => {
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Trade Analysis');
      expect(screen.getByTestId('fairness-rating')).toHaveAttribute('aria-live', 'polite');
    });

    test('supports keyboard navigation', () => {
      const onAcceptTrade = jest.fn();
      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...defaultProps} onAcceptTrade={onAcceptTrade} analysis={analysis} />);

      const acceptButton = screen.getByTestId('accept-trade-button');
      acceptButton.focus();
      fireEvent.keyDown(acceptButton, { key: 'Enter' });

      expect(onAcceptTrade).toHaveBeenCalled();
    });

    test('announces important changes to screen readers', async () => {
      const analysis = createMockAnalysis();
      const { rerender } = render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      const newAnalysis = createMockAnalysis({ recommendation: 'reject' });
      rerender(<TradeAnalyzer {...defaultProps} analysis={newAnalysis} />);

      await waitFor(() => {
        const announcement = screen.getByTestId('sr-announcement');
        expect(announcement).toHaveTextContent(/recommendation changed/i);
      });
    });
  });

  describe('Data Formatting', () => {
    test('formats large values with abbreviations', () => {
      const highValuePlayer = createMockPlayer({ value: 9500 });
      const props = {
        ...defaultProps,
        team1Players: [highValuePlayer]
      };

      const analysis = createMockAnalysis();

      render(<TradeAnalyzer {...props} analysis={analysis} />);

      expect(screen.getByText('9.5K')).toBeInTheDocument();
    });

    test('displays percentages correctly', () => {
      const analysis = createMockAnalysis({
        confidence: 0.876,
        riskAssessment: { team1Risk: 0.123, team2Risk: 0.789 }
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('88%')).toBeInTheDocument(); // Rounded confidence
      expect(screen.getByText('12%')).toBeInTheDocument(); // Rounded team1 risk
      expect(screen.getByText('79%')).toBeInTheDocument(); // Rounded team2 risk
    });

    test('handles edge cases gracefully', () => {
      const analysis = createMockAnalysis({
        confidence: 0,
        valueGap: null,
        reasoning: []
      });

      render(<TradeAnalyzer {...defaultProps} analysis={analysis} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('Even')).toBeInTheDocument(); // Null value gap
    });
  });
});