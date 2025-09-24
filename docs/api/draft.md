# Draft API

## Overview

The Draft API provides comprehensive draft management functionality including draft room operations, pick tracking, auto-draft capabilities, and real-time updates for fantasy sports leagues.

## Base URL

```
/api/v1/drafts
```

## Draft Types

- **Snake Draft** - Alternating pick order each round
- **Auction Draft** - Bidding system with salary cap
- **Linear Draft** - Same pick order each round

## Endpoints

### Create Draft

Create a new draft for a league.

**POST** `/`

**Authentication Required - Commissioner Only**

#### Request Body

```json
{
  "league_id": "uuid",
  "draft_type": "snake|auction|linear",
  "scheduled_start": "2024-03-01T20:00:00Z",
  "rounds": 16,
  "pick_time_seconds": 90,
  "auto_pick_enabled": true,
  "auction_budget": 200
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "uuid",
      "league_id": "uuid",
      "draft_type": "snake",
      "status": "scheduled",
      "scheduled_start": "2024-03-01T20:00:00Z",
      "rounds": 16,
      "pick_time_seconds": 90,
      "auto_pick_enabled": true,
      "total_picks": 192,
      "current_pick": 0,
      "created_at": "2024-01-01T00:00:00Z"
    },
    "draft_order": [
      {
        "team_id": "uuid",
        "team_name": "Team Name",
        "draft_position": 1,
        "owner_name": "Owner Name"
      }
    ]
  }
}
```

---

### Get Draft

Get detailed draft information and current state.

**GET** `/{draft_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "uuid",
      "league_id": "uuid",
      "draft_type": "snake",
      "status": "in_progress",
      "started_at": "2024-03-01T20:00:00Z",
      "rounds": 16,
      "pick_time_seconds": 90,
      "auto_pick_enabled": true,
      "total_picks": 192,
      "current_pick": 45,
      "current_round": 3,
      "time_remaining": 75
    },
    "current_pick_info": {
      "pick_number": 45,
      "round": 3,
      "team_id": "uuid",
      "team_name": "Team Name",
      "owner_name": "Owner Name",
      "pick_deadline": "2024-03-01T21:45:00Z",
      "auto_pick_at": "2024-03-01T21:46:30Z"
    },
    "draft_order": [
      {
        "team_id": "uuid",
        "team_name": "Team Name",
        "draft_position": 1,
        "picks_made": 3,
        "next_pick": 46
      }
    ],
    "recent_picks": [
      {
        "pick_number": 44,
        "round": 3,
        "team_id": "uuid",
        "team_name": "Team Name",
        "player_id": "uuid",
        "player_name": "Player Name",
        "position": "1B",
        "picked_at": "2024-03-01T21:43:00Z",
        "pick_time_used": 25
      }
    ]
  }
}
```

---

### Start Draft

Start a scheduled draft.

**POST** `/{draft_id}/start`

**Authentication Required - Commissioner Only**

#### Response

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "uuid",
      "status": "in_progress",
      "started_at": "2024-03-01T20:00:00Z",
      "current_pick": 1,
      "current_round": 1
    },
    "first_pick": {
      "team_id": "uuid",
      "team_name": "Team Name",
      "pick_deadline": "2024-03-01T20:01:30Z"
    }
  }
}
```

---

### Make Pick

Make a draft pick for the current team.

**POST** `/{draft_id}/picks`

**Authentication Required**

#### Request Body

```json
{
  "player_id": "uuid"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "pick": {
      "pick_number": 15,
      "round": 2,
      "team_id": "uuid",
      "team_name": "Team Name",
      "player_id": "uuid",
      "player_name": "Player Name",
      "position": "OF",
      "team": "LAD",
      "picked_at": "2024-03-01T20:15:00Z",
      "pick_time_used": 45
    },
    "next_pick": {
      "pick_number": 16,
      "team_id": "uuid",
      "team_name": "Next Team",
      "pick_deadline": "2024-03-01T20:16:30Z"
    },
    "roster_update": {
      "team_id": "uuid",
      "roster_spots_filled": 2,
      "roster_spots_remaining": 14,
      "positions_filled": ["1B", "OF"]
    }
  }
}
```

#### Error Codes

- `PLAYER_ALREADY_DRAFTED` - Player has been selected
- `NOT_YOUR_TURN` - Not the current picking team
- `PLAYER_NOT_FOUND` - Invalid player ID
- `DRAFT_NOT_ACTIVE` - Draft is not in progress

---

### Get Available Players

Get list of players available for drafting.

**GET** `/{draft_id}/available-players`

**Authentication Required**

#### Query Parameters

- `position` (optional): Filter by position
- `team` (optional): Filter by team
- `search` (optional): Search by player name
- `sort` (optional): Sort by (rank, name, position, team)
- `limit` (optional): Number of results (default: 50, max: 500)

#### Response

```json
{
  "success": true,
  "data": {
    "players": [
      {
        "player_id": "uuid",
        "name": "Player Name",
        "position": "1B",
        "team": "LAD",
        "sport": "mlb",
        "fantasy_rank": 25,
        "position_rank": 3,
        "adp": 27.5,
        "projection": {
          "fantasy_points": 245.5,
          "games": 150,
          "key_stats": {
            "home_runs": 30,
            "rbi": 100,
            "batting_average": 0.293
          }
        },
        "news_impact": "positive",
        "injury_status": "healthy"
      }
    ],
    "total_available": 1250,
    "filters_applied": {
      "position": "1B"
    }
  }
}
```

---

### Get Draft Board

Get complete draft board with all picks.

**GET** `/{draft_id}/board`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "draft_board": [
      {
        "round": 1,
        "picks": [
          {
            "pick_number": 1,
            "team_id": "uuid",
            "team_name": "Team Name",
            "player_id": "uuid",
            "player_name": "Player Name",
            "position": "OF",
            "team": "LAD",
            "picked_at": "2024-03-01T20:01:00Z",
            "pick_time_used": 30
          }
        ]
      }
    ],
    "summary": {
      "total_picks": 192,
      "completed_picks": 45,
      "current_round": 3,
      "estimated_completion": "2024-03-01T23:30:00Z"
    }
  }
}
```

---

### Set Auto-Pick

Configure auto-pick settings for a team.

**PUT** `/{draft_id}/teams/{team_id}/auto-pick`

**Authentication Required**

#### Request Body

```json
{
  "enabled": true,
  "queue": [
    {
      "player_id": "uuid",
      "priority": 1
    },
    {
      "player_id": "uuid",
      "priority": 2
    }
  ],
  "position_preferences": ["1B", "OF", "3B"],
  "auto_pick_strategy": "best_available|position_need|queue_only"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "auto_pick_settings": {
      "enabled": true,
      "queue_size": 10,
      "strategy": "best_available",
      "position_preferences": ["1B", "OF", "3B"],
      "updated_at": "2024-03-01T20:00:00Z"
    }
  }
}
```

---

### Get Team Roster

Get current roster for a team in the draft.

**GET** `/{draft_id}/teams/{team_id}/roster`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "team": {
      "id": "uuid",
      "name": "Team Name",
      "draft_position": 3,
      "picks_made": 8,
      "next_pick": 45
    },
    "roster": [
      {
        "player_id": "uuid",
        "name": "Player Name",
        "position": "1B",
        "team": "LAD",
        "pick_number": 3,
        "round": 1,
        "roster_slot": "1B"
      }
    ],
    "roster_analysis": {
      "positions_filled": {
        "C": 1,
        "1B": 1,
        "2B": 1,
        "3B": 0,
        "SS": 1,
        "OF": 3,
        "UTIL": 0,
        "SP": 1,
        "RP": 0,
        "BENCH": 0
      },
      "positions_needed": ["3B", "RP"],
      "projected_points": 1850.5
    }
  }
}
```

---

### Pause Draft

Pause an active draft (commissioner only).

**POST** `/{draft_id}/pause`

**Authentication Required - Commissioner Only**

#### Request Body

```json
{
  "reason": "Break for dinner",
  "resume_at": "2024-03-01T21:00:00Z"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "uuid",
      "status": "paused",
      "paused_at": "2024-03-01T20:30:00Z",
      "pause_reason": "Break for dinner",
      "scheduled_resume": "2024-03-01T21:00:00Z"
    }
  }
}
```

---

### Resume Draft

Resume a paused draft (commissioner only).

**POST** `/{draft_id}/resume`

**Authentication Required - Commissioner Only**

#### Response

```json
{
  "success": true,
  "data": {
    "draft": {
      "id": "uuid",
      "status": "in_progress",
      "resumed_at": "2024-03-01T21:00:00Z",
      "current_pick": 45,
      "pick_deadline": "2024-03-01T21:01:30Z"
    }
  }
}
```

---

### Get Draft History

Get historical draft data for analysis.

**GET** `/{draft_id}/history`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "draft_summary": {
      "id": "uuid",
      "completed_at": "2024-03-01T23:45:00Z",
      "total_duration": "3:45:00",
      "total_picks": 192,
      "average_pick_time": 52
    },
    "team_summaries": [
      {
        "team_id": "uuid",
        "team_name": "Team Name",
        "draft_position": 1,
        "total_pick_time": "42:30",
        "average_pick_time": 45,
        "auto_picks": 2,
        "projected_points": 1950.5,
        "draft_grade": "B+"
      }
    ],
    "notable_picks": [
      {
        "pick_number": 15,
        "player_name": "Player Name",
        "adp": 45.2,
        "pick_value": "Excellent",
        "reason": "Drafted 30 picks ahead of ADP"
      }
    ]
  }
}
```

## Real-time Updates

### WebSocket Connection

Connect to real-time draft updates:

```
/ws/drafts/{draft_id}
```

#### Message Types

```json
{
  "type": "pick_made",
  "data": {
    "pick": {
      "pick_number": 15,
      "player_name": "Player Name",
      "team_name": "Team Name"
    },
    "next_pick": {
      "team_name": "Next Team",
      "time_remaining": 90
    }
  }
}
```

```json
{
  "type": "timer_update",
  "data": {
    "time_remaining": 45,
    "auto_pick_in": 75
  }
}
```

```json
{
  "type": "draft_paused",
  "data": {
    "reason": "Technical issue",
    "estimated_resume": "2024-03-01T21:00:00Z"
  }
}
```

## Draft States

### Scheduled
- Draft created but not started
- Teams can modify auto-pick settings
- Commissioner can adjust settings

### In Progress
- Active drafting with timer
- Real-time pick updates
- Auto-pick functionality active

### Paused
- Timer stopped, picks suspended
- Settings can be modified
- Resume capability available

### Completed
- All picks made
- Final rosters set
- Historical data available

## Auto-Pick Strategies

### Best Available
- Selects highest-ranked available player
- Considers position scarcity
- Uses expert rankings and projections

### Position Need
- Prioritizes unfilled roster positions
- Balances roster construction
- Considers position depth

### Queue Only
- Only picks from user's custom queue
- Skips turn if queue is empty
- Most user control over selections