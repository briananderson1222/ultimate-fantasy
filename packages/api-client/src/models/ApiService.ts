import { z } from 'zod';
import { EndpointSchema, type EndpointData } from './Endpoint';

// ApiService validation schema
const ApiServiceSchema = z.object({
  name: z.string().min(1, 'Service name is required'),
  endpoints: z.array(EndpointSchema).default([]),
  baseUrl: z.string().url().optional(),
  authentication: z.boolean().default(false),
  platform: z.literal('universal')
});

// TypeScript types
export type ApiServiceData = z.infer<typeof ApiServiceSchema>;

// ApiService class
export class ApiService {
  public readonly name: string;
  public readonly endpoints: EndpointData[];
  public readonly baseUrl?: string;
  public readonly authentication: boolean;
  public readonly platform: 'universal';

  constructor(data: ApiServiceData) {
    // Validate input data
    const validatedData = ApiServiceSchema.parse(data);

    this.name = validatedData.name;
    this.endpoints = validatedData.endpoints;
    this.baseUrl = validatedData.baseUrl;
    this.authentication = validatedData.authentication;
    this.platform = validatedData.platform;
  }

  // Helper methods
  public addEndpoint(endpoint: EndpointData): ApiService {
    const newEndpoints = [...this.endpoints, endpoint];
    return new ApiService({
      name: this.name,
      endpoints: newEndpoints,
      baseUrl: this.baseUrl,
      authentication: this.authentication,
      platform: this.platform
    });
  }

  public getEndpointsByMethod(method: EndpointData['method']): EndpointData[] {
    return this.endpoints.filter(endpoint => endpoint.method === method);
  }

  public getEndpoint(path: string, method: EndpointData['method']): EndpointData | undefined {
    return this.endpoints.find(endpoint =>
      endpoint.path === path && endpoint.method === method
    );
  }

  public getAuthenticatedEndpoints(): EndpointData[] {
    return this.endpoints.filter(endpoint => endpoint.authenticated);
  }

  public getPublicEndpoints(): EndpointData[] {
    return this.endpoints.filter(endpoint => !endpoint.authenticated);
  }

  public hasEndpoint(path: string, method: EndpointData['method']): boolean {
    return this.getEndpoint(path, method) !== undefined;
  }

  public requiresAuthentication(): boolean {
    return this.authentication || this.endpoints.some(endpoint => endpoint.authenticated);
  }

  public toJSON(): ApiServiceData {
    return {
      name: this.name,
      endpoints: this.endpoints,
      baseUrl: this.baseUrl,
      authentication: this.authentication,
      platform: this.platform
    };
  }

  // Static factory methods
  static fromJSON(data: ApiServiceData): ApiService {
    return new ApiService(data);
  }

  static validate(data: unknown): ApiServiceData {
    return ApiServiceSchema.parse(data);
  }

  // Builder pattern methods
  static create(name: string, baseUrl?: string): ApiServiceBuilder {
    return new ApiServiceBuilder(name, baseUrl);
  }
}

// Builder class for easier ApiService construction
export class ApiServiceBuilder {
  private name: string;
  private endpoints: EndpointData[] = [];
  private baseUrl?: string;
  private authentication: boolean = false;

  constructor(name: string, baseUrl?: string) {
    this.name = name;
    this.baseUrl = baseUrl;
  }

  public withAuthentication(): ApiServiceBuilder {
    this.authentication = true;
    return this;
  }

  public addEndpoint(
    path: string,
    method: EndpointData['method'],
    options: {
      requestSchema?: object;
      responseSchema?: object;
      authenticated?: boolean;
    } = {}
  ): ApiServiceBuilder {
    const endpoint: EndpointData = {
      path,
      method,
      requestSchema: options.requestSchema,
      responseSchema: options.responseSchema,
      authenticated: options.authenticated || false
    };

    this.endpoints.push(endpoint);
    return this;
  }

  public get(path: string, authenticated = false): ApiServiceBuilder {
    return this.addEndpoint(path, 'GET', { authenticated });
  }

  public post(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = false
  ): ApiServiceBuilder {
    return this.addEndpoint(path, 'POST', { requestSchema, responseSchema, authenticated });
  }

  public put(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = true
  ): ApiServiceBuilder {
    return this.addEndpoint(path, 'PUT', { requestSchema, responseSchema, authenticated });
  }

  public delete(path: string, authenticated = true): ApiServiceBuilder {
    return this.addEndpoint(path, 'DELETE', { authenticated });
  }

  public patch(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = true
  ): ApiServiceBuilder {
    return this.addEndpoint(path, 'PATCH', { requestSchema, responseSchema, authenticated });
  }

  public build(): ApiService {
    return new ApiService({
      name: this.name,
      endpoints: this.endpoints,
      baseUrl: this.baseUrl,
      authentication: this.authentication,
      platform: 'universal'
    });
  }
}

// Export schemas for external use
export { ApiServiceSchema };