/**
 * TradeAnalyzer Component with AI Evaluation
 *
 * A comprehensive trade analysis component for fantasy sports applications.
 * Features AI-powered trade evaluation, fairness scoring, and detailed
 * impact analysis with visual feedback and recommendations.
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  fantasyTheme,
  getPositionColor,
  ThemeMode,
  getThemeColors
} from '../tokens/fantasy-theme';

export interface TradePlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  currentValue: number;
  projectedPoints: number;
  seasonProjection: number;
  averageDraftPosition?: number;
  positionRank?: number;
  tier?: number;
  injuryRisk?: number; // 0-1 scale
  consistencyScore?: number; // 0-1 scale
}

export interface TradeTeam {
  id: string;
  name: string;
  ownerName: string;
  currentRecord?: string;
  playoffOdds?: number;
  strengthOfSchedule?: number;
  rosterNeeds?: string[];
  rosterSurplus?: string[];
}

export interface TradeAnalysis {
  fairnessScore: number; // -100 to +100, 0 = perfectly fair
  winnerTeamId?: string;
  valueGap: number;

  // Impact analysis
  team1Impact: {
    weeklyPointsChange: number;
    seasonPointsChange: number;
    positionStrengthChange: { [position: string]: number };
    playoffOddsChange: number;
    riskLevel: 'low' | 'medium' | 'high';
  };

  team2Impact: {
    weeklyPointsChange: number;
    seasonPointsChange: number;
    positionStrengthChange: { [position: string]: number };
    playoffOddsChange: number;
    riskLevel: 'low' | 'medium' | 'high';
  };

  // AI insights
  aiRecommendation: 'accept' | 'reject' | 'negotiate';
  confidence: number; // 0-1 scale
  reasoning: string[];
  concerns: string[];
  alternatives?: string[];
}

export interface Trade {
  id?: string;
  team1: TradeTeam;
  team2: TradeTeam;
  team1Players: TradePlayer[];
  team2Players: TradePlayer[];
  status: 'proposed' | 'accepted' | 'rejected' | 'expired' | 'analysis';
  proposedBy: string;
  createdAt?: string;
  expiresAt?: string;
  analysis?: TradeAnalysis;
}

export interface TradeAnalyzerProps {
  trade: Trade;
  currentUserId: string;
  theme?: ThemeMode;
  showDetailedAnalysis?: boolean;
  showAIRecommendations?: boolean;
  allowModification?: boolean;

  // Event handlers
  onAcceptTrade?: (trade: Trade) => void;
  onRejectTrade?: (trade: Trade) => void;
  onCounterTrade?: (trade: Trade) => void;
  onPlayerSwap?: (tradeId: string, teamId: string, removePlayer: TradePlayer, addPlayer: TradePlayer) => void;
  onAnalysisRequest?: (trade: Trade) => Promise<TradeAnalysis>;

  // Customization
  className?: string;
  style?: React.CSSProperties;
}

const TradeAnalyzer: React.FC<TradeAnalyzerProps> = ({
  trade,
  currentUserId,
  theme = 'light',
  showDetailedAnalysis = true,
  showAIRecommendations = true,
  allowModification = false,
  onAcceptTrade,
  onRejectTrade,
  onCounterTrade,
  onPlayerSwap,
  onAnalysisRequest,
  className = '',
  style,
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<TradeAnalysis | null>(trade.analysis || null);

  const themeColors = getThemeColors(theme);

  // Determine user's perspective
  const userTeam = useMemo(() => {
    if (trade.team1.id === currentUserId) return trade.team1;
    if (trade.team2.id === currentUserId) return trade.team2;
    return null;
  }, [trade, currentUserId]);

  const isUserInvolved = Boolean(userTeam);
  const canTakeAction = isUserInvolved && trade.status === 'proposed';

  // Calculate basic trade values
  const team1TotalValue = useMemo(() =>
    trade.team1Players.reduce((sum, player) => sum + player.currentValue, 0),
    [trade.team1Players]
  );

  const team2TotalValue = useMemo(() =>
    trade.team2Players.reduce((sum, player) => sum + player.currentValue, 0),
    [trade.team2Players]
  );

  const valueDifference = team1TotalValue - team2TotalValue;
  const valueDifferencePercent = team2TotalValue > 0 ? (valueDifference / team2TotalValue) * 100 : 0;

  // Request AI analysis
  const requestAnalysis = useCallback(async () => {
    if (!onAnalysisRequest || analysis) return;

    setIsAnalyzing(true);
    try {
      const result = await onAnalysisRequest(trade);
      setAnalysis(result);
    } catch (error) {
      console.error('Failed to analyze trade:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [onAnalysisRequest, trade, analysis]);

  useEffect(() => {
    if (showAIRecommendations && !analysis && onAnalysisRequest) {
      requestAnalysis();
    }
  }, [showAIRecommendations, analysis, onAnalysisRequest, requestAnalysis]);

  // Event handlers
  const handleAccept = useCallback(() => {
    onAcceptTrade?.(trade);
  }, [onAcceptTrade, trade]);

  const handleReject = useCallback(() => {
    onRejectTrade?.(trade);
  }, [onRejectTrade, trade]);

  const handleCounter = useCallback(() => {
    onCounterTrade?.(trade);
  }, [onCounterTrade, trade]);

  const handleSectionToggle = useCallback((section: string) => {
    setExpandedSection(prev => prev === section ? null : section);
  }, []);

  // Styles
  const containerStyles: React.CSSProperties = {
    backgroundColor: themeColors.background.primary,
    border: `1px solid ${themeColors.border.default}`,
    borderRadius: fantasyTheme.borderRadius.lg,
    overflow: 'hidden',
    ...style,
  };

  const headerStyles: React.CSSProperties = {
    backgroundColor: themeColors.background.secondary,
    padding: fantasyTheme.spacing[4],
    borderBottom: `1px solid ${themeColors.border.default}`,
  };

  const teamSectionStyles: React.CSSProperties = {
    padding: fantasyTheme.spacing[4],
    borderBottom: `1px solid ${themeColors.border.light}`,
  };

  const playerCardStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    padding: fantasyTheme.spacing[3],
    backgroundColor: themeColors.surface.default,
    border: `1px solid ${themeColors.border.light}`,
    borderRadius: fantasyTheme.borderRadius.md,
    marginBottom: fantasyTheme.spacing[2],
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'accept': return fantasyTheme.brandColors.success[500];
      case 'reject': return fantasyTheme.brandColors.error[500];
      case 'negotiate': return fantasyTheme.brandColors.warning[500];
      default: return themeColors.text.muted;
    }
  };

  const renderPlayer = (player: TradePlayer, isGiving: boolean) => (
    <div key={player.id} style={playerCardStyles}>
      {/* Position indicator */}
      <div style={{
        width: '4px',
        height: '40px',
        backgroundColor: getPositionColor(player.position),
        marginRight: fantasyTheme.spacing[3],
        borderRadius: fantasyTheme.borderRadius.sm,
      }} />

      {/* Player info */}
      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: fantasyTheme.typography.fontSize.sm,
          fontWeight: fantasyTheme.typography.fontWeight.semibold,
          color: themeColors.text.primary,
          marginBottom: fantasyTheme.spacing[1],
        }}>
          {player.name}
        </div>
        <div style={{
          fontSize: fantasyTheme.typography.fontSize.xs,
          color: themeColors.text.secondary,
        }}>
          <span style={{ color: getPositionColor(player.position) }}>
            {player.position}
          </span>
          {' • '}{player.team}
          {player.positionRank && ` • #${player.positionRank} ${player.position}`}
        </div>
      </div>

      {/* Stats */}
      <div style={{ textAlign: 'right' }}>
        <div style={{
          fontSize: fantasyTheme.typography.fontSize.sm,
          fontWeight: fantasyTheme.typography.fontWeight.bold,
          color: themeColors.text.primary,
        }}>
          ${player.currentValue.toFixed(1)}M
        </div>
        <div style={{
          fontSize: fantasyTheme.typography.fontSize.xs,
          color: themeColors.text.muted,
        }}>
          {player.projectedPoints.toFixed(1)} proj
        </div>
      </div>

      {/* Trade direction indicator */}
      <div style={{
        marginLeft: fantasyTheme.spacing[3],
        fontSize: fantasyTheme.typography.fontSize.lg,
        color: isGiving
          ? fantasyTheme.brandColors.error[500]
          : fantasyTheme.brandColors.success[500],
      }}>
        {isGiving ? '→' : '←'}
      </div>
    </div>
  );

  return (
    <div className={`trade-analyzer ${className}`} style={containerStyles}>
      {/* Header */}
      <div style={headerStyles}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: fantasyTheme.spacing[3],
        }}>
          <div>
            <h2 style={{
              fontSize: fantasyTheme.typography.fontSize.xl,
              fontWeight: fantasyTheme.typography.fontWeight.bold,
              color: themeColors.text.primary,
              margin: 0,
            }}>
              Trade Analysis
            </h2>
            <p style={{
              fontSize: fantasyTheme.typography.fontSize.sm,
              color: themeColors.text.secondary,
              margin: `${fantasyTheme.spacing[1]} 0 0 0`,
            }}>
              {trade.team1.name} ↔ {trade.team2.name}
            </p>
          </div>

          {trade.status && (
            <span style={{
              backgroundColor: trade.status === 'proposed'
                ? fantasyTheme.brandColors.warning[100]
                : trade.status === 'accepted'
                ? fantasyTheme.brandColors.success[100]
                : fantasyTheme.brandColors.error[100],
              color: trade.status === 'proposed'
                ? fantasyTheme.brandColors.warning[700]
                : trade.status === 'accepted'
                ? fantasyTheme.brandColors.success[700]
                : fantasyTheme.brandColors.error[700],
              padding: `${fantasyTheme.spacing[1]} ${fantasyTheme.spacing[3]}`,
              borderRadius: fantasyTheme.borderRadius.md,
              fontSize: fantasyTheme.typography.fontSize.xs,
              fontWeight: fantasyTheme.typography.fontWeight.semibold,
              textTransform: 'uppercase',
            }}>
              {trade.status}
            </span>
          )}
        </div>

        {/* Value comparison */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: themeColors.background.tertiary,
          padding: fantasyTheme.spacing[3],
          borderRadius: fantasyTheme.borderRadius.md,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: fantasyTheme.typography.fontSize.lg,
              fontWeight: fantasyTheme.typography.fontWeight.bold,
              color: themeColors.text.primary,
            }}>
              ${team1TotalValue.toFixed(1)}M
            </div>
            <div style={{
              fontSize: fantasyTheme.typography.fontSize.xs,
              color: themeColors.text.secondary,
            }}>
              {trade.team1.name}
            </div>
          </div>

          <div style={{
            fontSize: fantasyTheme.typography.fontSize.xl,
            color: themeColors.text.muted,
          }}>
            ⇄
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: fantasyTheme.typography.fontSize.lg,
              fontWeight: fantasyTheme.typography.fontWeight.bold,
              color: themeColors.text.primary,
            }}>
              ${team2TotalValue.toFixed(1)}M
            </div>
            <div style={{
              fontSize: fantasyTheme.typography.fontSize.xs,
              color: themeColors.text.secondary,
            }}>
              {trade.team2.name}
            </div>
          </div>
        </div>

        {/* Value difference indicator */}
        {Math.abs(valueDifferencePercent) > 5 && (
          <div style={{
            marginTop: fantasyTheme.spacing[2],
            padding: fantasyTheme.spacing[2],
            backgroundColor: Math.abs(valueDifferencePercent) > 20
              ? fantasyTheme.brandColors.error[50]
              : fantasyTheme.brandColors.warning[50],
            borderRadius: fantasyTheme.borderRadius.md,
            textAlign: 'center',
          }}>
            <span style={{
              fontSize: fantasyTheme.typography.fontSize.sm,
              color: Math.abs(valueDifferencePercent) > 20
                ? fantasyTheme.brandColors.error[700]
                : fantasyTheme.brandColors.warning[700],
              fontWeight: fantasyTheme.typography.fontWeight.semibold,
            }}>
              {valueDifferencePercent > 0
                ? `${trade.team1.name} receives ${valueDifferencePercent.toFixed(1)}% more value`
                : `${trade.team2.name} receives ${Math.abs(valueDifferencePercent).toFixed(1)}% more value`
              }
            </span>
          </div>
        )}
      </div>

      {/* Team 1 Players */}
      <div style={teamSectionStyles}>
        <h3 style={{
          fontSize: fantasyTheme.typography.fontSize.lg,
          fontWeight: fantasyTheme.typography.fontWeight.semibold,
          color: themeColors.text.primary,
          margin: `0 0 ${fantasyTheme.spacing[3]} 0`,
        }}>
          {trade.team1.name} Gives
        </h3>
        {trade.team1Players.map(player => renderPlayer(player, true))}
      </div>

      {/* Team 2 Players */}
      <div style={teamSectionStyles}>
        <h3 style={{
          fontSize: fantasyTheme.typography.fontSize.lg,
          fontWeight: fantasyTheme.typography.fontWeight.semibold,
          color: themeColors.text.primary,
          margin: `0 0 ${fantasyTheme.spacing[3]} 0`,
        }}>
          {trade.team2.name} Gives
        </h3>
        {trade.team2Players.map(player => renderPlayer(player, true))}
      </div>

      {/* AI Analysis Section */}
      {showAIRecommendations && (
        <div style={{
          padding: fantasyTheme.spacing[4],
          backgroundColor: themeColors.background.secondary,
          borderTop: `1px solid ${themeColors.border.default}`,
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: fantasyTheme.spacing[3],
          }}>
            <h3 style={{
              fontSize: fantasyTheme.typography.fontSize.lg,
              fontWeight: fantasyTheme.typography.fontWeight.semibold,
              color: themeColors.text.primary,
              margin: 0,
            }}>
              AI Analysis
            </h3>

            {!analysis && (
              <button
                onClick={requestAnalysis}
                disabled={isAnalyzing}
                style={{
                  backgroundColor: fantasyTheme.brandColors.primary[500],
                  color: 'white',
                  border: 'none',
                  padding: `${fantasyTheme.spacing[2]} ${fantasyTheme.spacing[4]}`,
                  borderRadius: fantasyTheme.borderRadius.md,
                  fontSize: fantasyTheme.typography.fontSize.sm,
                  fontWeight: fantasyTheme.typography.fontWeight.semibold,
                  cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                  opacity: isAnalyzing ? 0.6 : 1,
                }}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Trade'}
              </button>
            )}
          </div>

          {analysis ? (
            <div>
              {/* AI Recommendation */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: fantasyTheme.spacing[4],
                padding: fantasyTheme.spacing[3],
                backgroundColor: themeColors.background.primary,
                borderRadius: fantasyTheme.borderRadius.md,
                border: `2px solid ${getRecommendationColor(analysis.aiRecommendation)}`,
              }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: getRecommendationColor(analysis.aiRecommendation),
                  marginRight: fantasyTheme.spacing[3],
                }} />

                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: fantasyTheme.typography.fontSize.sm,
                    fontWeight: fantasyTheme.typography.fontWeight.bold,
                    color: getRecommendationColor(analysis.aiRecommendation),
                    textTransform: 'uppercase',
                    marginBottom: fantasyTheme.spacing[1],
                  }}>
                    {analysis.aiRecommendation}
                  </div>
                  <div style={{
                    fontSize: fantasyTheme.typography.fontSize.sm,
                    color: themeColors.text.secondary,
                  }}>
                    Confidence: {(analysis.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                <div style={{
                  textAlign: 'right',
                  fontSize: fantasyTheme.typography.fontSize.sm,
                  color: themeColors.text.primary,
                }}>
                  <div style={{ fontWeight: fantasyTheme.typography.fontWeight.semibold }}>
                    Fairness Score
                  </div>
                  <div style={{
                    fontSize: fantasyTheme.typography.fontSize.lg,
                    fontWeight: fantasyTheme.typography.fontWeight.bold,
                    color: analysis.fairnessScore > 10
                      ? fantasyTheme.brandColors.error[500]
                      : analysis.fairnessScore < -10
                      ? fantasyTheme.brandColors.success[500]
                      : fantasyTheme.brandColors.info[500],
                  }}>
                    {analysis.fairnessScore > 0 ? '+' : ''}{analysis.fairnessScore.toFixed(0)}
                  </div>
                </div>
              </div>

              {/* Reasoning */}
              {analysis.reasoning.length > 0 && (
                <div style={{ marginBottom: fantasyTheme.spacing[4] }}>
                  <h4 style={{
                    fontSize: fantasyTheme.typography.fontSize.sm,
                    fontWeight: fantasyTheme.typography.fontWeight.semibold,
                    color: themeColors.text.primary,
                    margin: `0 0 ${fantasyTheme.spacing[2]} 0`,
                  }}>
                    Key Points
                  </h4>
                  <ul style={{
                    margin: 0,
                    paddingLeft: fantasyTheme.spacing[5],
                    color: themeColors.text.secondary,
                    fontSize: fantasyTheme.typography.fontSize.sm,
                  }}>
                    {analysis.reasoning.map((reason, index) => (
                      <li key={index} style={{ marginBottom: fantasyTheme.spacing[1] }}>
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Concerns */}
              {analysis.concerns.length > 0 && (
                <div style={{ marginBottom: fantasyTheme.spacing[4] }}>
                  <h4 style={{
                    fontSize: fantasyTheme.typography.fontSize.sm,
                    fontWeight: fantasyTheme.typography.fontWeight.semibold,
                    color: fantasyTheme.brandColors.warning[600],
                    margin: `0 0 ${fantasyTheme.spacing[2]} 0`,
                  }}>
                    Concerns
                  </h4>
                  <ul style={{
                    margin: 0,
                    paddingLeft: fantasyTheme.spacing[5],
                    color: fantasyTheme.brandColors.warning[700],
                    fontSize: fantasyTheme.typography.fontSize.sm,
                  }}>
                    {analysis.concerns.map((concern, index) => (
                      <li key={index} style={{ marginBottom: fantasyTheme.spacing[1] }}>
                        {concern}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Detailed Impact Analysis */}
              {showDetailedAnalysis && (
                <div>
                  <button
                    onClick={() => handleSectionToggle('impact')}
                    style={{
                      width: '100%',
                      padding: fantasyTheme.spacing[3],
                      backgroundColor: 'transparent',
                      border: `1px solid ${themeColors.border.default}`,
                      borderRadius: fantasyTheme.borderRadius.md,
                      color: themeColors.text.primary,
                      fontSize: fantasyTheme.typography.fontSize.sm,
                      fontWeight: fantasyTheme.typography.fontWeight.semibold,
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    Detailed Impact Analysis
                    <span>{expandedSection === 'impact' ? '▲' : '▼'}</span>
                  </button>

                  {expandedSection === 'impact' && (
                    <div style={{
                      marginTop: fantasyTheme.spacing[3],
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: fantasyTheme.spacing[4],
                    }}>
                      {/* Team 1 Impact */}
                      <div>
                        <h5 style={{
                          fontSize: fantasyTheme.typography.fontSize.sm,
                          fontWeight: fantasyTheme.typography.fontWeight.semibold,
                          color: themeColors.text.primary,
                          margin: `0 0 ${fantasyTheme.spacing[2]} 0`,
                        }}>
                          {trade.team1.name} Impact
                        </h5>
                        <div style={{
                          backgroundColor: themeColors.background.primary,
                          padding: fantasyTheme.spacing[3],
                          borderRadius: fantasyTheme.borderRadius.md,
                          fontSize: fantasyTheme.typography.fontSize.sm,
                        }}>
                          <div style={{ marginBottom: fantasyTheme.spacing[2] }}>
                            <strong>Weekly Points:</strong> {analysis.team1Impact.weeklyPointsChange > 0 ? '+' : ''}{analysis.team1Impact.weeklyPointsChange.toFixed(1)}
                          </div>
                          <div style={{ marginBottom: fantasyTheme.spacing[2] }}>
                            <strong>Playoff Odds:</strong> {analysis.team1Impact.playoffOddsChange > 0 ? '+' : ''}{analysis.team1Impact.playoffOddsChange.toFixed(1)}%
                          </div>
                          <div>
                            <strong>Risk Level:</strong> {analysis.team1Impact.riskLevel}
                          </div>
                        </div>
                      </div>

                      {/* Team 2 Impact */}
                      <div>
                        <h5 style={{
                          fontSize: fantasyTheme.typography.fontSize.sm,
                          fontWeight: fantasyTheme.typography.fontWeight.semibold,
                          color: themeColors.text.primary,
                          margin: `0 0 ${fantasyTheme.spacing[2]} 0`,
                        }}>
                          {trade.team2.name} Impact
                        </h5>
                        <div style={{
                          backgroundColor: themeColors.background.primary,
                          padding: fantasyTheme.spacing[3],
                          borderRadius: fantasyTheme.borderRadius.md,
                          fontSize: fantasyTheme.typography.fontSize.sm,
                        }}>
                          <div style={{ marginBottom: fantasyTheme.spacing[2] }}>
                            <strong>Weekly Points:</strong> {analysis.team2Impact.weeklyPointsChange > 0 ? '+' : ''}{analysis.team2Impact.weeklyPointsChange.toFixed(1)}
                          </div>
                          <div style={{ marginBottom: fantasyTheme.spacing[2] }}>
                            <strong>Playoff Odds:</strong> {analysis.team2Impact.playoffOddsChange > 0 ? '+' : ''}{analysis.team2Impact.playoffOddsChange.toFixed(1)}%
                          </div>
                          <div>
                            <strong>Risk Level:</strong> {analysis.team2Impact.riskLevel}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : isAnalyzing ? (
            <div style={{
              textAlign: 'center',
              padding: fantasyTheme.spacing[4],
              color: themeColors.text.muted,
            }}>
              <div style={{
                fontSize: fantasyTheme.typography.fontSize.sm,
                marginBottom: fantasyTheme.spacing[2],
              }}>
                Analyzing trade with AI...
              </div>
              <div style={{
                width: '32px',
                height: '32px',
                border: `3px solid ${themeColors.border.light}`,
                borderTop: `3px solid ${fantasyTheme.brandColors.primary[500]}`,
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto',
              }} />
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: fantasyTheme.spacing[4],
              color: themeColors.text.muted,
              fontSize: fantasyTheme.typography.fontSize.sm,
            }}>
              Click "Analyze Trade" to get AI-powered insights
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {canTakeAction && (
        <div style={{
          padding: fantasyTheme.spacing[4],
          borderTop: `1px solid ${themeColors.border.default}`,
          display: 'flex',
          gap: fantasyTheme.spacing[3],
          justifyContent: 'flex-end',
        }}>
          {onRejectTrade && (
            <button
              onClick={handleReject}
              style={{
                backgroundColor: fantasyTheme.brandColors.error[500],
                color: 'white',
                border: 'none',
                padding: `${fantasyTheme.spacing[3]} ${fantasyTheme.spacing[6]}`,
                borderRadius: fantasyTheme.borderRadius.md,
                fontSize: fantasyTheme.typography.fontSize.sm,
                fontWeight: fantasyTheme.typography.fontWeight.semibold,
                cursor: 'pointer',
              }}
            >
              Reject
            </button>
          )}

          {onCounterTrade && (
            <button
              onClick={handleCounter}
              style={{
                backgroundColor: 'transparent',
                color: themeColors.text.primary,
                border: `1px solid ${themeColors.border.default}`,
                padding: `${fantasyTheme.spacing[3]} ${fantasyTheme.spacing[6]}`,
                borderRadius: fantasyTheme.borderRadius.md,
                fontSize: fantasyTheme.typography.fontSize.sm,
                fontWeight: fantasyTheme.typography.fontWeight.semibold,
                cursor: 'pointer',
              }}
            >
              Counter
            </button>
          )}

          {onAcceptTrade && (
            <button
              onClick={handleAccept}
              style={{
                backgroundColor: fantasyTheme.brandColors.success[500],
                color: 'white',
                border: 'none',
                padding: `${fantasyTheme.spacing[3]} ${fantasyTheme.spacing[6]}`,
                borderRadius: fantasyTheme.borderRadius.md,
                fontSize: fantasyTheme.typography.fontSize.sm,
                fontWeight: fantasyTheme.typography.fontWeight.semibold,
                cursor: 'pointer',
              }}
            >
              Accept Trade
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default TradeAnalyzer;