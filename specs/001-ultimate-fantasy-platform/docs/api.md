# Ultimate Fantasy Platform API (Summary)

Source of truth: specs/001-ultimate-fantasy-platform/contracts/openapi.yml

Base URL
- Local dev: http://localhost:8000
- Frontend uses `NEXT_PUBLIC_API_BASE_URL` to target the backend.

Auth
- Prototyped via header `x-user-id: <uuid>` for endpoints that change data.

Endpoints
- POST `/leagues`
  - Summary: Create a new league
  - Body: `{ name: string, sport: string, league_type: string, season: string }`
  - Response 201: `{ league_id, name, sport, league_type, season, invite_link? }`

- PATCH `/leagues/{leagueId}/settings`
  - Summary: Update/customize league rules
  - Path: `leagueId` (uuid)
  - Body: `{ name: string, value: object }`
  - Response 200: `{ rule_id, league_id, name, value }`

- POST `/leagues/{leagueId}/join`
  - Summary: Join a league
  - Path: `leagueId` (uuid)
  - Response 200: `{ team_id, league_id, user_id, team_name }`

- PUT `/lineups`
  - Summary: Set a lineup
  - Body: `{ team_id: uuid, game_day: date, players: [{ player_id: uuid, position: string }, ...] }`
  - Response 200: Echoes saved lineup with optional `version`

- GET `/leagues/{leagueId}/scoreboard`
  - Summary: View scores
  - Path: `leagueId` (uuid)
  - Response 200: `{ league_id, items: [{ team_id: uuid, total_points: number, lineup_count?: number }] }`

- POST `/waivers/bids`
  - Summary: Place a waiver bid
  - Body: `{ league_id: uuid, team_id: uuid, player_id: uuid, bid: number }`
  - Response 201: `{ waiver_id, league_id, team_id, player_id, bid, status }`

- GET `/leagues/{leagueId}/public`
  - Summary: Public league view
  - Path: `leagueId` (uuid)
  - Response 200: `{ league_id, name, sport, league_type, season }`

Notes
- The OpenAPI file remains authoritative for field types and response codes.
- SQLite is used in local tests; PostgreSQL is recommended for development.
