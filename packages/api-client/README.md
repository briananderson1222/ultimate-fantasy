# @ultimate-fantasy/api-client

Cross-platform API client for the Ultimate Fantasy platform. Provides a unified interface for making HTTP requests that works seamlessly between NextJS web applications and React Native mobile apps.

## Features

- 🌐 **Cross-Platform HTTP Client** - Works on web and React Native
- 🔄 **React Query Integration** - Built-in caching and synchronization
- 🛡️ **Type Safety** - Full TypeScript support with generated types
- ⚡ **Auto-Retry Logic** - Configurable retry mechanisms
- 🔐 **Authentication** - JWT token management
- 📊 **Request/Response Logging** - Debug-friendly logging
- 🎯 **Service Layer** - Organized API endpoints by domain

## Installation

```bash
npm install @ultimate-fantasy/api-client
```

## Quick Start

### Basic Usage

```typescript
import { httpClient, LeaguesService } from '@ultimate-fantasy/api-client';

// Create a service instance
const leaguesService = LeaguesService.create(httpClient);

// Fetch user's leagues
const leagues = await leaguesService.getMyLeagues();

// Create a new league
const newLeague = await leaguesService.createLeague({
  name: 'My Fantasy League',
  total_rosters: 12,
  settings: {
    scoring: { scoring_type: 'ppr' },
    roster: { roster_positions: ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'] }
  }
});
```

### React Query Integration

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { LeaguesService, httpClient } from '@ultimate-fantasy/api-client';

const leaguesService = LeaguesService.create(httpClient);

function MyLeagues() {
  // Fetch leagues with caching
  const { data: leagues, isLoading, error } = useQuery({
    queryKey: ['leagues'],
    queryFn: () => leaguesService.getMyLeagues()
  });

  // Create league mutation
  const createLeague = useMutation({
    mutationFn: leaguesService.createLeague,
    onSuccess: () => {
      // Invalidate and refetch leagues
      queryClient.invalidateQueries({ queryKey: ['leagues'] });
    }
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {leagues?.items.map(league => (
        <div key={league.league_id}>{league.name}</div>
      ))}
    </div>
  );
}
```

## API Reference

### HTTP Client

The core HTTP client provides low-level request functionality:

```typescript
import { httpClient } from '@ultimate-fantasy/api-client';

// GET request
const response = await httpClient.get('/api/leagues');

// POST request with data
const league = await httpClient.post('/api/leagues', {
  name: 'My League',
  total_rosters: 12
});

// PUT request
const updated = await httpClient.put('/api/leagues/123', updateData);

// DELETE request
await httpClient.delete('/api/leagues/123');
```

#### Configuration

```typescript
import { createHttpClient } from '@ultimate-fantasy/api-client';

const client = createHttpClient({
  baseURL: 'https://api.ultimatefantasy.app',
  timeout: 30000,
  retryAttempts: 3,
  headers: {
    'Authorization': 'Bearer your-token'
  }
});
```

### Services

Services provide domain-specific API methods:

#### LeaguesService

```typescript
import { LeaguesService } from '@ultimate-fantasy/api-client';

const service = LeaguesService.create(httpClient);

// Get user's leagues
const leagues = await service.getMyLeagues();

// Get specific league
const league = await service.getLeague('league-id');

// Create league
const newLeague = await service.createLeague(leagueData);

// Update league
const updated = await service.updateLeague('league-id', updates);

// Delete league
await service.deleteLeague('league-id');

// Join league
await service.joinLeague('league-id', { password: 'optional' });

// Leave league
await service.leaveLeague('league-id');
```

#### ScoreboardService

```typescript
import { ScoreboardService } from '@ultimate-fantasy/api-client';

const service = ScoreboardService.create(httpClient);

// Get league scoreboard
const scoreboard = await service.getScoreboard('league-id', { week: 1 });

// Get matchups
const matchups = await service.getMatchups('league-id', { week: 1 });

// Get standings
const standings = await service.getStandings('league-id');
```

#### WaiversService

```typescript
import { WaiversService } from '@ultimate-fantasy/api-client';

const service = WaiversService.create(httpClient);

// Get waiver claims
const claims = await service.getWaiverClaims('league-id');

// Add waiver claim
await service.addWaiverClaim('league-id', {
  player_id: 'player-123',
  drop_player_id: 'player-456',
  priority: 1
});

// Cancel waiver claim
await service.cancelWaiverClaim('league-id', 'claim-id');

// Process waivers (commissioner only)
await service.processWaivers('league-id');
```

#### LineupsService

```typescript
import { LineupsService } from '@ultimate-fantasy/api-client';

const service = LineupsService.create(httpClient);

// Get lineup
const lineup = await service.getLineup('team-id', { week: 1 });

// Set lineup
await service.setLineup('team-id', {
  week: 1,
  lineup: {
    QB: 'player-123',
    RB: ['player-456', 'player-789'],
    WR: ['player-101', 'player-102'],
    TE: 'player-103',
    K: 'player-104',
    DEF: 'player-105'
  }
});

// Get optimal lineup
const optimal = await service.getOptimalLineup('team-id', { week: 1 });
```

### Error Handling

The API client provides structured error handling:

```typescript
import { ApiError } from '@ultimate-fantasy/api-client';

try {
  const leagues = await leaguesService.getMyLeagues();
} catch (error) {
  if (error instanceof ApiError) {
    console.log('API Error:', error.message);
    console.log('Status:', error.status);
    console.log('Data:', error.data);

    // Handle specific errors
    switch (error.status) {
      case 401:
        // Unauthorized - redirect to login
        break;
      case 403:
        // Forbidden - show access denied
        break;
      case 404:
        // Not found - show not found message
        break;
      case 500:
        // Server error - show generic error
        break;
    }
  } else {
    // Network or other errors
    console.error('Request failed:', error);
  }
}
```

### Authentication

The client handles JWT token authentication automatically:

```typescript
import { httpClient } from '@ultimate-fantasy/api-client';

// Set authentication token
httpClient.setAuthToken('your-jwt-token');

// Clear authentication
httpClient.clearAuth();

// Check if authenticated
const isAuthenticated = httpClient.isAuthenticated();
```

### Request/Response Interceptors

Customize request and response handling:

```typescript
import { httpClient } from '@ultimate-fantasy/api-client';

// Request interceptor
httpClient.addRequestInterceptor((config) => {
  // Add timestamp to all requests
  config.headers['X-Request-Time'] = Date.now().toString();
  return config;
});

// Response interceptor
httpClient.addResponseInterceptor(
  (response) => {
    // Transform successful responses
    return response;
  },
  (error) => {
    // Handle errors globally
    if (error.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Models

### ApiService

Represents an API service configuration:

```typescript
import { ApiService } from '@ultimate-fantasy/api-client';

const service = new ApiService({
  name: 'LeaguesService',
  baseUrl: '/api/leagues',
  endpoints: [
    {
      path: '/',
      method: 'GET',
      authenticated: true
    },
    {
      path: '/',
      method: 'POST',
      authenticated: true,
      requestSchema: createLeagueSchema,
      responseSchema: leagueSchema
    }
  ],
  authenticated: true,
  rateLimit: { requests: 100, window: 60000 }
});
```

### Endpoint

Represents an individual API endpoint:

```typescript
import { Endpoint } from '@ultimate-fantasy/api-client';

const endpoint = new Endpoint({
  path: '/leagues/{id}',
  method: 'GET',
  authenticated: true,
  requestSchema: z.object({
    id: z.string()
  }),
  responseSchema: leagueSchema
});
```

## Platform Compatibility

### Web (NextJS)
- Uses `fetch` API
- Full browser request capabilities
- CORS handling
- Cookie support

### Mobile (React Native)
- Uses React Native `fetch`
- Network state awareness
- Background request handling
- Certificate pinning support

### Automatic Detection

The client automatically adapts based on the platform:

```typescript
// Platform-specific optimizations are applied automatically
const client = httpClient; // Same interface, platform-optimized implementation
```

## Configuration

### Environment Variables

```bash
# API Base URL
NEXT_PUBLIC_API_BASE_URL=https://api.ultimatefantasy.app

# API Timeout (optional)
NEXT_PUBLIC_API_TIMEOUT=30000

# Enable debug logging (optional)
NEXT_PUBLIC_API_DEBUG=true
```

### Default Configuration

```typescript
const defaultConfig = {
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};
```

## Development

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

### Type Generation

API types are generated from OpenAPI specifications:

```bash
npm run generate-types
```

## Contributing

1. Follow RESTful API conventions
2. Add comprehensive error handling
3. Write tests for new endpoints
4. Update TypeScript types
5. Ensure cross-platform compatibility

## Dependencies

### Core Dependencies
- `axios` - HTTP client library
- `zod` - Schema validation

### Peer Dependencies
- `@tanstack/react-query` - Caching and synchronization
- `react` ^18.0.0

## License

MIT