# Waivers API

## Overview

The Waivers API provides comprehensive waiver wire and free agency management functionality including claims, FAAB bidding, and player pickup/drop operations for fantasy sports leagues.

## Base URL

```
/api/v1/waivers
```

## Waiver Types

- **FAAB** - Free Agent Auction Budget (bidding system)
- **Rolling** - Rolling waiver priority
- **Priority** - Fixed waiver priority order

## Endpoints

### Get Available Players

Get list of players available on waivers and free agency.

**GET** `/available`

**Authentication Required**

#### Query Parameters

- `league_id` (required): League identifier
- `position` (optional): Filter by position
- `status` (optional): waiver, free_agent, all (default: all)
- `sort` (optional): owned_percentage, projections, recent_performance
- `limit` (optional): Number of results (default: 50, max: 200)

#### Response

```json
{
  "success": true,
  "data": {
    "players": [
      {
        "player_id": "uuid",
        "name": "Available Player",
        "position": "OF",
        "team": "MIA",
        "status": "waiver",
        "waiver_status": {
          "type": "waiver",
          "clears_at": "2024-06-12T09:00:00Z",
          "priority_required": 3,
          "current_bids": 2
        },
        "ownership": {
          "league_percentage": 65.5,
          "global_percentage": 42.3,
          "trending": "up"
        },
        "performance": {
          "last_7_days": {
            "fantasy_points": 25.8,
            "games": 4,
            "avg_per_game": 6.45
          },
          "season_projection": 180.5,
          "recent_form": "hot"
        },
        "next_games": [
          {
            "date": "2024-06-12",
            "opponent": "WAS",
            "home_away": "home",
            "matchup_rating": "excellent"
          }
        ],
        "pickup_recommendation": {
          "priority": "high",
          "suggested_faab": 25,
          "roster_percentage": 18.5
        }
      }
    ],
    "summary": {
      "total_available": 420,
      "on_waivers": 180,
      "free_agents": 240,
      "trending_up": 35,
      "trending_down": 22
    }
  }
}
```

---

### Submit Waiver Claim

Submit a waiver claim for a player.

**POST** `/claims`

**Authentication Required**

#### Request Body

```json
{
  "league_id": "uuid",
  "player_id": "uuid",
  "claim_type": "add|add_drop",
  "drop_player_id": "uuid",
  "bid_amount": 25,
  "priority": 1
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "claim": {
      "id": "uuid",
      "league_id": "uuid",
      "team_id": "uuid",
      "player_id": "uuid",
      "player_name": "Claimed Player",
      "claim_type": "add_drop",
      "drop_player_id": "uuid",
      "drop_player_name": "Dropped Player",
      "bid_amount": 25,
      "priority": 1,
      "submitted_at": "2024-06-11T14:30:00Z",
      "processes_at": "2024-06-12T09:00:00Z",
      "status": "pending"
    },
    "waiver_info": {
      "current_budget": 175,
      "remaining_after_claim": 150,
      "position_in_queue": 3,
      "estimated_success_chance": 0.65
    }
  }
}
```

#### Error Codes

- `INSUFFICIENT_FAAB` - Not enough budget for bid
- `PLAYER_NOT_AVAILABLE` - Player not on waivers
- `ROSTER_FULL` - Must drop a player first
- `INVALID_DROP_PLAYER` - Cannot drop specified player

---

### Get Team Claims

Get all waiver claims for a team.

**GET** `/teams/{team_id}/claims`

**Authentication Required**

#### Query Parameters

- `status` (optional): pending, successful, failed, cancelled
- `week` (optional): Filter by specific week
- `limit` (optional): Number of results (default: 20)

#### Response

```json
{
  "success": true,
  "data": {
    "claims": [
      {
        "id": "uuid",
        "player_name": "Claimed Player",
        "position": "OF",
        "team": "MIA",
        "claim_type": "add_drop",
        "drop_player_name": "Dropped Player",
        "bid_amount": 25,
        "priority": 1,
        "status": "pending",
        "submitted_at": "2024-06-11T14:30:00Z",
        "processes_at": "2024-06-12T09:00:00Z",
        "success_probability": 0.65
      }
    ],
    "summary": {
      "total_claims": 15,
      "pending": 3,
      "successful": 8,
      "failed": 4,
      "total_faab_spent": 145
    },
    "budget_info": {
      "starting_budget": 200,
      "current_budget": 175,
      "pending_bids": 50,
      "available_budget": 125
    }
  }
}
```

---

### Update Waiver Claim

Update or modify a pending waiver claim.

**PUT** `/claims/{claim_id}`

**Authentication Required**

#### Request Body

```json
{
  "bid_amount": 30,
  "priority": 2,
  "drop_player_id": "uuid"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "claim": {
      "id": "uuid",
      "bid_amount": 30,
      "priority": 2,
      "drop_player_name": "New Drop Player",
      "updated_at": "2024-06-11T16:00:00Z",
      "processes_at": "2024-06-12T09:00:00Z"
    },
    "impact": {
      "success_probability": 0.75,
      "budget_remaining": 145
    }
  }
}
```

---

### Cancel Waiver Claim

Cancel a pending waiver claim.

**DELETE** `/claims/{claim_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "claim": {
      "id": "uuid",
      "status": "cancelled",
      "cancelled_at": "2024-06-11T17:00:00Z"
    },
    "budget_freed": 25
  }
}
```

---

### Add Free Agent

Immediately add a free agent player.

**POST** `/free-agents/add`

**Authentication Required**

#### Request Body

```json
{
  "league_id": "uuid",
  "player_id": "uuid",
  "drop_player_id": "uuid"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "transaction": {
      "id": "uuid",
      "type": "free_agent_pickup",
      "team_id": "uuid",
      "added_player": {
        "player_id": "uuid",
        "name": "Free Agent",
        "position": "RP",
        "team": "TEX"
      },
      "dropped_player": {
        "player_id": "uuid",
        "name": "Dropped Player",
        "position": "RP",
        "team": "KC"
      },
      "processed_at": "2024-06-11T18:00:00Z"
    },
    "roster_update": {
      "roster_size": 16,
      "faab_remaining": 175
    }
  }
}
```

---

### Get Waiver Results

Get results from processed waiver claims.

**GET** `/results`

**Authentication Required**

#### Query Parameters

- `league_id` (required): League identifier
- `week` (optional): Specific week (default: current)
- `date` (optional): Specific date (YYYY-MM-DD)

#### Response

```json
{
  "success": true,
  "data": {
    "waiver_results": {
      "processed_at": "2024-06-12T09:00:00Z",
      "week": 12,
      "total_claims": 25,
      "successful_claims": 18,
      "failed_claims": 7
    },
    "claims": [
      {
        "team_name": "Team A",
        "player_added": "Hot Pickup",
        "player_dropped": "Cold Player",
        "bid_amount": 35,
        "success": true,
        "priority_used": 1
      },
      {
        "team_name": "Team B",
        "player_targeted": "Hot Pickup",
        "bid_amount": 28,
        "success": false,
        "reason": "outbid"
      }
    ],
    "notable_pickups": [
      {
        "player_name": "Breakout Star",
        "winning_bid": 45,
        "league_high": true,
        "previous_owner": null,
        "ownership_change": "+65%"
      }
    ]
  }
}
```

---

### Get Waiver Wire Trends

Get trending players and waiver wire activity.

**GET** `/trends`

**Authentication Required**

#### Query Parameters

- `league_id` (optional): Specific league analysis
- `timeframe` (optional): week, month (default: week)
- `position` (optional): Filter by position

#### Response

```json
{
  "success": true,
  "data": {
    "trending_up": [
      {
        "player_id": "uuid",
        "name": "Rising Star",
        "position": "OF",
        "team": "SD",
        "ownership_change": "+35%",
        "add_percentage": 78.5,
        "reason": "Hot streak, 5 HR in last week",
        "suggested_faab": "15-25%"
      }
    ],
    "trending_down": [
      {
        "player_id": "uuid",
        "name": "Struggling Vet",
        "position": "1B",
        "team": "CWS",
        "ownership_change": "-22%",
        "drop_percentage": 45.2,
        "reason": "Injured, struggling performance"
      }
    ],
    "hot_pickups": [
      {
        "player_name": "Rookie Sensation",
        "position": "SP",
        "average_faab": 28.5,
        "pickup_rate": 89.3,
        "leagues_available": 12
      }
    ],
    "injury_replacements": [
      {
        "injured_player": "Star Player",
        "replacement_options": [
          {
            "player_name": "Backup Option",
            "role": "Handcuff",
            "ownership": 25.5,
            "projected_value": "High if starter injured"
          }
        ]
      }
    ]
  }
}
```

---

### Get Team Waiver Priority

Get current waiver priority order for the league.

**GET** `/priority`

**Authentication Required**

#### Query Parameters

- `league_id` (required): League identifier

#### Response

```json
{
  "success": true,
  "data": {
    "waiver_type": "rolling",
    "priority_order": [
      {
        "priority": 1,
        "team_id": "uuid",
        "team_name": "Last Place Team",
        "owner_name": "Owner Name",
        "record": "4-8",
        "last_claim": "2024-06-05T09:00:00Z"
      }
    ],
    "your_team": {
      "priority": 5,
      "next_claim_priority": 6,
      "claims_this_week": 1,
      "successful_claims": 8
    },
    "next_waiver_period": {
      "processes_at": "2024-06-13T09:00:00Z",
      "claims_submitted": 12,
      "deadline": "2024-06-12T23:59:59Z"
    }
  }
}
```

---

### Get FAAB Standings

Get FAAB budget standings for the league.

**GET** `/faab-standings`

**Authentication Required**

#### Query Parameters

- `league_id` (required): League identifier

#### Response

```json
{
  "success": true,
  "data": {
    "faab_standings": [
      {
        "rank": 1,
        "team_id": "uuid",
        "team_name": "Conservative Spender",
        "remaining_budget": 175,
        "spent": 25,
        "percentage_remaining": 87.5,
        "successful_claims": 3,
        "average_bid": 8.3
      }
    ],
    "league_averages": {
      "remaining_budget": 142.5,
      "spent": 57.5,
      "successful_claims": 4.8,
      "total_transactions": 156
    },
    "your_team": {
      "remaining_budget": 125,
      "rank": 8,
      "pending_bids": 35,
      "biggest_purchase": {
        "player_name": "Expensive Pickup",
        "amount": 40
      }
    }
  }
}
```

## Waiver Processing

### Processing Schedule

- **Standard Processing**: Wednesday 9:00 AM ET
- **Weekend Processing**: Sunday 9:00 AM ET
- **Daily Processing**: Available in some leagues

### Claim Resolution Order

1. **FAAB Leagues**: Highest bid wins
2. **Priority Leagues**: Waiver order determines winner
3. **Ties**: Earlier submission time wins

### Budget Management

- Starting budget: Typically $100-$200
- Minimum bid: Usually $1
- Budget carries over: Season-long resource

## Real-time Updates

### WebSocket Connection

Connect to real-time waiver updates:

```
/ws/waivers/{league_id}
```

#### Message Types

```json
{
  "type": "claim_submitted",
  "data": {
    "player_name": "Hot Pickup",
    "team_name": "Bidding Team",
    "total_claims": 8
  }
}
```

```json
{
  "type": "waiver_deadline_warning",
  "data": {
    "minutes_remaining": 30,
    "pending_claims": 3
  }
}
```

```json
{
  "type": "waivers_processed",
  "data": {
    "processed_at": "2024-06-12T09:00:00Z",
    "your_successful_claims": 2,
    "your_failed_claims": 1
  }
}
```

## Best Practices

### FAAB Strategy

- **Early Season**: Aggressive bidding for breakouts
- **Mid Season**: Target specific needs
- **Late Season**: Save for playoffs/injuries

### Priority Management

- **High Priority**: Use on high-value adds
- **Low Priority**: Stream defenses/kickers
- **Planning**: Consider upcoming schedule

### Roster Management

- **Drop Candidates**: Injured, bye weeks, poor matchups
- **Handcuffs**: Backup for star players
- **Streaming**: Week-to-week matchup plays