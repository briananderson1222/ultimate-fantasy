// Platform-agnostic HTTP client for Ultimate Fantasy API

export interface HttpClientConfig {
  baseUrl: string;
  timeout?: number;
  defaultHeaders?: Record<string, string>;
  retryAttempts?: number;
  retryDelay?: number;
  enableTokenRefresh?: boolean;
  refreshTokenEndpoint?: string;
}

export interface HttpClient {
  get<T>(path: string, options?: RequestInit): Promise<T>;
  post<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  put<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  patch<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  delete<T>(path: string, options?: RequestInit): Promise<T>;
  setAuthToken(token: string): void;
  clearAuthToken(): void;
  updateConfig(newConfig: Partial<HttpClientConfig>): void;
}

export class ApiError extends Error {
  public status: number;
  public data?: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// Universal HTTP client implementation
export class UniversalHttpClient implements HttpClient {
  private config: HttpClientConfig;
  private authToken: string | null = null;

  constructor(config: HttpClientConfig) {
    this.config = config;
  }

  private getAuthToken(): string | null {
    // Try to get from instance first, then fall back to storage
    if (this.authToken) {
      return this.authToken;
    }

    try {
      // Web environment
      if (typeof window !== 'undefined' && window.localStorage) {
        return localStorage.getItem('uf_token');
      }

      // React Native environment would use AsyncStorage
      // This would be handled by the platform-specific adapter
      return null;
    } catch {
      return null;
    }
  }

  private async makeRequest<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    return this.makeRequestWithRetry<T>(path, options, 0);
  }

  private async makeRequestWithRetry<T>(
    path: string,
    options: RequestInit = {},
    attempt: number
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const token = this.getAuthToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.config.defaultHeaders,
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // Apply request interceptors
    let requestOptions: RequestInit = {
      ...options,
      headers,
    };

    for (const interceptor of this.requestInterceptors) {
      requestOptions = await interceptor(requestOptions);
    }

    // Add timeout if supported
    if (this.config.timeout && 'signal' in options === false) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
      requestOptions.signal = controller.signal;

      try {
        let response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);

        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          response = await interceptor(response);
        }

        // Handle 401 with token refresh
        if (response.status === 401 && this.config.enableTokenRefresh && attempt === 0) {
          const refreshSuccess = await this.attemptTokenRefresh();
          if (refreshSuccess) {
            return this.makeRequestWithRetry<T>(path, options, attempt + 1);
          }
        }

        return await this.handleResponse<T>(response);
      } catch (error) {
        clearTimeout(timeoutId);

        // Retry logic for network errors
        if (this.shouldRetry(error, attempt)) {
          await this.delay(this.config.retryDelay || 1000);
          return this.makeRequestWithRetry<T>(path, options, attempt + 1);
        }

        throw error;
      }
    } else {
      try {
        let response = await fetch(url, requestOptions);

        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          response = await interceptor(response);
        }

        // Handle 401 with token refresh
        if (response.status === 401 && this.config.enableTokenRefresh && attempt === 0) {
          const refreshSuccess = await this.attemptTokenRefresh();
          if (refreshSuccess) {
            return this.makeRequestWithRetry<T>(path, options, attempt + 1);
          }
        }

        return await this.handleResponse<T>(response);
      } catch (error) {
        // Retry logic for network errors
        if (this.shouldRetry(error, attempt)) {
          await this.delay(this.config.retryDelay || 1000);
          return this.makeRequestWithRetry<T>(path, options, attempt + 1);
        }

        throw error;
      }
    }
  }

  private shouldRetry(error: unknown, attempt: number): boolean {
    if (!this.config.retryAttempts || attempt >= this.config.retryAttempts) {
      return false;
    }

    // Retry on network errors, timeouts, and some server errors
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('fetch') ||
        message.includes('aborted')
      );
    }

    return false;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async attemptTokenRefresh(): Promise<boolean> {
    if (!this.config.refreshTokenEndpoint) {
      return false;
    }

    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${this.config.baseUrl}${this.config.refreshTokenEndpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access_token) {
          this.setAuthToken(data.access_token);
          if (data.refresh_token) {
            this.setRefreshToken(data.refresh_token);
          }
          return true;
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  }

  private getRefreshToken(): string | null {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        return localStorage.getItem('uf_refresh_token');
      }
    } catch {
      // Storage not available
    }
    return null;
  }

  private setRefreshToken(token: string): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('uf_refresh_token', token);
      }
    } catch {
      // Storage not available
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      // Try to surface structured error details when available
      try {
        const data = await response.clone().json();
        const error = new ApiError(
          `API ${response.status}: ${typeof data?.detail === 'string' ? data.detail : response.statusText}`,
          response.status,
          data
        );
        throw error;
      } catch (jsonError) {
        const text = await response.text().catch(() => '');
        const error = new ApiError(
          `API ${response.status}: ${text || response.statusText}`,
          response.status
        );
        throw error;
      }
    }

    // Some endpoints may return 204 or no body
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    }

    // 204 No Content: return null instead of undefined to satisfy consumers like React Query.
    if (response.status === 204) {
      return null as unknown as T;
    }

    // If content-type is not JSON, attempt to read text and throw a descriptive error
    // instead of returning undefined (which breaks consumers expecting a value).
    try {
      const text = await response.text();
      throw new ApiError(
        `Unexpected response content-type: ${contentType || 'unknown'} (${response.status}).`,
        response.status,
        text
      );
    } catch (e) {
      if (e instanceof ApiError) throw e;
      throw new ApiError(
        `Unexpected non-JSON response (${response.status}).`,
        response.status
      );
    }
  }

  async get<T>(path: string, options?: RequestInit): Promise<T> {
    return this.makeRequest<T>(path, {
      ...options,
      method: 'GET',
    });
  }

  async post<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.makeRequest<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.makeRequest<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.makeRequest<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(path: string, options?: RequestInit): Promise<T> {
    return this.makeRequest<T>(path, {
      ...options,
      method: 'DELETE',
    });
  }

  setAuthToken(token: string): void {
    this.authToken = token;

    // Also persist to storage if available
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('uf_token', token);
      }
    } catch {
      // Storage not available or failed
    }
  }

  clearAuthToken(): void {
    this.authToken = null;

    // Also clear from storage if available
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('uf_token');
        localStorage.removeItem('uf_refresh_token');
      }
    } catch {
      // Storage not available or failed
    }
  }

  // Request/response interceptors
  private requestInterceptors: Array<(options: RequestInit) => RequestInit | Promise<RequestInit>> = [];
  private responseInterceptors: Array<(response: Response) => Response | Promise<Response>> = [];

  addRequestInterceptor(interceptor: (options: RequestInit) => RequestInit | Promise<RequestInit>): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: (response: Response) => Response | Promise<Response>): void {
    this.responseInterceptors.push(interceptor);
  }

  // Utility methods
  getBaseUrl(): string {
    return this.config.baseUrl;
  }

  updateConfig(newConfig: Partial<HttpClientConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Factory function for creating HTTP client
export function createHttpClient(config: HttpClientConfig): HttpClient {
  return new UniversalHttpClient(config);
}

function resolveDefaultBaseUrl(): string {
  if (typeof process !== 'undefined' && process?.env) {
    const env = process.env as Record<string, string | undefined>;
    const candidates = [
      env.NEXT_PUBLIC_API_BASE_URL,
      env.EXPO_PUBLIC_API_BASE_URL,
      env.API_BASE_URL,
      env.REACT_NATIVE_API_BASE_URL,
    ];

    for (const value of candidates) {
      if (typeof value === 'string' && value.trim().length > 0) {
        return value.trim();
      }
    }
  }

  return '/api';
}

// Default configuration
export const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseUrl: resolveDefaultBaseUrl(),
  timeout: 30000, // 30 seconds
  defaultHeaders: {
    'Accept': 'application/json',
  },
};

// Singleton instance for easy usage
export const httpClient = createHttpClient(DEFAULT_HTTP_CONFIG);

// ApiError is already exported above

// Utility functions for common patterns
export function isApiError(error: unknown): error is ApiError {
  return error instanceof Error && 'status' in error;
}

export function handleApiError(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}
