import { z } from 'zod';

// Endpoint validation schema
const EndpointSchema = z.object({
  path: z.string().regex(
    /^\/[a-zA-Z0-9\/_\-\{\}]*$/,
    'Path must be a valid URL path starting with /'
  ),
  method: z.enum(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
  requestSchema: z.object({}).optional(),
  responseSchema: z.object({}).optional(),
  authenticated: z.boolean().default(false)
});

// TypeScript type
export type EndpointData = z.infer<typeof EndpointSchema>;

// HTTP method type
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// Endpoint class
export class Endpoint {
  public readonly path: string;
  public readonly method: HttpMethod;
  public readonly requestSchema?: object;
  public readonly responseSchema?: object;
  public readonly authenticated: boolean;

  constructor(data: EndpointData) {
    // Validate input data
    const validatedData = EndpointSchema.parse(data);

    this.path = validatedData.path;
    this.method = validatedData.method;
    this.requestSchema = validatedData.requestSchema;
    this.responseSchema = validatedData.responseSchema;
    this.authenticated = validatedData.authenticated;
  }

  // Helper methods
  public isReadOperation(): boolean {
    return this.method === 'GET';
  }

  public isWriteOperation(): boolean {
    return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(this.method);
  }

  public isIdempotent(): boolean {
    return ['GET', 'PUT', 'DELETE'].includes(this.method);
  }

  public isSafe(): boolean {
    return this.method === 'GET';
  }

  public requiresRequestBody(): boolean {
    return ['POST', 'PUT', 'PATCH'].includes(this.method);
  }

  public hasPathParameters(): boolean {
    return this.path.includes('{') && this.path.includes('}');
  }

  public getPathParameters(): string[] {
    const matches = this.path.match(/\{([^}]+)\}/g);
    return matches ? matches.map(match => match.slice(1, -1)) : [];
  }

  public interpolatePath(parameters: Record<string, string | number>): string {
    let interpolatedPath = this.path;

    Object.entries(parameters).forEach(([key, value]) => {
      const placeholder = `{${key}}`;
      if (interpolatedPath.includes(placeholder)) {
        interpolatedPath = interpolatedPath.replace(placeholder, String(value));
      }
    });

    // Check if all parameters were replaced
    if (interpolatedPath.includes('{') && interpolatedPath.includes('}')) {
      const remainingParams = this.getPathParameters().filter(param =>
        interpolatedPath.includes(`{${param}}`)
      );
      throw new Error(`Missing path parameters: ${remainingParams.join(', ')}`);
    }

    return interpolatedPath;
  }

  public withAuthentication(): Endpoint {
    return new Endpoint({
      path: this.path,
      method: this.method,
      requestSchema: this.requestSchema,
      responseSchema: this.responseSchema,
      authenticated: true
    });
  }

  public withRequestSchema(schema: object): Endpoint {
    return new Endpoint({
      path: this.path,
      method: this.method,
      requestSchema: schema,
      responseSchema: this.responseSchema,
      authenticated: this.authenticated
    });
  }

  public withResponseSchema(schema: object): Endpoint {
    return new Endpoint({
      path: this.path,
      method: this.method,
      requestSchema: this.requestSchema,
      responseSchema: schema,
      authenticated: this.authenticated
    });
  }

  public toJSON(): EndpointData {
    return {
      path: this.path,
      method: this.method,
      requestSchema: this.requestSchema,
      responseSchema: this.responseSchema,
      authenticated: this.authenticated
    };
  }

  // Static factory methods
  static fromJSON(data: EndpointData): Endpoint {
    return new Endpoint(data);
  }

  static validate(data: unknown): EndpointData {
    return EndpointSchema.parse(data);
  }

  // Static factory methods for common HTTP methods
  static get(path: string, authenticated = false): Endpoint {
    return new Endpoint({
      path,
      method: 'GET',
      authenticated
    });
  }

  static post(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = false
  ): Endpoint {
    return new Endpoint({
      path,
      method: 'POST',
      requestSchema,
      responseSchema,
      authenticated
    });
  }

  static put(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = true
  ): Endpoint {
    return new Endpoint({
      path,
      method: 'PUT',
      requestSchema,
      responseSchema,
      authenticated
    });
  }

  static patch(
    path: string,
    requestSchema?: object,
    responseSchema?: object,
    authenticated = true
  ): Endpoint {
    return new Endpoint({
      path,
      method: 'PATCH',
      requestSchema,
      responseSchema,
      authenticated
    });
  }

  static delete(path: string, authenticated = true): Endpoint {
    return new Endpoint({
      path,
      method: 'DELETE',
      authenticated
    });
  }

  // Utility method to generate OpenAPI specification
  public toOpenAPI(): object {
    const operation: any = {
      summary: `${this.method} ${this.path}`,
      operationId: `${this.method.toLowerCase()}${this.path.replace(/[^a-zA-Z0-9]/g, '')}`,
      parameters: [],
      responses: {
        '200': {
          description: 'Successful response'
        }
      }
    };

    // Add path parameters
    const pathParams = this.getPathParameters();
    pathParams.forEach(param => {
      operation.parameters.push({
        name: param,
        in: 'path',
        required: true,
        schema: { type: 'string' }
      });
    });

    // Add request body for write operations
    if (this.requiresRequestBody() && this.requestSchema) {
      operation.requestBody = {
        required: true,
        content: {
          'application/json': {
            schema: this.requestSchema
          }
        }
      };
    }

    // Add response schema
    if (this.responseSchema) {
      operation.responses['200'].content = {
        'application/json': {
          schema: this.responseSchema
        }
      };
    }

    // Add security for authenticated endpoints
    if (this.authenticated) {
      operation.security = [{ bearerAuth: [] }];
    }

    return operation;
  }
}

// Export schema for external use
export { EndpointSchema };