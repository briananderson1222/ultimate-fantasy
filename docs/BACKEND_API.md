# Ultimate Fantasy Platform - Backend API Documentation

This document provides comprehensive documentation of the Ultimate Fantasy backend API, including all endpoints, data models, and integration details.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Core Resources](#core-resources)
- [League Management](#league-management)
- [Team Management](#team-management)
- [Player Management](#player-management)
- [Draft Management](#draft-management)
- [Lineup Management](#lineup-management)
- [Trading System](#trading-system)
- [Waiver System](#waiver-system)
- [Scoring System](#scoring-system)
- [User Management](#user-management)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Webhooks](#webhooks)

## API Overview

### Base URL

```
https://api.ultimatefantasy.com/v1
```

### Authentication

All API requests require authentication using JWT tokens:

```
Authorization: Bearer <your_jwt_token>
```

### Response Format

All responses follow a consistent format:

```json
{
  "data": { ... },
  "message": "Success message",
  "status": "success"
}
```

### Error Format

```json
{
  "error": "Error message",
  "status": "error",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

## Authentication

### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "fantasy_guru",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**

```json
{
  "data": {
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "username": "fantasy_guru",
      "first_name": "John",
      "last_name": "Doe",
      "verified": false
    }
  },
  "status": "success"
}
```

### Login User

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

### Logout User

```http
POST /auth/logout
```

## Core Resources

### Get Current User

```http
GET /users/me
```

**Response:**

```json
{
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "fantasy_guru",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://...",
    "verified": true,
    "preferences": {
      "theme": "dark",
      "notifications": {
        "email": true,
        "push": true,
        "trades": true,
        "waivers": false
      }
    }
  },
  "status": "success"
}
```

### Update User Preferences

```http
PATCH /users/me/preferences
Content-Type: application/json

{
  "theme": "light",
  "notifications": {
    "waivers": true
  }
}
```

## League Management

### List User's Leagues

```http
GET /leagues
```

**Query Parameters:**

- `sport`: Filter by sport (mlb, wnba, nfl)
- `status`: Filter by status (setup, drafting, active, completed)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:**

```json
{
  "data": [
    {
      "id": "league_id",
      "name": "Fantasy Baseball League 2024",
      "sport": "mlb",
      "league_type": "traditional",
      "settings": {
        "max_teams": 12,
        "scoring_type": "points",
        "roster_size": 25,
        "playoff_teams": 6
      },
      "status": "active",
      "commissioner_id": "user_id",
      "member_count": 12,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  },
  "status": "success"
}
```

### Create League

```http
POST /leagues
Content-Type: application/json

{
  "name": "My Fantasy League",
  "sport": "mlb",
  "league_type": "traditional",
  "settings": {
    "max_teams": 10,
    "scoring_type": "categories",
    "roster_size": 25,
    "playoff_teams": 4,
    "waiver_type": "faab",
    "trade_deadline": "2024-08-01T00:00:00Z"
  },
  "invite_emails": ["friend1@example.com", "friend2@example.com"]
}
```

### Get League Details

```http
GET /leagues/{league_id}
```

**Response:**

```json
{
  "data": {
    "id": "league_id",
    "name": "Fantasy Baseball League 2024",
    "sport": "mlb",
    "league_type": "traditional",
    "settings": {
      "max_teams": 12,
      "scoring_type": "points",
      "roster_size": 25,
      "playoff_teams": 6,
      "waiver_type": "faab",
      "trade_deadline": "2024-08-01T00:00:00Z",
      "draft_settings": {
        "draft_type": "snake",
        "pick_timer_seconds": 90,
        "draft_date": "2024-03-15T19:00:00Z"
      }
    },
    "status": "active",
    "commissioner_id": "user_id",
    "members": [
      {
        "user_id": "user1_id",
        "username": "fantasy_guru",
        "team_name": "Home Run Heroes",
        "role": "commissioner"
      }
    ],
    "standings": [
      {
        "team_id": "team1_id",
        "team_name": "Home Run Heroes",
        "wins": 8,
        "losses": 2,
        "ties": 0,
        "points_for": 1250.5,
        "points_against": 1180.2,
        "playoff_odds": 0.95
      }
    ]
  },
  "status": "success"
}
```

### Update League Settings

```http
PATCH /leagues/{league_id}
Content-Type: application/json

{
  "settings": {
    "trade_deadline": "2024-07-15T00:00:00Z",
    "waiver_type": "rolling"
  }
}
```

### Delete League

```http
DELETE /leagues/{league_id}
```

## Team Management

### Get Team Details

```http
GET /teams/{team_id}
```

**Response:**

```json
{
  "data": {
    "id": "team_id",
    "league_id": "league_id",
    "user_id": "user_id",
    "name": "Home Run Heroes",
    "wins": 8,
    "losses": 2,
    "ties": 0,
    "points_for": 1250.5,
    "points_against": 1180.2,
    "waiver_priority": 3,
    "budget": 87,
    "roster": [
      {
        "player_id": "player1_id",
        "name": "Mike Trout",
        "position": "OF",
        "team": "LAA",
        "projected_points": 45.2,
        "actual_points": 42.1
      }
    ],
    "taxi_squad": [],
    "injured_reserve": []
  },
  "status": "success"
}
```

### Update Team Settings

```http
PATCH /teams/{team_id}
Content-Type: application/json

{
  "name": "New Team Name",
  "logo_url": "https://..."
}
```

## Player Management

### Search Players

```http
GET /players
```

**Query Parameters:**

- `query`: Search term for player name
- `sport`: Filter by sport (mlb, wnba, nfl)
- `position`: Filter by position
- `team`: Filter by team
- `available_only`: Only show available players
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**

```json
{
  "data": [
    {
      "id": "player_id",
      "external_id": "mlb_545361",
      "name": "Mike Trout",
      "position": "OF",
      "team": "LAA",
      "injury_status": "healthy",
      "projected_points": 45.2,
      "season_stats": {
        "r": 12,
        "hr": 5,
        "rbi": 15,
        "sb": 2,
        "avg": 0.312
      },
      "game_stats": {
        "r": 1,
        "hr": 0,
        "rbi": 0,
        "sb": 0,
        "avg": 0.25
      },
      "ownership": {
        "owned": true,
        "owned_by": "team_id",
        "percent_owned": 95.2,
        "percent_started": 89.1
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1200,
    "total_pages": 24
  },
  "status": "success"
}
```

### Get Player Details

```http
GET /players/{player_id}
```

**Response:**

```json
{
  "data": {
    "id": "player_id",
    "external_id": "mlb_545361",
    "name": "Mike Trout",
    "position": "OF",
    "team": "LAA",
    "injury_status": "healthy",
    "projected_points": 45.2,
    "season_stats": {
      "r": 12,
      "hr": 5,
      "rbi": 15,
      "sb": 2,
      "avg": 0.312
    },
    "recent_games": [
      {
        "date": "2024-04-15",
        "opponent": "BOS",
        "stats": {
          "r": 1,
          "hr": 0,
          "rbi": 0,
          "sb": 0,
          "avg": 0.25
        }
      }
    ],
    "projections": {
      "week": {
        "points": 28.5,
        "confidence": 0.85
      },
      "season": {
        "points": 450.2,
        "confidence": 0.72
      }
    }
  },
  "status": "success"
}
```

## Draft Management

### Get Draft Status

```http
GET /drafts/{league_id}
```

**Response:**

```json
{
  "data": {
    "id": "draft_id",
    "league_id": "league_id",
    "status": "in_progress",
    "current_pick": 45,
    "current_team_id": "team_id",
    "picks": [
      {
        "pick_number": 1,
        "team_id": "team1_id",
        "player_id": "player1_id",
        "timestamp": "2024-03-15T19:05:00Z"
      }
    ],
    "timer_seconds": 90,
    "started_at": "2024-03-15T19:00:00Z",
    "available_players": 1155
  },
  "status": "success"
}
```

### Make Draft Pick

```http
POST /drafts/{league_id}/picks
Content-Type: application/json

{
  "player_id": "player_id",
  "team_id": "team_id"
}
```

**Response:**

```json
{
  "data": {
    "pick_number": 45,
    "team_id": "team_id",
    "player_id": "player_id",
    "timestamp": "2024-03-15T19:32:15Z"
  },
  "status": "success"
}
```

### Get Draft Board

```http
GET /drafts/{league_id}/board
```

**Response:**

```json
{
  "data": {
    "draft_order": [
      {
        "round": 1,
        "pick": 1,
        "team_id": "team1_id",
        "team_name": "Team 1",
        "player_id": "player1_id",
        "player_name": "Mike Trout",
        "timestamp": "2024-03-15T19:05:00Z"
      }
    ],
    "available_players": [
      {
        "player_id": "player2_id",
        "name": "Shohei Ohtani",
        "position": "SP",
        "team": "LAD",
        "projected_points": 52.1,
        "adp": 2.1
      }
    ],
    "draft_trends": {
      "position_runs": {
        "SP": 3,
        "OF": 2
      },
      "team_stacks": {
        "LAD": 2,
        "ATL": 3
      }
    }
  },
  "status": "success"
}
```

## Lineup Management

### Get Lineup

```http
GET /lineups/{team_id}
```

**Query Parameters:**

- `week`: Week number (default: current week)

**Response:**

```json
{
  "data": {
    "id": "lineup_id",
    "team_id": "team_id",
    "week": 15,
    "players": [
      {
        "position": "C",
        "player_id": "player1_id",
        "player_name": "Mike Trout",
        "is_flex": false
      },
      {
        "position": "1B",
        "player_id": "player2_id",
        "player_name": "Freddie Freeman",
        "is_flex": false
      }
    ],
    "projected_points": 42.5,
    "actual_points": 38.2,
    "locked": false,
    "version": 3,
    "updated_at": "2024-04-15T14:30:00Z"
  },
  "status": "success"
}
```

### Update Lineup

```http
POST /lineups/{team_id}
Content-Type: application/json

{
  "week": 15,
  "players": [
    {
      "position": "C",
      "player_id": "player1_id"
    },
    {
      "position": "UTIL",
      "player_id": "player2_id"
    }
  ]
}
```

### Get Lineup History

```http
GET /lineups/{team_id}/history
```

**Query Parameters:**

- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)

## Trading System

### List Trade Proposals

```http
GET /trades
```

**Query Parameters:**

- `league_id`: Filter by league
- `status`: Filter by status (pending, accepted, rejected, expired)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:**

```json
{
  "data": [
    {
      "id": "trade_id",
      "league_id": "league_id",
      "proposing_team_id": "team1_id",
      "receiving_team_id": "team2_id",
      "proposed_players": ["player1_id", "player2_id"],
      "requested_players": ["player3_id"],
      "status": "pending",
      "evaluation_score": 85,
      "expires_at": "2024-04-20T00:00:00Z",
      "created_at": "2024-04-15T10:00:00Z",
      "analysis": {
        "fairness": "fair",
        "recommendations": ["Consider adding a draft pick"],
        "risk_factors": ["Player 1 has injury concerns"]
      }
    }
  ],
  "status": "success"
}
```

### Propose Trade

```http
POST /trades
Content-Type: application/json

{
  "league_id": "league_id",
  "receiving_team_id": "team2_id",
  "proposed_players": ["player1_id", "player2_id"],
  "requested_players": ["player3_id"],
  "message": "Looking to upgrade my outfield"
}
```

### Accept/Reject Trade

```http
PATCH /trades/{trade_id}
Content-Type: application/json

{
  "status": "accepted"
}
```

### Get Trade Analysis

```http
GET /trades/{trade_id}/analysis
```

**Response:**

```json
{
  "data": {
    "score": 85,
    "analysis": "This trade appears to be fair based on current player values...",
    "fairness": "fair",
    "recommendations": [
      "Consider the injury history of Player 1",
      "Player 3 has higher upside potential"
    ],
    "risk_factors": ["Player 1 is currently questionable with an injury"],
    "comparable_trades": [
      {
        "date": "2024-03-20",
        "players_involved": ["Similar players"],
        "outcome": "accepted"
      }
    ]
  },
  "status": "success"
}
```

## Waiver System

### List Waiver Claims

```http
GET /waivers
```

**Query Parameters:**

- `league_id`: Filter by league
- `status`: Filter by status (pending, successful, failed)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:**

```json
{
  "data": [
    {
      "id": "waiver_id",
      "team_id": "team_id",
      "player_id": "player_id",
      "bid_amount": 25,
      "drop_player_id": "drop_player_id",
      "priority": 1,
      "status": "pending",
      "processed_at": null,
      "created_at": "2024-04-15T10:00:00Z"
    }
  ],
  "status": "success"
}
```

### Submit Waiver Claim

```http
POST /waivers
Content-Type: application/json

{
  "league_id": "league_id",
  "player_id": "player_id",
  "bid_amount": 25,
  "drop_player_id": "drop_player_id"
}
```

### Get Waiver History

```http
GET /waivers/history
```

**Query Parameters:**

- `league_id`: Filter by league
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

## Scoring System

### Get Scoreboard

```http
GET /scoring/scoreboard/{league_id}
```

**Query Parameters:**

- `week`: Week number (default: current week)

**Response:**

```json
{
  "data": {
    "league_id": "league_id",
    "week": 15,
    "matchups": [
      {
        "team1_id": "team1_id",
        "team1_name": "Team 1",
        "team1_score": 125.5,
        "team2_id": "team2_id",
        "team2_name": "Team 2",
        "team2_score": 118.2,
        "categories": {
          "r": { "team1": 8, "team2": 6 },
          "hr": { "team1": 2, "team2": 1 },
          "rbi": { "team1": 12, "team2": 9 }
        }
      }
    ],
    "standings": [
      {
        "team_id": "team1_id",
        "team_name": "Team 1",
        "wins": 8,
        "losses": 2,
        "ties": 0,
        "points_for": 1250.5,
        "points_against": 1180.2,
        "playoff_odds": 0.95
      }
    ]
  },
  "status": "success"
}
```

### Get Player Scores

```http
GET /scoring/players/{player_id}
```

**Query Parameters:**

- `week`: Week number (default: current week)
- `season`: Season year (default: current season)

**Response:**

```json
{
  "data": {
    "player_id": "player_id",
    "name": "Mike Trout",
    "week_scores": [
      {
        "week": 15,
        "date": "2024-04-15",
        "stats": {
          "r": 1,
          "hr": 0,
          "rbi": 0,
          "sb": 0,
          "avg": 0.25
        },
        "points": 2.5,
        "projected_points": 3.2
      }
    ],
    "season_totals": {
      "r": 12,
      "hr": 5,
      "rbi": 15,
      "sb": 2,
      "avg": 0.312,
      "total_points": 45.2
    }
  },
  "status": "success"
}
```

## Data Models

### League Model

```typescript
interface League {
  id: string;
  name: string;
  sport: "mlb" | "wnba" | "nfl";
  league_type: "traditional" | "guillotine" | "dynasty" | "keeper";
  settings: LeagueSettings;
  status: "setup" | "drafting" | "active" | "completed";
  commissioner_id: string;
  created_at: string;
  updated_at: string;
}
```

### Player Model

```typescript
interface Player {
  id: string;
  external_id: string;
  name: string;
  position: string;
  team: string;
  injury_status: "healthy" | "questionable" | "doubtful" | "out" | "ir";
  projected_points: number;
  season_stats: Record<string, number>;
  game_stats: Record<string, number>;
}
```

### Lineup Model

```typescript
interface Lineup {
  id: string;
  team_id: string;
  week: number;
  players: LineupSlot[];
  projected_points: number;
  actual_points?: number;
  locked: boolean;
  version: number;
  updated_at: string;
}
```

## Error Handling

### Error Response Format

```json
{
  "error": "Invalid league ID",
  "status": "error",
  "code": "INVALID_LEAGUE_ID",
  "details": {
    "league_id": "invalid_id",
    "valid_format": "uuid"
  }
}
```

### Common Error Codes

- `INVALID_REQUEST`: Malformed request data
- `UNAUTHORIZED`: Invalid or missing authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid data provided
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Rate Limiting

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded

```json
{
  "error": "Rate limit exceeded",
  "status": "error",
  "code": "RATE_LIMITED",
  "details": {
    "limit": 1000,
    "remaining": 0,
    "reset_time": "2024-04-15T15:00:00Z"
  }
}
```

## Webhooks

### Webhook Configuration

```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["trade.proposed", "waiver.processed", "draft.completed"],
  "secret": "your_webhook_secret"
}
```

### Supported Events

- `league.created`: New league created
- `league.updated`: League settings changed
- `team.joined`: User joined league
- `draft.started`: Draft began
- `draft.completed`: Draft finished
- `trade.proposed`: Trade proposal created
- `trade.accepted`: Trade accepted
- `trade.rejected`: Trade rejected
- `waiver.processed`: Waiver claims processed
- `lineup.locked`: Lineup deadline passed
- `scoring.updated`: Scores updated

### Webhook Payload

```json
{
  "event": "trade.proposed",
  "timestamp": "2024-04-15T10:00:00Z",
  "data": {
    "trade_id": "trade_id",
    "league_id": "league_id",
    "proposing_team_id": "team1_id",
    "receiving_team_id": "team2_id"
  }
}
```

## Conclusion

This API provides comprehensive access to all Ultimate Fantasy platform features, enabling developers to build custom applications, integrations, and tools. The API follows RESTful conventions with consistent error handling and comprehensive documentation.

For additional support or questions about the API, please refer to the developer documentation or contact the development team.
