# Leagues API

## Overview

The Leagues API provides comprehensive league management functionality including creation, membership, settings, and administrative operations for fantasy sports leagues.

## Base URL

```
/api/v1/leagues
```

## Endpoints

### Create League

Create a new fantasy league.

**POST** `/`

**Authentication Required**

#### Request Body

```json
{
  "name": "string",
  "sport": "mlb|nfl|nba|nhl",
  "league_type": "standard|keeper|dynasty",
  "season": "2024",
  "max_teams": 12,
  "custom_settings": {
    "draft_type": "snake|auction",
    "scoring_system": "standard|ppr|half_ppr",
    "playoff_teams": 6,
    "trade_deadline": "2024-08-31",
    "waiver_type": "faab|rolling|priority"
  }
}
```

#### Validation Rules

- `name`: 1-100 characters
- `sport`: Must be one of: mlb, nfl, nba, nhl
- `league_type`: Must be one of: standard, keeper, dynasty
- `max_teams`: 4-20 teams
- `season`: Valid year string

#### Response

```json
{
  "success": true,
  "data": {
    "league": {
      "id": "uuid",
      "name": "string",
      "sport": "mlb",
      "league_type": "standard",
      "season": "2024",
      "status": "setup",
      "max_teams": 12,
      "current_teams": 1,
      "commissioner_id": "uuid",
      "invite_code": "ABC123",
      "created_at": "2024-01-01T00:00:00Z",
      "settings": {
        "draft_type": "snake",
        "scoring_system": "standard",
        "playoff_teams": 6
      }
    }
  }
}
```

#### Error Codes

- `LEAGUE_VALIDATION_ERROR` - Invalid league configuration
- `VALIDATION_ERROR` - Invalid input data

---

### Get League

Get detailed league information.

**GET** `/{league_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "league": {
      "id": "uuid",
      "name": "string",
      "sport": "mlb",
      "league_type": "standard",
      "season": "2024",
      "status": "active|setup|completed|paused",
      "max_teams": 12,
      "current_teams": 10,
      "commissioner_id": "uuid",
      "invite_code": "ABC123",
      "created_at": "2024-01-01T00:00:00Z",
      "draft_date": "2024-03-01T20:00:00Z",
      "settings": {
        "draft_type": "snake",
        "scoring_system": "standard",
        "playoff_teams": 6,
        "trade_deadline": "2024-08-31",
        "waiver_type": "faab"
      }
    },
    "teams": [
      {
        "id": "uuid",
        "name": "Team Name",
        "owner_id": "uuid",
        "owner_name": "User Name",
        "draft_position": 1,
        "wins": 8,
        "losses": 4,
        "ties": 0,
        "points_for": 1250.5,
        "points_against": 1180.2
      }
    ],
    "user_role": "commissioner|member|viewer"
  }
}
```

#### Error Codes

- `LEAGUE_NOT_FOUND` - League doesn't exist
- `INSUFFICIENT_PERMISSIONS` - User not authorized to view league

---

### Update League

Update league settings (commissioner only).

**PUT** `/{league_id}`

**Authentication Required - Commissioner Only**

#### Request Body

```json
{
  "name": "string",
  "draft_date": "2024-03-01T20:00:00Z",
  "settings": {
    "scoring_system": "ppr",
    "playoff_teams": 8,
    "trade_deadline": "2024-08-31"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "league": {
      "id": "uuid",
      "name": "Updated League Name",
      "draft_date": "2024-03-01T20:00:00Z",
      "settings": {
        "scoring_system": "ppr",
        "playoff_teams": 8
      },
      "updated_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

#### Error Codes

- `COMMISSIONER_ONLY` - Only commissioner can update league
- `LEAGUE_VALIDATION_ERROR` - Invalid settings for league state

---

### Join League

Join a league using invite code.

**POST** `/{league_id}/join`

**Authentication Required**

#### Request Body

```json
{
  "invite_code": "ABC123",
  "team_name": "My Fantasy Team"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "team": {
      "id": "uuid",
      "league_id": "uuid",
      "name": "My Fantasy Team",
      "owner_id": "uuid",
      "draft_position": null,
      "joined_at": "2024-01-01T00:00:00Z"
    },
    "league": {
      "id": "uuid",
      "name": "League Name",
      "current_teams": 11,
      "max_teams": 12
    }
  }
}
```

#### Error Codes

- `INVALID_INVITE_CODE` - Invite code is incorrect
- `LEAGUE_FULL` - League has reached maximum teams
- `ALREADY_IN_LEAGUE` - User already has a team in this league
- `LEAGUE_NOT_FOUND` - League doesn't exist

---

### Leave League

Leave a league (remove team).

**DELETE** `/{league_id}/teams/{team_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "message": "Successfully left league"
  }
}
```

#### Error Codes

- `TEAM_NOT_FOUND` - Team doesn't exist
- `INSUFFICIENT_PERMISSIONS` - Cannot remove team
- `DRAFT_IN_PROGRESS` - Cannot leave during active draft

---

### Get User Leagues

Get all leagues for the authenticated user.

**GET** `/my-leagues`

**Authentication Required**

#### Query Parameters

- `status` (optional): Filter by league status
- `sport` (optional): Filter by sport
- `season` (optional): Filter by season

#### Response

```json
{
  "success": true,
  "data": {
    "leagues": [
      {
        "id": "uuid",
        "name": "League Name",
        "sport": "mlb",
        "season": "2024",
        "status": "active",
        "user_role": "commissioner",
        "team": {
          "id": "uuid",
          "name": "Team Name",
          "wins": 8,
          "losses": 4,
          "rank": 2
        },
        "next_matchup": {
          "week": 13,
          "opponent": "Opponent Team",
          "starts_at": "2024-01-15T00:00:00Z"
        }
      }
    ],
    "total": 5,
    "active": 3,
    "completed": 2
  }
}
```

---

### Invite Users

Send league invitations (commissioner only).

**POST** `/{league_id}/invites`

**Authentication Required - Commissioner Only**

#### Request Body

```json
{
  "emails": ["user1@example.com", "user2@example.com"],
  "message": "Join my fantasy league!"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "invites_sent": 2,
    "failed_invites": [],
    "invite_code": "ABC123"
  }
}
```

---

### Get League Standings

Get current league standings.

**GET** `/{league_id}/standings`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "standings": [
      {
        "rank": 1,
        "team": {
          "id": "uuid",
          "name": "Team Name",
          "owner_name": "Owner Name"
        },
        "record": {
          "wins": 10,
          "losses": 2,
          "ties": 0,
          "win_percentage": 0.833
        },
        "scoring": {
          "points_for": 1450.5,
          "points_against": 1280.2,
          "avg_points": 120.9
        },
        "streak": {
          "type": "W",
          "length": 3
        }
      }
    ],
    "playoff_cutoff": 6,
    "season_stats": {
      "weeks_completed": 12,
      "total_weeks": 17
    }
  }
}
```

---

### Get League Activity

Get recent league activity feed.

**GET** `/{league_id}/activity`

**Authentication Required**

#### Query Parameters

- `limit` (optional): Number of activities to return (default: 20, max: 100)
- `offset` (optional): Pagination offset
- `types` (optional): Filter by activity types (comma-separated)

#### Response

```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": "uuid",
        "type": "trade_completed",
        "title": "Trade Completed",
        "description": "Team A traded Player X for Player Y",
        "participants": ["team_a", "team_b"],
        "timestamp": "2024-01-01T12:00:00Z",
        "metadata": {
          "trade_id": "uuid",
          "players_involved": ["player_x", "player_y"]
        }
      }
    ],
    "total": 150,
    "has_more": true
  }
}
```

## League States

### Setup Phase
- Commissioner can modify all settings
- Teams can join using invite code
- Draft can be scheduled
- No gameplay features active

### Active Phase
- Draft completed, season in progress
- Weekly matchups and scoring
- Trades and waiver claims active
- Limited setting changes allowed

### Completed Phase
- Season finished, final standings set
- Historical data preserved
- No active gameplay
- Preparation for next season available

## Permission Levels

### Commissioner
- Full league management access
- Modify settings and rules
- Manage teams and users
- Force trades and lineup changes
- Access to admin tools

### Team Owner
- Manage own team and lineup
- Propose trades
- Submit waiver claims
- Participate in draft
- View league information

### Viewer
- Read-only access to public league information
- Cannot participate in gameplay
- Limited to standings and basic stats