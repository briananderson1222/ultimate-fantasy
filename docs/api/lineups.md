# Lineups API

## Overview

The Lineups API provides comprehensive lineup management functionality including roster optimization, player management, and weekly lineup submissions for fantasy sports leagues.

## Base URL

```
/api/v1/lineups
```

## Endpoints

### Get Team Lineup

Get current lineup for a team.

**GET** `/teams/{team_id}`

**Authentication Required**

#### Query Parameters

- `week` (optional): Specific week number (default: current week)
- `season` (optional): Season year (default: current season)

#### Response

```json
{
  "success": true,
  "data": {
    "lineup": {
      "team_id": "uuid",
      "team_name": "Team Name",
      "week": 12,
      "season": "2024",
      "is_submitted": true,
      "submitted_at": "2024-06-10T14:30:00Z",
      "lineup_deadline": "2024-06-11T13:00:00Z",
      "projected_points": 125.5,
      "starting_lineup": [
        {
          "position": "C",
          "player_id": "uuid",
          "player_name": "Player Name",
          "team": "LAD",
          "status": "active",
          "game_info": {
            "opponent": "SF",
            "game_time": "2024-06-11T19:10:00Z",
            "is_home": true,
            "weather": "Clear, 75°F"
          },
          "projection": {
            "fantasy_points": 8.5,
            "key_stats": {
              "at_bats": 4,
              "hits": 1.2,
              "home_runs": 0.15,
              "rbi": 0.8
            }
          },
          "actual_stats": null
        }
      ],
      "bench": [
        {
          "player_id": "uuid",
          "player_name": "Bench Player",
          "position": "OF",
          "team": "NYY",
          "status": "inactive",
          "reason": "Bench player"
        }
      ]
    },
    "roster_requirements": {
      "C": 1,
      "1B": 1,
      "2B": 1,
      "3B": 1,
      "SS": 1,
      "OF": 3,
      "UTIL": 1,
      "SP": 2,
      "RP": 2,
      "BENCH": 5
    }
  }
}
```

---

### Update Lineup

Update team lineup for a specific week.

**PUT** `/teams/{team_id}`

**Authentication Required**

#### Request Body

```json
{
  "week": 12,
  "lineup_changes": [
    {
      "action": "start",
      "player_id": "uuid",
      "position": "OF"
    },
    {
      "action": "bench",
      "player_id": "uuid"
    }
  ]
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "lineup": {
      "team_id": "uuid",
      "week": 12,
      "changes_applied": 2,
      "projected_points": 127.2,
      "is_submitted": false,
      "updated_at": "2024-06-10T15:00:00Z"
    },
    "changes": [
      {
        "action": "start",
        "player_name": "New Starter",
        "position": "OF",
        "projected_impact": "+1.7 points"
      },
      {
        "action": "bench",
        "player_name": "Benched Player",
        "projected_impact": "-2.3 points"
      }
    ]
  }
}
```

#### Error Codes

- `LINEUP_LOCKED` - Lineup deadline has passed
- `INVALID_LINEUP` - Lineup doesn't meet requirements
- `PLAYER_NOT_ON_ROSTER` - Player not owned by team
- `PLAYER_INJURED` - Player is injured and cannot start

---

### Submit Lineup

Submit lineup for scoring (locks changes).

**POST** `/teams/{team_id}/submit`

**Authentication Required**

#### Request Body

```json
{
  "week": 12
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "lineup": {
      "team_id": "uuid",
      "week": 12,
      "is_submitted": true,
      "submitted_at": "2024-06-10T15:30:00Z",
      "projected_points": 127.2,
      "lineup_hash": "abc123def456"
    },
    "confirmation": {
      "message": "Lineup submitted successfully",
      "can_modify_until": "2024-06-11T13:00:00Z"
    }
  }
}
```

---

### Get Lineup Optimization

Get AI-powered lineup optimization suggestions.

**GET** `/teams/{team_id}/optimize`

**Authentication Required**

#### Query Parameters

- `week` (optional): Week to optimize (default: current)
- `strategy` (optional): ceiling, floor, balanced (default: balanced)
- `risk_tolerance` (optional): conservative, moderate, aggressive

#### Response

```json
{
  "success": true,
  "data": {
    "optimization": {
      "team_id": "uuid",
      "week": 12,
      "strategy": "balanced",
      "current_projection": 125.5,
      "optimized_projection": 132.8,
      "improvement": "+7.3 points"
    },
    "suggested_changes": [
      {
        "type": "position_swap",
        "current_player": {
          "player_id": "uuid",
          "name": "Current Player",
          "position": "OF",
          "projection": 8.2
        },
        "suggested_player": {
          "player_id": "uuid",
          "name": "Better Player",
          "position": "OF",
          "projection": 12.5
        },
        "impact": "+4.3 points",
        "confidence": 0.85,
        "reasoning": "Better matchup vs weak pitching"
      }
    ],
    "lineup_analysis": {
      "strengths": ["Strong hitting matchups", "Pitching advantage"],
      "concerns": ["Weather risk for outdoor games"],
      "recommendations": ["Consider benching players in bad weather"]
    }
  }
}
```

---

### Apply Optimization

Apply suggested lineup optimization.

**POST** `/teams/{team_id}/optimize/apply`

**Authentication Required**

#### Request Body

```json
{
  "week": 12,
  "changes_to_apply": [
    {
      "change_id": "uuid",
      "confirmed": true
    }
  ]
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "lineup": {
      "team_id": "uuid",
      "week": 12,
      "changes_applied": 3,
      "new_projection": 132.8,
      "optimization_complete": true
    },
    "applied_changes": [
      {
        "type": "position_swap",
        "players_involved": ["Player A", "Player B"],
        "projected_impact": "+4.3 points"
      }
    ]
  }
}
```

---

### Get Weekly Matchup

Get detailed matchup information for a team's weekly opponents.

**GET** `/teams/{team_id}/matchup`

**Authentication Required**

#### Query Parameters

- `week` (optional): Week number (default: current)

#### Response

```json
{
  "success": true,
  "data": {
    "matchup": {
      "week": 12,
      "team": {
        "id": "uuid",
        "name": "Team Name",
        "projected_points": 127.2,
        "lineup_submitted": true
      },
      "opponent": {
        "id": "uuid",
        "name": "Opponent Team",
        "projected_points": 122.8,
        "lineup_submitted": false
      },
      "prediction": {
        "favored_team": "uuid",
        "win_probability": 0.65,
        "projected_margin": 4.4,
        "confidence": 0.78
      }
    },
    "key_matchups": [
      {
        "position": "SP",
        "your_player": {
          "name": "Your Pitcher",
          "projection": 15.2,
          "matchup_rating": "excellent"
        },
        "opponent_player": {
          "name": "Opponent Pitcher",
          "projection": 12.8,
          "matchup_rating": "average"
        },
        "advantage": "your_team",
        "impact": "high"
      }
    ],
    "weather_alerts": [
      {
        "game_id": "uuid",
        "teams": ["LAD", "SF"],
        "condition": "Rain expected",
        "impact": "Potential postponement",
        "affected_players": ["Player A", "Player B"]
      }
    ]
  }
}
```

---

### Get Player Performance

Get detailed performance history for a player.

**GET** `/players/{player_id}/performance`

**Authentication Required**

#### Query Parameters

- `weeks` (optional): Number of weeks to include (default: 4)
- `vs_position` (optional): Performance vs specific position
- `home_away` (optional): Filter by home/away games

#### Response

```json
{
  "success": true,
  "data": {
    "player": {
      "player_id": "uuid",
      "name": "Player Name",
      "position": "OF",
      "team": "LAD"
    },
    "recent_performance": [
      {
        "week": 11,
        "opponent": "SF",
        "fantasy_points": 12.5,
        "stats": {
          "at_bats": 4,
          "hits": 2,
          "home_runs": 1,
          "rbi": 3,
          "runs": 2
        },
        "game_context": {
          "home_away": "home",
          "weather": "Clear",
          "opposing_pitcher": "Left-handed"
        }
      }
    ],
    "season_averages": {
      "fantasy_points_per_game": 9.8,
      "consistency_score": 0.72,
      "ceiling_games": 8,
      "floor_games": 3
    },
    "trends": {
      "last_4_weeks": "+2.3 points above average",
      "vs_position": "Excellent vs RHP, Average vs LHP",
      "home_away": "Better at home (+1.8 ppg)"
    },
    "upcoming_schedule": [
      {
        "week": 12,
        "opponent": "COL",
        "pitcher_handedness": "right",
        "park_factor": 1.15,
        "matchup_rating": "excellent"
      }
    ]
  }
}
```

---

### Get Lineup Scoring

Get scoring results for a completed week.

**GET** `/teams/{team_id}/scoring`

**Authentication Required**

#### Query Parameters

- `week` (required): Week number to get scores for

#### Response

```json
{
  "success": true,
  "data": {
    "scoring": {
      "team_id": "uuid",
      "week": 11,
      "total_points": 134.7,
      "projected_points": 127.2,
      "vs_projection": "+7.5",
      "league_rank": 3,
      "starting_lineup": [
        {
          "position": "C",
          "player_name": "Player Name",
          "projected": 8.5,
          "actual": 12.2,
          "stats": {
            "at_bats": 4,
            "hits": 3,
            "home_runs": 1,
            "rbi": 2,
            "runs": 2
          },
          "performance": "exceeded"
        }
      ],
      "bench_points": 15.3,
      "optimal_lineup_points": 142.1,
      "efficiency_score": 0.95
    },
    "weekly_summary": {
      "best_performer": {
        "player_name": "Star Player",
        "points": 18.7,
        "performance": "Excellent"
      },
      "worst_performer": {
        "player_name": "Struggling Player",
        "points": 2.1,
        "performance": "Poor"
      },
      "biggest_surprise": {
        "player_name": "Unexpected Hero",
        "projected": 6.2,
        "actual": 15.8,
        "difference": "+9.6"
      }
    }
  }
}
```

---

### Get Waiver Wire Targets

Get recommended waiver wire pickups based on lineup needs.

**GET** `/teams/{team_id}/waiver-targets`

**Authentication Required**

#### Query Parameters

- `position` (optional): Filter by position need
- `limit` (optional): Number of recommendations (default: 10)

#### Response

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "player_id": "uuid",
        "name": "Waiver Target",
        "position": "OF",
        "team": "MIA",
        "ownership_percentage": 25.3,
        "projected_points": 11.2,
        "reason": "Strong upcoming schedule",
        "priority": "high",
        "roster_impact": "Immediate starter",
        "next_3_weeks": [
          {
            "week": 12,
            "opponent": "WAS",
            "projection": 12.5,
            "matchup_rating": "excellent"
          }
        ]
      }
    ],
    "lineup_analysis": {
      "weakest_positions": ["OF", "SP"],
      "upcoming_bye_weeks": [],
      "injury_concerns": ["Player X - Day-to-day"]
    },
    "waiver_budget_remaining": 85,
    "suggested_bids": [
      {
        "player_name": "Waiver Target",
        "suggested_bid": 15,
        "reasoning": "High upside, immediate need"
      }
    ]
  }
}
```

## Lineup Rules and Validation

### Position Requirements

Standard lineup requirements vary by sport:

**MLB:**
- C: 1
- 1B: 1
- 2B: 1
- 3B: 1
- SS: 1
- OF: 3
- UTIL: 1
- SP: 2
- RP: 2
- Bench: 5

### Lineup Deadlines

- Daily lineups: 1 hour before first game
- Weekly lineups: Tuesday 1:00 PM ET
- Emergency changes: Until player's game starts

### Validation Rules

- All required positions must be filled
- Players must be on team roster
- Players cannot be in lineup if injured (DTD allowed)
- Position eligibility verified
- Game time conflicts checked

## Real-time Updates

### WebSocket Connection

Connect to real-time lineup updates:

```
/ws/lineups/{team_id}
```

#### Message Types

```json
{
  "type": "lineup_deadline_warning",
  "data": {
    "minutes_remaining": 30,
    "unsubmitted_lineups": 1
  }
}
```

```json
{
  "type": "player_injury_update",
  "data": {
    "player_id": "uuid",
    "player_name": "Player Name",
    "injury_status": "questionable",
    "impact": "May need lineup adjustment"
  }
}
```

```json
{
  "type": "game_postponed",
  "data": {
    "game_id": "uuid",
    "affected_players": ["Player A", "Player B"],
    "recommendation": "Replace in lineup"
  }
}
```