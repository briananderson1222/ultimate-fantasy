/**
 * ScoreTicker Component for Live Updates
 *
 * A real-time scrolling ticker component for fantasy sports live scoring.
 * Features smooth animations, configurable update intervals, and rich
 * scoring information with player and team updates.
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  fantasyTheme,
  getPositionColor,
  getScoringColor,
  ThemeMode,
  getThemeColors
} from '../tokens/fantasy-theme';

export interface ScoreUpdate {
  id: string;
  type: 'player_score' | 'game_score' | 'breaking_news' | 'injury_update';
  timestamp: string;

  // Player scoring
  playerId?: string;
  playerName?: string;
  playerPosition?: string;
  playerTeam?: string;
  points?: number;
  statType?: string; // 'touchdown', 'field_goal', 'interception', etc.
  statValue?: number;

  // Game information
  gameId?: string;
  homeTeam?: string;
  awayTeam?: string;
  quarter?: number;
  timeRemaining?: string;

  // News/Updates
  title?: string;
  description?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';

  // Visual
  urgent?: boolean;
  highlighted?: boolean;
}

export interface TickerSettings {
  scrollSpeed: number; // pixels per second
  updateInterval: number; // milliseconds
  maxItems: number;
  showPlayerPhotos: boolean;
  showTeamLogos: boolean;
  groupByGame: boolean;
  autoHide: boolean;
  autoHideDelay: number; // seconds
}

export interface ScoreTickerProps {
  updates: ScoreUpdate[];
  theme?: ThemeMode;
  variant?: 'compact' | 'standard' | 'detailed';
  position?: 'top' | 'bottom' | 'floating';
  settings?: Partial<TickerSettings>;

  // Real-time connection
  webSocketUrl?: string;
  onUpdateReceived?: (update: ScoreUpdate) => void;

  // Event handlers
  onItemClick?: (update: ScoreUpdate) => void;
  onPause?: () => void;
  onResume?: () => void;

  // Customization
  className?: string;
  style?: React.CSSProperties;
}

const defaultSettings: TickerSettings = {
  scrollSpeed: 50,
  updateInterval: 5000,
  maxItems: 20,
  showPlayerPhotos: false,
  showTeamLogos: true,
  groupByGame: false,
  autoHide: false,
  autoHideDelay: 10,
};

const ScoreTicker: React.FC<ScoreTickerProps> = ({
  updates,
  theme = 'light',
  variant = 'standard',
  position = 'bottom',
  settings: userSettings = {},
  webSocketUrl,
  onUpdateReceived,
  onItemClick,
  onPause,
  onResume,
  className = '',
  style,
}) => {
  const [isScrolling, setIsScrolling] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [liveUpdates, setLiveUpdates] = useState<ScoreUpdate[]>(updates);
  const [scrollPosition, setScrollPosition] = useState(0);

  const tickerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();
  const autoHideTimeoutRef = useRef<NodeJS.Timeout>();

  const settings = useMemo(() => ({ ...defaultSettings, ...userSettings }), [userSettings]);
  const themeColors = getThemeColors(theme);

  // Merge incoming updates with live updates
  useEffect(() => {
    const mergedUpdates = [...updates, ...liveUpdates];
    const uniqueUpdates = mergedUpdates
      .filter((update, index, arr) =>
        arr.findIndex(u => u.id === update.id) === index
      )
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, settings.maxItems);

    setLiveUpdates(uniqueUpdates);
  }, [updates, settings.maxItems]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!webSocketUrl) return;

    const ws = new WebSocket(webSocketUrl);

    ws.onmessage = (event) => {
      try {
        const update: ScoreUpdate = JSON.parse(event.data);
        setLiveUpdates(prev => {
          const newUpdates = [update, ...prev].slice(0, settings.maxItems);
          onUpdateReceived?.(update);

          // Show ticker if hidden and urgent update
          if (update.urgent && !isVisible) {
            setIsVisible(true);
          }

          return newUpdates;
        });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, [webSocketUrl, settings.maxItems, onUpdateReceived, isVisible]);

  // Auto-hide functionality
  useEffect(() => {
    if (!settings.autoHide) return;

    const resetTimer = () => {
      if (autoHideTimeoutRef.current) {
        clearTimeout(autoHideTimeoutRef.current);
      }

      autoHideTimeoutRef.current = setTimeout(() => {
        setIsVisible(false);
      }, settings.autoHideDelay * 1000);
    };

    if (liveUpdates.length > 0 && isVisible) {
      resetTimer();
    }

    return () => {
      if (autoHideTimeoutRef.current) {
        clearTimeout(autoHideTimeoutRef.current);
      }
    };
  }, [liveUpdates.length, isVisible, settings.autoHide, settings.autoHideDelay]);

  // Scrolling animation
  useEffect(() => {
    if (!isScrolling || isPaused || !isVisible) return;

    const animate = () => {
      if (!contentRef.current || !tickerRef.current) return;

      const contentWidth = contentRef.current.scrollWidth;
      const containerWidth = tickerRef.current.clientWidth;

      if (contentWidth <= containerWidth) {
        animationRef.current = requestAnimationFrame(animate);
        return;
      }

      setScrollPosition(prev => {
        const newPosition = prev + (settings.scrollSpeed / 60); // 60fps
        return newPosition > contentWidth ? -containerWidth : newPosition;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isScrolling, isPaused, isVisible, settings.scrollSpeed]);

  // Event handlers
  const handlePause = useCallback(() => {
    setIsPaused(true);
    onPause?.();
  }, [onPause]);

  const handleResume = useCallback(() => {
    setIsPaused(false);
    onResume?.();
  }, [onResume]);

  const handleItemClick = useCallback((update: ScoreUpdate) => {
    onItemClick?.(update);
  }, [onItemClick]);

  const handleMouseEnter = useCallback(() => {
    handlePause();
  }, [handlePause]);

  const handleMouseLeave = useCallback(() => {
    handleResume();
  }, [handleResume]);

  // Render update item
  const renderUpdate = useCallback((update: ScoreUpdate) => {
    const isPlayerScore = update.type === 'player_score' && update.points;
    const isBreakingNews = update.type === 'breaking_news' || update.urgent;

    const itemStyles: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      padding: variant === 'compact'
        ? `${fantasyTheme.spacing[1]} ${fantasyTheme.spacing[3]}`
        : `${fantasyTheme.spacing[2]} ${fantasyTheme.spacing[4]}`,
      margin: `0 ${fantasyTheme.spacing[2]}`,
      backgroundColor: update.highlighted || isBreakingNews
        ? fantasyTheme.brandColors.warning[100]
        : themeColors.surface.default,
      border: `1px solid ${update.highlighted || isBreakingNews
        ? fantasyTheme.brandColors.warning[300]
        : themeColors.border.light}`,
      borderRadius: fantasyTheme.borderRadius.md,
      cursor: onItemClick ? 'pointer' : 'default',
      whiteSpace: 'nowrap',
      minWidth: 'max-content',
    };

    return (
      <div
        key={update.id}
        style={itemStyles}
        onClick={() => handleItemClick(update)}
      >
        {/* Urgency indicator */}
        {(update.urgent || isBreakingNews) && (
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: fantasyTheme.brandColors.error[500],
            marginRight: fantasyTheme.spacing[2],
            animation: 'pulse 1.5s infinite',
          }} />
        )}

        {/* Position indicator for player updates */}
        {isPlayerScore && update.playerPosition && (
          <div style={{
            width: '3px',
            height: variant === 'compact' ? '16px' : '20px',
            backgroundColor: getPositionColor(update.playerPosition),
            marginRight: fantasyTheme.spacing[2],
            borderRadius: fantasyTheme.borderRadius.sm,
          }} />
        )}

        {/* Content */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: fantasyTheme.spacing[2],
        }}>
          {/* Player/Game info */}
          <div>
            {isPlayerScore ? (
              <div>
                <span style={{
                  fontSize: variant === 'compact'
                    ? fantasyTheme.typography.fontSize.xs
                    : fantasyTheme.typography.fontSize.sm,
                  fontWeight: fantasyTheme.typography.fontWeight.semibold,
                  color: themeColors.text.primary,
                }}>
                  {update.playerName}
                </span>

                {update.playerPosition && (
                  <span style={{
                    fontSize: fantasyTheme.typography.fontSize.xs,
                    color: getPositionColor(update.playerPosition),
                    marginLeft: fantasyTheme.spacing[1],
                  }}>
                    {update.playerPosition}
                  </span>
                )}

                {variant !== 'compact' && update.statType && (
                  <span style={{
                    fontSize: fantasyTheme.typography.fontSize.xs,
                    color: themeColors.text.secondary,
                    marginLeft: fantasyTheme.spacing[2],
                  }}>
                    {update.statType}
                    {update.statValue && ` (${update.statValue})`}
                  </span>
                )}
              </div>
            ) : update.type === 'game_score' ? (
              <div>
                <span style={{
                  fontSize: variant === 'compact'
                    ? fantasyTheme.typography.fontSize.xs
                    : fantasyTheme.typography.fontSize.sm,
                  fontWeight: fantasyTheme.typography.fontWeight.semibold,
                  color: themeColors.text.primary,
                }}>
                  {update.homeTeam} vs {update.awayTeam}
                </span>

                {variant !== 'compact' && update.quarter && (
                  <span style={{
                    fontSize: fantasyTheme.typography.fontSize.xs,
                    color: themeColors.text.secondary,
                    marginLeft: fantasyTheme.spacing[2],
                  }}>
                    Q{update.quarter}
                    {update.timeRemaining && ` ${update.timeRemaining}`}
                  </span>
                )}
              </div>
            ) : (
              <div>
                <span style={{
                  fontSize: variant === 'compact'
                    ? fantasyTheme.typography.fontSize.xs
                    : fantasyTheme.typography.fontSize.sm,
                  fontWeight: fantasyTheme.typography.fontWeight.semibold,
                  color: isBreakingNews
                    ? fantasyTheme.brandColors.error[700]
                    : themeColors.text.primary,
                }}>
                  {update.title || update.description}
                </span>
              </div>
            )}
          </div>

          {/* Points/Score */}
          {isPlayerScore && update.points !== undefined && (
            <div style={{
              fontSize: variant === 'compact'
                ? fantasyTheme.typography.fontSize.sm
                : fantasyTheme.typography.fontSize.lg,
              fontWeight: fantasyTheme.typography.fontWeight.bold,
              color: getScoringColor(update.points),
              marginLeft: fantasyTheme.spacing[2],
            }}>
              {update.points > 0 ? '+' : ''}{update.points.toFixed(1)}
            </div>
          )}

          {/* Timestamp */}
          {variant === 'detailed' && (
            <div style={{
              fontSize: fantasyTheme.typography.fontSize.xs,
              color: themeColors.text.muted,
              marginLeft: fantasyTheme.spacing[3],
            }}>
              {new Date(update.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>
    );
  }, [variant, themeColors, onItemClick, handleItemClick]);

  // Container styles based on position
  const getContainerStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: position === 'floating' ? 'fixed' : 'relative',
      left: 0,
      right: 0,
      backgroundColor: themeColors.background.secondary,
      borderTop: position === 'bottom' ? `1px solid ${themeColors.border.default}` : undefined,
      borderBottom: position === 'top' ? `1px solid ${themeColors.border.default}` : undefined,
      boxShadow: position === 'floating' ? fantasyTheme.shadows.lg : undefined,
      zIndex: position === 'floating' ? fantasyTheme.zIndex.fixed : 'auto',
      height: variant === 'compact' ? '40px' : variant === 'detailed' ? '60px' : '48px',
      overflow: 'hidden',
      transform: isVisible ? 'translateY(0)' : `translateY(${position === 'top' ? '-100%' : '100%'})`,
      transition: 'transform 0.3s ease-in-out',
      ...style,
    };

    if (position === 'top') {
      baseStyles.top = 0;
    } else if (position === 'bottom') {
      baseStyles.bottom = 0;
    } else {
      baseStyles.top = '50%';
      baseStyles.transform = `translateY(-50%) ${isVisible ? 'translateY(0)' : 'translateY(100%)'}`;
    }

    return baseStyles;
  };

  if (!isVisible || liveUpdates.length === 0) {
    return null;
  }

  return (
    <div
      className={`score-ticker ${className}`}
      style={getContainerStyles()}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Control buttons */}
      <div style={{
        position: 'absolute',
        right: fantasyTheme.spacing[2],
        top: '50%',
        transform: 'translateY(-50%)',
        display: 'flex',
        gap: fantasyTheme.spacing[1],
        zIndex: 1,
      }}>
        <button
          onClick={isPaused ? handleResume : handlePause}
          style={{
            backgroundColor: 'transparent',
            border: `1px solid ${themeColors.border.default}`,
            borderRadius: fantasyTheme.borderRadius.sm,
            padding: fantasyTheme.spacing[1],
            color: themeColors.text.secondary,
            cursor: 'pointer',
            fontSize: fantasyTheme.typography.fontSize.xs,
          }}
        >
          {isPaused ? '▶' : '⏸'}
        </button>

        <button
          onClick={() => setIsVisible(false)}
          style={{
            backgroundColor: 'transparent',
            border: `1px solid ${themeColors.border.default}`,
            borderRadius: fantasyTheme.borderRadius.sm,
            padding: fantasyTheme.spacing[1],
            color: themeColors.text.secondary,
            cursor: 'pointer',
            fontSize: fantasyTheme.typography.fontSize.xs,
          }}
        >
          ✕
        </button>
      </div>

      {/* Scrolling content */}
      <div
        ref={tickerRef}
        style={{
          height: '100%',
          overflow: 'hidden',
          paddingRight: '80px', // Space for controls
        }}
      >
        <div
          ref={contentRef}
          style={{
            display: 'flex',
            alignItems: 'center',
            height: '100%',
            transform: `translateX(-${scrollPosition}px)`,
            transition: isPaused ? 'none' : undefined,
          }}
        >
          {liveUpdates.map(renderUpdate)}

          {/* Spacer to ensure continuous scroll */}
          <div style={{ width: '100px', flexShrink: 0 }} />
        </div>
      </div>

      {/* Breaking news indicator */}
      {liveUpdates.some(update => update.urgent || update.type === 'breaking_news') && (
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '4px',
          backgroundColor: fantasyTheme.brandColors.error[500],
          animation: 'pulse 1.5s infinite',
        }} />
      )}

      {/* Live indicator */}
      <div style={{
        position: 'absolute',
        left: fantasyTheme.spacing[2],
        top: '50%',
        transform: 'translateY(-50%)',
        display: 'flex',
        alignItems: 'center',
        gap: fantasyTheme.spacing[1],
      }}>
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: fantasyTheme.brandColors.success[500],
          animation: 'pulse 2s infinite',
        }} />
        <span style={{
          fontSize: fantasyTheme.typography.fontSize.xs,
          fontWeight: fantasyTheme.typography.fontWeight.semibold,
          color: fantasyTheme.brandColors.success[600],
          textTransform: 'uppercase',
        }}>
          LIVE
        </span>
      </div>
    </div>
  );
};

export default ScoreTicker;