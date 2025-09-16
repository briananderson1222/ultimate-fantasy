// Platform-agnostic HTTP client for Ultimate Fantasy API

export interface HttpClientConfig {
  baseUrl: string;
  timeout?: number;
  defaultHeaders?: Record<string, string>;
}

export interface HttpClient {
  get<T>(path: string, options?: RequestInit): Promise<T>;
  post<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  put<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  patch<T>(path: string, data?: any, options?: RequestInit): Promise<T>;
  delete<T>(path: string, options?: RequestInit): Promise<T>;
  setAuthToken(token: string): void;
  clearAuthToken(): void;
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

    const requestOptions: RequestInit = {
      ...options,
      headers,
    };

    // Add timeout if supported
    if (this.config.timeout && 'signal' in options === false) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
      requestOptions.signal = controller.signal;

      try {
        const response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);
        return await this.handleResponse<T>(response);
      } catch (error) {
        clearTimeout(timeoutId);
        throw error;
      }
    } else {
      const response = await fetch(url, requestOptions);
      return await this.handleResponse<T>(response);
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
    return undefined as unknown as T;
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

// Default configuration
export const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
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