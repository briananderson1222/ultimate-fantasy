'use client';

import React, { useState } from 'react';
import { Card } from '../primitives/Card';
import { Button } from '../primitives/Button';
import { ProgressBar } from '../primitives/ProgressBar';
import { Avatar } from '../primitives/Avatar';
import { cn } from '../../../lib/utils';

export interface TrendData {
  direction: 'up' | 'down' | 'hot';
  percentage: number;
  reason: string;
  addDropPercentage: number;
}

export interface TrendingPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  photoUrl?: string;
  trendData: TrendData;
  weeklyPoints: number[];
  projectedPoints: number;
}

export interface TrendingPlayersFilters {
  position?: string[];
  trend?: string[];
  availability?: string[];
}

export interface TrendingPlayersProps {
  players: TrendingPlayer[];
  title?: string;
  variant?: 'default' | 'compact';
  loading?: boolean;
  filters?: TrendingPlayersFilters;
  showActions?: boolean;
  onFilterChange?: (filters: TrendingPlayersFilters) => void;
  onAddPlayer?: (playerId: string) => void;
  onWatchPlayer?: (playerId: string) => void;
  className?: string;
}

const getTrendIcon = (direction: TrendData['direction']) => {
  switch (direction) {
    case 'up':
      return '↗️';
    case 'down':
      return '↘️';
    case 'hot':
      return '🔥';
    default:
      return '—';
  }
};

const getTrendColor = (direction: TrendData['direction']) => {
  switch (direction) {
    case 'up':
      return 'text-green-600';
    case 'down':
      return 'text-red-600';
    case 'hot':
      return 'text-orange-600';
    default:
      return 'text-gray-600';
  }
};

const WeeklyTrend: React.FC<{ points: number[] }> = ({ points }) => {
  const maxPoints = Math.max(...points);
  const minPoints = Math.min(...points);
  const range = maxPoints - minPoints || 1;

  return (
    <div className="flex items-end gap-1 h-8">
      {points.map((point, index) => {
        const height = ((point - minPoints) / range) * 100;
        return (
          <div
            key={index}
            className="bg-blue-200 rounded-sm flex-1 min-h-[2px]"
            style={{ height: `${Math.max(height, 10)}%` }}
            title={`Week ${index + 1}: ${point.toFixed(1)} pts`}
          />
        );
      })}
    </div>
  );
};

export const TrendingPlayers: React.FC<TrendingPlayersProps> = ({
  players,
  title = 'Trending Players',
  variant = 'default',
  loading = false,
  filters,
  showActions = false,
  onFilterChange,
  onAddPlayer,
  onWatchPlayer,
  className
}) => {
  const [activeFilters, setActiveFilters] = useState<TrendingPlayersFilters>(filters || {});

  const handleFilterChange = (filterType: keyof TrendingPlayersFilters, value: string) => {
    const newFilters = { ...activeFilters };
    if (!newFilters[filterType]) {
      newFilters[filterType] = [];
    }

    const currentValues = newFilters[filterType] as string[];
    if (currentValues.includes(value)) {
      newFilters[filterType] = currentValues.filter(v => v !== value);
    } else {
      newFilters[filterType] = [...currentValues, value];
    }

    setActiveFilters(newFilters);
    onFilterChange?.(newFilters);
  };

  if (loading) {
    return (
      <Card className={className}>
        <Card.Header>
          <h3 className="font-semibold">{title}</h3>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-200 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-1/3" />
                    <div className="h-3 bg-gray-200 rounded w-1/4" />
                  </div>
                  <div className="w-16 h-4 bg-gray-200 rounded" />
                </div>
              </div>
            ))}
          </div>
        </Card.Content>
      </Card>
    );
  }

  if (players.length === 0) {
    return (
      <Card className={className}>
        <Card.Header>
          <h3 className="font-semibold">{title}</h3>
        </Card.Header>
        <Card.Content>
          <div className="text-center py-8 text-muted-foreground">
            <div className="text-4xl mb-2">📈</div>
            <div>No trending players found</div>
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <Card.Header>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{title}</h3>
          {filters && (
            <div className="flex gap-2">
              {filters.position?.map(pos => (
                <Button
                  key={pos}
                  variant="outline"
                  size="sm"
                  onClick={() => handleFilterChange('position', pos)}
                  className={cn(
                    activeFilters.position?.includes(pos) && 'bg-primary text-white'
                  )}
                >
                  {pos}
                </Button>
              ))}
            </div>
          )}
        </div>
      </Card.Header>

      <Card.Content>
        <div className="space-y-4">
          {players.map((player) => {
            const { id, name, position, team, photoUrl, trendData, weeklyPoints, projectedPoints } = player;

            if (variant === 'compact') {
              return (
                <div key={id} className="flex items-center gap-3 py-2">
                  <Avatar
                    src={photoUrl}
                    alt={name}
                    fallback={name.split(' ').map(n => n[0]).join('')}
                    size="sm"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{name}</div>
                    <div className="text-xs text-muted-foreground">
                      {position} • {team}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={cn('text-sm', getTrendColor(trendData.direction))}>
                      {getTrendIcon(trendData.direction)} {Math.abs(trendData.percentage).toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            }

            return (
              <div key={id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar
                      src={photoUrl}
                      alt={name}
                      fallback={name.split(' ').map(n => n[0]).join('')}
                      size="md"
                    />
                    <div>
                      <div className="font-semibold">{name}</div>
                      <div className="text-sm text-muted-foreground">
                        {position} • {team}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn('font-bold', getTrendColor(trendData.direction))}>
                      {getTrendIcon(trendData.direction)} {Math.abs(trendData.percentage).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Proj: {projectedPoints.toFixed(1)}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">{trendData.reason}</div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Add/Drop Percentage</span>
                      <span>{trendData.addDropPercentage > 0 ? '+' : ''}{trendData.addDropPercentage.toFixed(1)}%</span>
                    </div>
                    <ProgressBar
                      value={Math.abs(trendData.addDropPercentage)}
                      max={100}
                      variant={trendData.addDropPercentage > 0 ? 'success' : 'error'}
                      size="sm"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Weekly Trend</div>
                    <WeeklyTrend points={weeklyPoints} />
                  </div>
                </div>

                {showActions && (
                  <div className="flex gap-2">
                    {onAddPlayer && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => onAddPlayer(id)}
                      >
                        Add
                      </Button>
                    )}
                    {onWatchPlayer && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onWatchPlayer(id)}
                      >
                        Watch
                      </Button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card.Content>
    </Card>
  );
};