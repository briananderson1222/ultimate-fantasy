# Trades API

## Overview

The Trades API provides comprehensive trade management functionality including trade proposals, evaluation, negotiation, and execution for fantasy sports leagues.

## Base URL

```
/api/v1/trades
```

## Trade States

- **Proposed** - Initial trade offer sent
- **Counter** - Counter-offer made
- **Accepted** - Agreed to by both parties
- **Completed** - Successfully processed
- **Rejected** - Declined by recipient
- **Expired** - Deadline passed without action
- **Vetoed** - Blocked by league vote/commissioner

## Endpoints

### Create Trade Proposal

Create a new trade proposal.

**POST** `/`

**Authentication Required**

#### Request Body

```json
{
  "recipient_team_id": "uuid",
  "offering_players": [
    {
      "player_id": "uuid",
      "player_name": "Player A"
    }
  ],
  "requesting_players": [
    {
      "player_id": "uuid",
      "player_name": "Player B"
    }
  ],
  "message": "Interested in trading for your outfielder",
  "expires_at": "2024-06-15T23:59:59Z"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "league_id": "uuid",
      "proposer_team_id": "uuid",
      "recipient_team_id": "uuid",
      "status": "proposed",
      "created_at": "2024-06-10T14:00:00Z",
      "expires_at": "2024-06-15T23:59:59Z",
      "offering_players": [
        {
          "player_id": "uuid",
          "player_name": "Player A",
          "position": "OF",
          "team": "LAD"
        }
      ],
      "requesting_players": [
        {
          "player_id": "uuid",
          "player_name": "Player B",
          "position": "1B",
          "team": "NYY"
        }
      ],
      "message": "Interested in trading for your outfielder"
    },
    "trade_analysis": {
      "fairness_rating": "fair",
      "value_difference": 2.5,
      "confidence": 0.78,
      "summary": "Slight value advantage to proposing team"
    }
  }
}
```

#### Error Codes

- `PLAYER_NOT_ON_ROSTER` - Player not owned by proposing team
- `TRADE_WITH_SELF` - Cannot trade with own team
- `TRADE_DEADLINE_PASSED` - League trade deadline has passed
- `PLAYER_RECENTLY_TRADED` - Player in cooldown period

---

### Get Trade Details

Get detailed information about a specific trade.

**GET** `/{trade_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "league_id": "uuid",
      "proposer_team": {
        "id": "uuid",
        "name": "Team A",
        "owner_name": "Owner A"
      },
      "recipient_team": {
        "id": "uuid",
        "name": "Team B",
        "owner_name": "Owner B"
      },
      "status": "proposed",
      "created_at": "2024-06-10T14:00:00Z",
      "expires_at": "2024-06-15T23:59:59Z",
      "last_action_at": "2024-06-10T14:00:00Z",
      "offering_players": [
        {
          "player_id": "uuid",
          "player_name": "Player A",
          "position": "OF",
          "team": "LAD",
          "season_stats": {
            "fantasy_points": 185.5,
            "games": 75,
            "home_runs": 15,
            "rbi": 48
          },
          "recent_form": "hot",
          "injury_status": "healthy"
        }
      ],
      "requesting_players": [
        {
          "player_id": "uuid",
          "player_name": "Player B",
          "position": "1B",
          "team": "NYY",
          "season_stats": {
            "fantasy_points": 195.2,
            "games": 78,
            "home_runs": 18,
            "rbi": 52
          },
          "recent_form": "average",
          "injury_status": "healthy"
        }
      ],
      "message": "Interested in trading for your outfielder",
      "trade_history": [
        {
          "action": "proposed",
          "timestamp": "2024-06-10T14:00:00Z",
          "team": "Team A"
        }
      ]
    },
    "trade_analysis": {
      "overall_rating": "fair",
      "value_analysis": {
        "proposer_value": 185.5,
        "recipient_value": 195.2,
        "difference": -9.7,
        "percentage_difference": -5.2
      },
      "positional_impact": {
        "proposer": {
          "giving_up": "Starting OF",
          "receiving": "Starting 1B",
          "roster_impact": "Slight upgrade"
        },
        "recipient": {
          "giving_up": "Starting 1B",
          "receiving": "Starting OF",
          "roster_impact": "Slight downgrade"
        }
      },
      "ai_recommendation": {
        "for_proposer": "accept",
        "for_recipient": "consider",
        "reasoning": "Good positional fit, fair value exchange",
        "confidence": 0.75
      }
    }
  }
}
```

---

### Get Team Trades

Get all trades for a specific team.

**GET** `/teams/{team_id}`

**Authentication Required**

#### Query Parameters

- `status` (optional): Filter by trade status
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset

#### Response

```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": "uuid",
        "status": "proposed",
        "created_at": "2024-06-10T14:00:00Z",
        "expires_at": "2024-06-15T23:59:59Z",
        "role": "proposer",
        "other_team": {
          "id": "uuid",
          "name": "Team B",
          "owner_name": "Owner B"
        },
        "offering_players": ["Player A"],
        "requesting_players": ["Player B"],
        "value_summary": "Fair trade",
        "requires_action": true
      }
    ],
    "summary": {
      "total_trades": 15,
      "pending_action": 2,
      "completed_this_season": 8,
      "average_completion_time": "2.5 days"
    }
  }
}
```

---

### Accept Trade

Accept a trade proposal.

**POST** `/{trade_id}/accept`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "status": "accepted",
      "accepted_at": "2024-06-11T09:30:00Z",
      "processing_status": "pending_review"
    },
    "next_steps": {
      "review_period": "24 hours",
      "veto_threshold": "4 votes",
      "expected_completion": "2024-06-12T09:30:00Z"
    }
  }
}
```

---

### Reject Trade

Reject a trade proposal.

**POST** `/{trade_id}/reject`

**Authentication Required**

#### Request Body

```json
{
  "reason": "Not interested in this deal"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "status": "rejected",
      "rejected_at": "2024-06-11T10:00:00Z",
      "rejection_reason": "Not interested in this deal"
    }
  }
}
```

---

### Counter Trade

Make a counter-offer to a trade proposal.

**POST** `/{trade_id}/counter`

**Authentication Required**

#### Request Body

```json
{
  "offering_players": [
    {
      "player_id": "uuid",
      "player_name": "Player C"
    }
  ],
  "requesting_players": [
    {
      "player_id": "uuid",
      "player_name": "Player D"
    }
  ],
  "message": "How about this instead?",
  "expires_at": "2024-06-16T23:59:59Z"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "status": "counter",
      "countered_at": "2024-06-11T11:00:00Z",
      "counter_number": 1,
      "offering_players": [
        {
          "player_id": "uuid",
          "player_name": "Player C",
          "position": "2B",
          "team": "BOS"
        }
      ],
      "requesting_players": [
        {
          "player_id": "uuid",
          "player_name": "Player D",
          "position": "SP",
          "team": "HOU"
        }
      ],
      "message": "How about this instead?"
    },
    "trade_analysis": {
      "fairness_rating": "slightly_favors_proposer",
      "value_difference": 12.3,
      "improvement_from_original": true
    }
  }
}
```

---

### Cancel Trade

Cancel a trade proposal (proposer only).

**DELETE** `/{trade_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "trade": {
      "id": "uuid",
      "status": "cancelled",
      "cancelled_at": "2024-06-11T12:00:00Z"
    },
    "message": "Trade proposal cancelled successfully"
  }
}
```

---

### Get Trade Analysis

Get detailed AI analysis of a trade.

**GET** `/{trade_id}/analysis`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "analysis": {
      "trade_id": "uuid",
      "overall_rating": "fair",
      "confidence": 0.82,
      "value_analysis": {
        "proposer_total_value": 245.8,
        "recipient_total_value": 238.5,
        "net_difference": 7.3,
        "percentage_difference": 3.1
      },
      "player_comparisons": [
        {
          "proposer_player": {
            "name": "Player A",
            "value": 125.5,
            "ceiling": 155.0,
            "floor": 95.0,
            "consistency": 0.75
          },
          "recipient_player": {
            "name": "Player B",
            "value": 128.2,
            "ceiling": 140.0,
            "floor": 115.0,
            "consistency": 0.88
          },
          "comparison": "Recipient player safer, less upside"
        }
      ],
      "roster_impact": {
        "proposer": {
          "position_changes": {
            "OF": "weaker",
            "1B": "stronger"
          },
          "overall_impact": "slight_improvement",
          "championship_odds": "+2.5%"
        },
        "recipient": {
          "position_changes": {
            "1B": "weaker",
            "OF": "stronger"
          },
          "overall_impact": "slight_decline",
          "championship_odds": "-1.8%"
        }
      },
      "schedule_analysis": {
        "proposer_advantage_weeks": [14, 15, 16],
        "recipient_advantage_weeks": [12, 13],
        "playoff_impact": "Favors proposer"
      },
      "injury_risk": {
        "proposer_risk": "low",
        "recipient_risk": "moderate",
        "details": "Player B has minor injury history"
      },
      "ai_recommendation": {
        "for_proposer": "accept",
        "for_recipient": "consider_carefully",
        "reasoning": "Fair value with slight upside for proposer",
        "factors": [
          "Positional need addressed",
          "Playoff schedule favorable",
          "Value difference minimal"
        ]
      }
    },
    "historical_context": {
      "similar_trades": 15,
      "average_value_difference": 8.5,
      "success_rate": 0.73
    }
  }
}
```

---

### Get League Trade Activity

Get recent trade activity for the league.

**GET** `/leagues/{league_id}/activity`

**Authentication Required**

#### Query Parameters

- `limit` (optional): Number of trades to return (default: 10)
- `status` (optional): Filter by trade status

#### Response

```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": "uuid",
        "status": "completed",
        "completed_at": "2024-06-10T15:00:00Z",
        "teams": [
          {
            "name": "Team A",
            "gave": ["Player X", "Player Y"],
            "received": ["Player Z"]
          },
          {
            "name": "Team B",
            "gave": ["Player Z"],
            "received": ["Player X", "Player Y"]
          }
        ],
        "value_assessment": "Fair trade",
        "veto_votes": 0,
        "processing_time": "36 hours"
      }
    ],
    "league_stats": {
      "total_trades_this_season": 45,
      "average_trades_per_team": 3.8,
      "most_active_trader": "Team C",
      "vetoed_trades": 2,
      "trade_deadline": "2024-08-31T23:59:59Z"
    }
  }
}
```

---

### Veto Trade

Vote to veto a trade (league members only).

**POST** `/{trade_id}/veto`

**Authentication Required**

#### Request Body

```json
{
  "reason": "Unfair advantage, too lopsided"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "veto_vote": {
      "trade_id": "uuid",
      "voter_team_id": "uuid",
      "reason": "Unfair advantage, too lopsided",
      "voted_at": "2024-06-11T16:00:00Z"
    },
    "veto_status": {
      "total_votes": 3,
      "required_votes": 4,
      "time_remaining": "18 hours",
      "will_veto_if_threshold_met": true
    }
  }
}
```

## Trade Processing

### Review Period

- **Standard leagues**: 24-48 hours
- **Commissioner review**: Immediate or manual review
- **League vote**: 24-48 hours for veto voting

### Veto Conditions

- League vote threshold (typically 4+ votes)
- Commissioner discretion
- Automatic veto for obvious collusion

### Processing Timeline

1. **Accepted** - Trade agreed to by both parties
2. **Review Period** - 24-48 hour window for vetoes
3. **Processing** - Roster moves executed
4. **Completed** - Players moved to new teams

## Real-time Updates

### WebSocket Connection

Connect to real-time trade updates:

```
/ws/trades/{trade_id}
```

#### Message Types

```json
{
  "type": "trade_accepted",
  "data": {
    "trade_id": "uuid",
    "accepted_by": "Team B",
    "review_period_ends": "2024-06-12T09:30:00Z"
  }
}
```

```json
{
  "type": "veto_vote_cast",
  "data": {
    "trade_id": "uuid",
    "votes_for_veto": 3,
    "votes_needed": 4,
    "voting_ends": "2024-06-12T09:30:00Z"
  }
}
```

```json
{
  "type": "trade_completed",
  "data": {
    "trade_id": "uuid",
    "completed_at": "2024-06-12T09:30:00Z",
    "players_moved": 4
  }
}
```

## Trade Restrictions

### Deadline Restrictions

- Trade deadline: Typically August 31st
- Playoff roster locks: Varies by league
- Emergency exceptions: Commissioner discretion

### Player Restrictions

- Recently traded: 24-48 hour cooldown
- Injured players: May require approval
- Prospect eligibility: League specific rules

### Roster Limits

- Position requirements must be maintained
- Salary cap compliance (if applicable)
- Prospect limits (dynasty leagues)