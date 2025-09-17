'use client';

import React from 'react';
import { Card } from '../primitives/Card';
import { Avatar } from '../primitives/Avatar';
import { cn } from '../../../lib/utils';

export interface Team {
  id: string;
  name: string;
  owner: string;
  logo?: string;
  record: {
    wins: number;
    losses: number;
  };
}

export interface Match {
  homeTeam: Team;
  awayTeam: Team;
  week: number;
  projectedPoints?: {
    home: number;
    away: number;
  };
  actualPoints?: {
    home: number;
    away: number;
  };
  status: 'upcoming' | 'in_progress' | 'completed';
  playoffImplications?: string;
}

export interface MatchCardProps {
  match: Match;
  onClick?: () => void;
  showDetailsButton?: boolean;
  className?: string;
}

const formatRecord = (record: { wins: number; losses: number }) => {
  return `${record.wins}-${record.losses}`;
};

const getWinner = (actualPoints: { home: number; away: number }) => {
  if (actualPoints.home > actualPoints.away) return 'home';
  if (actualPoints.away > actualPoints.home) return 'away';
  return 'tie';
};

export const MatchCard: React.FC<MatchCardProps> = ({
  match,
  onClick,
  showDetailsButton = false,
  className
}) => {
  const { homeTeam, awayTeam, week, projectedPoints, actualPoints, status, playoffImplications } = match;
  const isClickable = !!onClick;
  const winner = actualPoints ? getWinner(actualPoints) : null;

  return (
    <Card
      clickable={isClickable}
      className={cn('w-full', className)}
      onClick={onClick}
    >
      <Card.Header>
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-muted-foreground">
            Week {week}
          </div>
          <div className={cn(
            'text-xs px-2 py-1 rounded-full',
            status === 'upcoming' && 'bg-blue-100 text-blue-700',
            status === 'in_progress' && 'bg-yellow-100 text-yellow-700',
            status === 'completed' && 'bg-green-100 text-green-700'
          )}>
            {status === 'upcoming' && 'Upcoming'}
            {status === 'in_progress' && 'Live'}
            {status === 'completed' && 'Final'}
          </div>
        </div>
        {playoffImplications && (
          <div className="text-xs text-purple-600 font-medium">
            {playoffImplications}
          </div>
        )}
      </Card.Header>

      <Card.Content>
        <div className="space-y-4">
          {/* Away Team */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar
                src={awayTeam.logo}
                alt={awayTeam.name}
                fallback={awayTeam.name.charAt(0)}
                size="sm"
              />
              <div>
                <div className={cn(
                  'font-semibold',
                  winner === 'away' && 'text-green-600'
                )}>
                  {awayTeam.name}
                </div>
                <div className="text-sm text-muted-foreground">
                  {awayTeam.owner} ({formatRecord(awayTeam.record)})
                </div>
              </div>
            </div>
            <div className="text-right">
              {actualPoints && (
                <div className={cn(
                  'text-lg font-bold',
                  winner === 'away' && 'text-green-600'
                )}>
                  {actualPoints.away.toFixed(1)}
                </div>
              )}
              {projectedPoints && !actualPoints && (
                <div className="text-sm text-muted-foreground">
                  Proj: {projectedPoints.away.toFixed(1)}
                </div>
              )}
              {projectedPoints && actualPoints && (
                <div className="text-xs text-muted-foreground">
                  ({projectedPoints.away.toFixed(1)})
                </div>
              )}
            </div>
          </div>

          {/* VS Divider */}
          <div className="flex items-center justify-center">
            <div className="text-xs text-muted-foreground font-medium">
              VS
            </div>
          </div>

          {/* Home Team */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar
                src={homeTeam.logo}
                alt={homeTeam.name}
                fallback={homeTeam.name.charAt(0)}
                size="sm"
              />
              <div>
                <div className={cn(
                  'font-semibold',
                  winner === 'home' && 'text-green-600'
                )}>
                  {homeTeam.name}
                </div>
                <div className="text-sm text-muted-foreground">
                  {homeTeam.owner} ({formatRecord(homeTeam.record)})
                </div>
              </div>
            </div>
            <div className="text-right">
              {actualPoints && (
                <div className={cn(
                  'text-lg font-bold',
                  winner === 'home' && 'text-green-600'
                )}>
                  {actualPoints.home.toFixed(1)}
                </div>
              )}
              {projectedPoints && !actualPoints && (
                <div className="text-sm text-muted-foreground">
                  Proj: {projectedPoints.home.toFixed(1)}
                </div>
              )}
              {projectedPoints && actualPoints && (
                <div className="text-xs text-muted-foreground">
                  ({projectedPoints.home.toFixed(1)})
                </div>
              )}
            </div>
          </div>
        </div>
      </Card.Content>

      {showDetailsButton && (
        <Card.Footer>
          <button className="text-sm text-primary hover:underline">
            View Details
          </button>
        </Card.Footer>
      )}
    </Card>
  );
};