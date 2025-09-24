# Ultimate Fantasy Platform API Documentation

This directory contains comprehensive documentation for the Ultimate Fantasy Platform REST API.

## Overview

The Ultimate Fantasy Platform provides a complete RESTful API for fantasy sports applications, including user management, league operations, sports data, draft management, trading, and real-time features.

## Base URL

```
https://api.ultimatefantasy.com/api/v1
```

## Authentication

All API endpoints (except registration and login) require authentication using Bearer tokens:

```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints Documentation

- [Authentication](./auth.md) - User registration, login, password reset
- [Leagues](./leagues.md) - League CRUD, membership, settings
- [Sports Data](./sports.md) - Player data, stats, news, projections
- [Draft](./draft.md) - Draft room management, picks, auto-draft
- [Lineups](./lineups.md) - Lineup management, optimization
- [Trades](./trades.md) - Trade proposals, evaluation, execution
- [Waivers](./waivers.md) - Waiver claims, free agency

## Rate Limiting

- Most endpoints: 100 requests per minute
- Real-time endpoints: 1000 requests per minute
- Sports data endpoints: 500 requests per minute

## Error Handling

All API responses follow a consistent format:

```json
{
  "success": boolean,
  "data": object | array | null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": object | null
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

## Standard HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

## WebSocket Endpoints

Real-time features are available via WebSocket connections:

- `/ws/drafts/{draft_id}` - Real-time draft updates
- `/ws/leagues/{league_id}/chat` - League chat
- `/ws/trades/{trade_id}` - Trade status updates

## Performance Targets

- Standard endpoints: < 300ms response time
- Analytics endpoints: < 600ms response time
- WebSocket message latency: < 100ms
- 99.9% uptime SLA

## SDK and Client Libraries

Official SDKs are available for:
- JavaScript/TypeScript
- Python
- Swift (iOS)
- Kotlin (Android)

## Support

For API support and questions:
- Documentation: https://docs.ultimatefantasy.com
- Support: api-support@ultimatefantasy.com
- Status Page: https://status.ultimatefantasy.com