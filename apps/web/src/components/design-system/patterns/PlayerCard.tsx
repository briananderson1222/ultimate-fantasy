'use client';

import React from 'react';
import { Card } from '../primitives/Card';
import { Avatar } from '../primitives/Avatar';
import { Button } from '../primitives/Button';
import { cn } from '../../../lib/utils';

export interface PlayerStats {
  points: number;
  projected: number;
  [key: string]: number; // Additional stats like rushingYards, touchdowns, etc.
}

export interface PlayerInjury {
  status: 'questionable' | 'doubtful' | 'out' | 'probable';
  description: string;
}

export interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  photoUrl?: string;
  stats: PlayerStats;
  injury?: PlayerInjury | null;
  status: 'active' | 'bench' | 'injured' | 'bye';
}

export interface PlayerAction {
  label: string;
  action: () => void;
  destructive?: boolean;
}

export interface PlayerCardProps {
  player: Player;
  variant?: 'default' | 'compact';
  actions?: PlayerAction[];
  draggable?: boolean;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  className?: string;
}

const getInjuryStatusColor = (status: PlayerInjury['status']) => {
  switch (status) {
    case 'out':
      return 'text-red-600 bg-red-100';
    case 'doubtful':
      return 'text-red-600 bg-red-50';
    case 'questionable':
      return 'text-yellow-600 bg-yellow-100';
    case 'probable':
      return 'text-green-600 bg-green-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

const getStatusColor = (status: Player['status']) => {
  switch (status) {
    case 'active':
      return 'text-green-600 bg-green-100';
    case 'bench':
      return 'text-gray-600 bg-gray-100';
    case 'injured':
      return 'text-red-600 bg-red-100';
    case 'bye':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

const getPerformanceColor = (actual: number, projected: number) => {
  const diff = ((actual - projected) / projected) * 100;
  if (diff > 10) return 'text-green-600';
  if (diff < -10) return 'text-red-600';
  return 'text-gray-600';
};

export const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  variant = 'default',
  actions,
  draggable = false,
  onDragStart,
  onDragEnd,
  className
}) => {
  const { name, position, team, photoUrl, stats, injury, status } = player;
  const performanceColor = getPerformanceColor(stats.points, stats.projected);

  if (variant === 'compact') {
    return (
      <Card
        className={cn(
          'p-3',
          draggable && 'cursor-move',
          className
        )}
        draggable={draggable}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar
              src={photoUrl}
              alt={name}
              fallback={name.split(' ').map(n => n[0]).join('')}
              size="sm"
            />
            <div className="min-w-0 flex-1">
              <div className="font-medium text-sm truncate">{name}</div>
              <div className="text-xs text-muted-foreground">
                {position} • {team}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className={cn('font-bold text-sm', performanceColor)}>
              {stats.points.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">
              ({stats.projected.toFixed(1)})
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        'w-full',
        draggable && 'cursor-move',
        className
      )}
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
    >
      <Card.Header>
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
          <div className="flex flex-col gap-1">
            <div className={cn(
              'text-xs px-2 py-1 rounded-full text-center',
              getStatusColor(status)
            )}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
            {injury && (
              <div className={cn(
                'text-xs px-2 py-1 rounded-full text-center',
                getInjuryStatusColor(injury.status)
              )}>
                {injury.status.charAt(0).toUpperCase() + injury.status.slice(1)}
              </div>
            )}
          </div>
        </div>
      </Card.Header>

      <Card.Content>
        <div className="space-y-3">
          {/* Points Performance */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Fantasy Points</span>
            <div className="text-right">
              <div className={cn('text-lg font-bold', performanceColor)}>
                {stats.points.toFixed(1)}
              </div>
              <div className="text-xs text-muted-foreground">
                Projected: {stats.projected.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Additional Stats */}
          {Object.entries(stats)
            .filter(([key]) => !['points', 'projected'].includes(key))
            .slice(0, 3)
            .map(([statName, value]) => (
              <div key={statName} className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground capitalize">
                  {statName.replace(/([A-Z])/g, ' $1').trim()}
                </span>
                <span className="text-sm font-medium">{value}</span>
              </div>
            ))
          }

          {/* Injury Information */}
          {injury && (
            <div className="text-xs text-muted-foreground">
              <span className="font-medium">Injury:</span> {injury.description}
            </div>
          )}
        </div>
      </Card.Content>

      {actions && actions.length > 0 && (
        <Card.Footer>
          <div className="flex gap-2 flex-wrap">
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.destructive ? 'danger' : 'outline'}
                size="sm"
                onClick={action.action}
              >
                {action.label}
              </Button>
            ))}
          </div>
        </Card.Footer>
      )}
    </Card>
  );
};