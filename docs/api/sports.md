# Sports Data API

## Overview

The Sports Data API provides comprehensive access to player information, statistics, news, schedules, and projections across multiple sports leagues.

## Base URL

```
/api/v1/sports
```

## Supported Sports

- **MLB** - Major League Baseball
- **NFL** - National Football League
- **WNBA** - Women's National Basketball Association

## Endpoints

### Get Players

Get list of players with filtering and search capabilities.

**GET** `/players`

**Authentication Required**

#### Query Parameters

- `sport` (required): Sport type (mlb, nfl, wnba)
- `team` (optional): Filter by team abbreviation
- `position` (optional): Filter by player position
- `status` (optional): Player status (active, injured, inactive)
- `search` (optional): Search by player name
- `limit` (optional): Number of results (default: 50, max: 500)
- `offset` (optional): Pagination offset

#### Response

```json
{
  "success": true,
  "data": {
    "players": [
      {
        "player_id": "uuid",
        "external_id": "espn_12345",
        "name": "Player Name",
        "team_id": "LAD",
        "team_name": "Los Angeles Dodgers",
        "position": "1B",
        "sport": "mlb",
        "status": "active",
        "jersey_number": 22,
        "height": "6-2",
        "weight": 220,
        "birth_date": "1995-03-15",
        "experience": 5,
        "salary": 15000000,
        "fantasy_positions": ["1B", "OF"],
        "injury_status": null,
        "last_updated": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 750,
    "has_more": true,
    "filters_applied": {
      "sport": "mlb",
      "position": "1B"
    }
  }
}
```

#### Error Codes

- `VALIDATION_ERROR` - Invalid query parameters
- `PROVIDER_ERROR` - Sports data provider error
- `RATE_LIMIT_EXCEEDED` - Too many requests

---

### Get Player Details

Get detailed information for a specific player.

**GET** `/players/{player_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "player": {
      "player_id": "uuid",
      "external_id": "espn_12345",
      "name": "Player Name",
      "team_id": "LAD",
      "team_name": "Los Angeles Dodgers",
      "position": "1B",
      "sport": "mlb",
      "status": "active",
      "jersey_number": 22,
      "height": "6-2",
      "weight": 220,
      "birth_date": "1995-03-15",
      "experience": 5,
      "salary": 15000000,
      "fantasy_positions": ["1B", "OF"],
      "injury_status": {
        "status": "healthy",
        "description": null,
        "expected_return": null
      },
      "bio": {
        "college": "Stanford University",
        "drafted": "2018 - Round 1, Pick 5",
        "hometown": "San Diego, CA"
      },
      "last_updated": "2024-01-01T12:00:00Z"
    },
    "current_season_stats": {
      "games_played": 145,
      "at_bats": 580,
      "hits": 175,
      "home_runs": 28,
      "rbi": 95,
      "batting_average": 0.302,
      "on_base_percentage": 0.385,
      "slugging_percentage": 0.525
    },
    "career_stats": {
      "seasons": 5,
      "games_played": 720,
      "home_runs": 125,
      "rbi": 425,
      "career_batting_average": 0.285
    }
  }
}
```

#### Error Codes

- `PLAYER_NOT_FOUND` - Player doesn't exist
- `PROVIDER_ERROR` - Sports data provider error

---

### Get Player Statistics

Get detailed statistics for a player across multiple seasons.

**GET** `/players/{player_id}/stats`

**Authentication Required**

#### Query Parameters

- `season` (optional): Specific season (default: current)
- `stat_type` (optional): Type of stats (batting, pitching, fielding for MLB)
- `split_type` (optional): Stat splits (vs_left, vs_right, home, away)

#### Response

```json
{
  "success": true,
  "data": {
    "player_id": "uuid",
    "seasons": [
      {
        "season": "2024",
        "team": "LAD",
        "games_played": 145,
        "stats": {
          "at_bats": 580,
          "hits": 175,
          "doubles": 35,
          "triples": 2,
          "home_runs": 28,
          "rbi": 95,
          "runs": 88,
          "stolen_bases": 12,
          "walks": 65,
          "strikeouts": 135,
          "batting_average": 0.302,
          "on_base_percentage": 0.385,
          "slugging_percentage": 0.525,
          "ops": 0.910
        },
        "advanced_stats": {
          "war": 4.2,
          "wrc_plus": 125,
          "babip": 0.315,
          "iso": 0.223
        }
      }
    ],
    "career_totals": {
      "games_played": 720,
      "home_runs": 125,
      "rbi": 425,
      "batting_average": 0.285
    }
  }
}
```

---

### Get Player News

Get latest news and updates for a player.

**GET** `/players/{player_id}/news`

**Authentication Required**

#### Query Parameters

- `limit` (optional): Number of articles (default: 10, max: 50)
- `days` (optional): News from last N days (default: 30)

#### Response

```json
{
  "success": true,
  "data": {
    "news": [
      {
        "id": "uuid",
        "headline": "Player Name signs contract extension",
        "summary": "The first baseman agreed to a 5-year extension...",
        "source": "ESPN",
        "author": "Reporter Name",
        "published_at": "2024-01-01T10:00:00Z",
        "url": "https://espn.com/article/12345",
        "impact": "positive",
        "tags": ["contract", "extension"],
        "relevance_score": 0.95
      }
    ],
    "total": 25,
    "last_updated": "2024-01-01T12:00:00Z"
  }
}
```

---

### Get Teams

Get list of teams for a specific sport.

**GET** `/teams`

**Authentication Required**

#### Query Parameters

- `sport` (required): Sport type (mlb, nfl, wnba)
- `conference` (optional): Filter by conference/league
- `division` (optional): Filter by division

#### Response

```json
{
  "success": true,
  "data": {
    "teams": [
      {
        "team_id": "LAD",
        "name": "Los Angeles Dodgers",
        "city": "Los Angeles",
        "abbreviation": "LAD",
        "sport": "mlb",
        "conference": "National League",
        "division": "NL West",
        "logo_url": "https://cdn.ultimatefantasy.com/logos/LAD.png",
        "primary_color": "#005A9C",
        "secondary_color": "#FFFFFF",
        "established": 1883,
        "venue": {
          "name": "Dodger Stadium",
          "city": "Los Angeles",
          "capacity": 56000
        }
      }
    ],
    "total": 30
  }
}
```

---

### Get Team Details

Get detailed information for a specific team.

**GET** `/teams/{team_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "team": {
      "team_id": "LAD",
      "name": "Los Angeles Dodgers",
      "city": "Los Angeles",
      "abbreviation": "LAD",
      "sport": "mlb",
      "conference": "National League",
      "division": "NL West",
      "logo_url": "https://cdn.ultimatefantasy.com/logos/LAD.png",
      "website": "https://dodgers.com",
      "established": 1883,
      "venue": {
        "name": "Dodger Stadium",
        "address": "1000 Vin Scully Ave, Los Angeles, CA",
        "capacity": 56000,
        "surface": "Grass"
      },
      "season_record": {
        "wins": 100,
        "losses": 62,
        "win_percentage": 0.617,
        "division_rank": 1,
        "conference_rank": 3
      }
    },
    "roster": [
      {
        "player_id": "uuid",
        "name": "Player Name",
        "position": "1B",
        "jersey_number": 22,
        "status": "active"
      }
    ]
  }
}
```

---

### Get Schedule

Get game schedule for teams or leagues.

**GET** `/schedule`

**Authentication Required**

#### Query Parameters

- `sport` (required): Sport type
- `team` (optional): Filter by team
- `date_from` (optional): Start date (YYYY-MM-DD)
- `date_to` (optional): End date (YYYY-MM-DD)
- `season` (optional): Season year

#### Response

```json
{
  "success": true,
  "data": {
    "games": [
      {
        "game_id": "uuid",
        "sport": "mlb",
        "season": "2024",
        "week": 15,
        "game_date": "2024-06-15T19:10:00Z",
        "status": "scheduled|in_progress|completed|postponed",
        "home_team": {
          "team_id": "LAD",
          "name": "Los Angeles Dodgers",
          "score": null
        },
        "away_team": {
          "team_id": "SF",
          "name": "San Francisco Giants",
          "score": null
        },
        "venue": "Dodger Stadium",
        "weather": {
          "temperature": 75,
          "conditions": "Clear",
          "wind": "5 mph SW"
        }
      }
    ],
    "total": 162,
    "date_range": {
      "from": "2024-03-28",
      "to": "2024-09-29"
    }
  }
}
```

---

### Get Game Details

Get detailed information for a specific game.

**GET** `/games/{game_id}`

**Authentication Required**

#### Response

```json
{
  "success": true,
  "data": {
    "game": {
      "game_id": "uuid",
      "sport": "mlb",
      "season": "2024",
      "game_date": "2024-06-15T19:10:00Z",
      "status": "completed",
      "inning": 9,
      "home_team": {
        "team_id": "LAD",
        "name": "Los Angeles Dodgers",
        "score": 8,
        "hits": 12,
        "errors": 0
      },
      "away_team": {
        "team_id": "SF",
        "name": "San Francisco Giants",
        "score": 5,
        "hits": 9,
        "errors": 1
      },
      "venue": "Dodger Stadium",
      "attendance": 52000,
      "duration": "3:15"
    },
    "box_score": {
      "batting": [
        {
          "player_id": "uuid",
          "name": "Player Name",
          "team": "LAD",
          "position": "1B",
          "ab": 4,
          "r": 2,
          "h": 3,
          "rbi": 2,
          "bb": 0,
          "so": 1
        }
      ],
      "pitching": [
        {
          "player_id": "uuid",
          "name": "Pitcher Name",
          "team": "LAD",
          "ip": 6.0,
          "h": 6,
          "r": 3,
          "er": 3,
          "bb": 2,
          "so": 8,
          "decision": "W"
        }
      ]
    }
  }
}
```

---

### Get Player Projections

Get fantasy projections for players.

**GET** `/projections`

**Authentication Required**

#### Query Parameters

- `sport` (required): Sport type
- `position` (optional): Filter by position
- `team` (optional): Filter by team
- `timeframe` (optional): season, month, week (default: season)
- `projection_type` (optional): conservative, standard, aggressive

#### Response

```json
{
  "success": true,
  "data": {
    "projections": [
      {
        "player_id": "uuid",
        "name": "Player Name",
        "team": "LAD",
        "position": "1B",
        "projection_type": "standard",
        "timeframe": "season",
        "stats": {
          "games": 150,
          "at_bats": 580,
          "runs": 85,
          "hits": 170,
          "home_runs": 30,
          "rbi": 100,
          "stolen_bases": 8,
          "batting_average": 0.293
        },
        "fantasy_points": {
          "standard": 245.5,
          "ppr": 245.5
        },
        "confidence": 0.85,
        "last_updated": "2024-01-01T06:00:00Z"
      }
    ],
    "projection_date": "2024-01-01",
    "source": "Ultimate Fantasy Analytics"
  }
}
```

## Rate Limiting

- Standard endpoints: 500 requests per minute
- Real-time data endpoints: 100 requests per minute
- Bulk data endpoints: 50 requests per minute

## Data Freshness

- Player stats: Updated every 30 minutes during games
- News: Updated every 15 minutes
- Projections: Updated daily at 6:00 AM ET
- Schedules: Updated hourly
- Injury reports: Updated every 15 minutes

## Error Handling

### Provider Errors

When sports data providers are unavailable:

```json
{
  "success": false,
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "Sports data temporarily unavailable",
    "details": {
      "provider": "ESPN",
      "retry_after": 300
    }
  }
}
```

### Rate Limiting

When rate limits are exceeded:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 500,
      "window": 60,
      "retry_after": 45
    }
  }
}
```