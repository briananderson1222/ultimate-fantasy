# Ultimate Fantasy Platform API (Summary)

Source of truth: specs/001-ultimate-fantasy-platform/contracts/openapi.yml

Base URL
- Local dev: http://localhost:8000
- Frontend uses `NEXT_PUBLIC_API_BASE_URL` to target the backend.

Auth
- Authorization: Bearer JWT
  - Dev mode: HS256 signed with `AUTH_DEV_SECRET` (sub claim identifies the user)
  - Prod mode (optional): RS256 via JWKS at `AUTH_JWKS_URL` with `AUTH_AUDIENCE` and `AUTH_ISSUER`

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

- GET `/me/leagues`
  - Summary: List leagues for the current user
  - Auth: `Authorization: Bearer <JWT>` (dev HS256 supported)
  - Response 200: `{ items: [{ league_id, name, season, team_id }] }`
  - Example:
    - export TOKEN="<jwt>"
    - curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:8000/me/leagues | jq

- GET `/leagues/{leagueId}/members`
  - Summary: List members (teams) in a league
  - Path: `leagueId` (uuid)
  - Response 200: `{ items: [{ team_id, user_id, team_name }] }`
  - Example:
    - LEAGUE_ID=00000000-0000-0000-0000-000000000000
    - curl -sS http://localhost:8000/leagues/$LEAGUE_ID/members | jq

- GET `/waivers`
  - Summary: List waiver bids
  - Query: `league_id: uuid` (required), `team_id?: uuid`, `limit?: 1..100` (default 50), `offset?: >=0` (default 0)
  - Response 200: `{ items: [{ waiver_id, league_id, team_id, player_id, bid, status }] }`
  - Example:
    - LEAGUE_ID=00000000-0000-0000-0000-000000000000
    - curl -sS "http://localhost:8000/waivers?league_id=$LEAGUE_ID&limit=50&offset=0" | jq

- GET `/lineups`
  - Summary: List saved lineups
  - Query: `team_id: uuid` (required), `game_day?: YYYY-MM-DD`, `limit?: 1..100` (default 50), `offset?: >=0` (default 0)
  - Response 200: `{ items: [{ lineup_id, team_id, game_day, players: [{ player_id, position }], version }] }`
  - Example:
    - TEAM_ID=00000000-0000-0000-0000-000000000000
    - curl -sS "http://localhost:8000/lineups?team_id=$TEAM_ID&game_day=2025-01-01" | jq

Notes
- The OpenAPI file remains authoritative for field types and response codes.
- SQLite is used in local tests; PostgreSQL is recommended for development.
- Frontend includes a dev-only token helper panel ("Dev Auth Token") to mint HS256 tokens in-browser and save them to `localStorage.uf_token`. Use only with `AUTH_MODE=dev`.

Frontend quick usage (React Query)
- Get your leagues:
  - import { useQuery } from '@tanstack/react-query'
  - import { getMyLeagues } from '@/services/api'
  - const leagues = useQuery({ queryKey: ['myLeagues'], queryFn: getMyLeagues })
- League members:
  - import { getLeagueMembers } from '@/services/api'
  - useQuery({ queryKey: ['leagueMembers', leagueId], queryFn: () => getLeagueMembers(leagueId), enabled: !!leagueId })
- Waivers list:
  - import { listWaivers } from '@/services/api'
  - useQuery({ queryKey: ['waivers', args], queryFn: () => listWaivers(args), enabled: !!args.league_id })
- Lineups list:
  - import { listLineups } from '@/services/api'
  - useQuery({ queryKey: ['lineups', args], queryFn: () => listLineups(args), enabled: !!args.team_id })
