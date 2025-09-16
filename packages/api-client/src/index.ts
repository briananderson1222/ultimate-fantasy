// API Client Package - Main Exports

// Models - specific exports to avoid conflicts
export {
  ApiService,
  ApiServiceBuilder,
  ApiServiceSchema,
  type ApiServiceData
} from './models/ApiService';

export {
  Endpoint,
  EndpointSchema,
  type EndpointData,
  type HttpMethod
} from './models/Endpoint';

// Services
export * from './services/leagues';
export * from './services/scoreboard';
export * from './services/waivers';
export * from './services/lineups';

// HTTP Client
export * from './client/http';

// Re-export types for convenience
export type {
  HttpClient,
  HttpClientConfig,
  ApiError
} from './client/http';