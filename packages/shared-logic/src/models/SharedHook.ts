import { z } from 'zod';

// Hook parameter validation schema
const HookParameterSchema = z.object({
  name: z.string()
    .min(1, 'Parameter name is required')
    .regex(/^[a-zA-Z_$][a-zA-Z0-9_$]*$/, 'Parameter name must be a valid JavaScript identifier'),
  type: z.string().min(1, 'Parameter type is required'),
  optional: z.boolean().default(false),
  defaultValue: z.any().optional(),
  description: z.string().optional()
});

// Hook return value validation schema
const HookReturnSchema = z.object({
  type: z.string().min(1, 'Return type is required'),
  description: z.string().optional(),
  properties: z.array(z.object({
    name: z.string(),
    type: z.string(),
    description: z.string().optional()
  })).default([])
});

// SharedHook validation schema
const SharedHookSchema = z.object({
  name: z.string().regex(
    /^use[A-Z][a-zA-Z0-9]*$/,
    'Hook name must start with "use" followed by a capital letter'
  ),
  description: z.string().min(1, 'Hook description is required'),
  category: z.enum(['state', 'api', 'utility', 'ui', 'form', 'navigation', 'data']),
  platform: z.literal('universal'),
  parameters: z.array(HookParameterSchema).default([]),
  returns: HookReturnSchema,
  dependencies: z.array(z.string()).default([]),
  examples: z.array(z.string()).default([]),
  deprecated: z.boolean().default(false),
  version: z.string().regex(
    /^\d+\.\d+\.\d+$/,
    'Version must follow semantic versioning (MAJOR.MINOR.PATCH)'
  ).default('1.0.0')
});

// TypeScript types
export type HookParameter = z.infer<typeof HookParameterSchema>;
export type HookReturn = z.infer<typeof HookReturnSchema>;
export type SharedHookData = z.infer<typeof SharedHookSchema>;

// SharedHook class
export class SharedHook {
  public readonly name: string;
  public readonly description: string;
  public readonly category: 'state' | 'api' | 'utility' | 'ui' | 'form' | 'navigation' | 'data';
  public readonly platform: 'universal';
  public readonly parameters: HookParameter[];
  public readonly returns: HookReturn;
  public readonly dependencies: string[];
  public readonly examples: string[];
  public readonly deprecated: boolean;
  public readonly version: string;

  constructor(data: SharedHookData) {
    // Validate input data
    const validatedData = SharedHookSchema.parse(data);

    this.name = validatedData.name;
    this.description = validatedData.description;
    this.category = validatedData.category;
    this.platform = validatedData.platform;
    this.parameters = validatedData.parameters;
    this.returns = validatedData.returns;
    this.dependencies = validatedData.dependencies;
    this.examples = validatedData.examples;
    this.deprecated = validatedData.deprecated;
    this.version = validatedData.version;
  }

  // Computed properties for backward compatibility
  public get returnType(): string {
    return this.returns?.type || '';
  }

  // Helper methods
  public addParameter(parameter: HookParameter): SharedHook {
    const newParameters = [...this.parameters, parameter];
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: newParameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: this.examples,
      deprecated: this.deprecated,
      version: this.version
    });
  }

  public addDependency(dependency: string): SharedHook {
    if (this.dependencies.includes(dependency)) {
      return this;
    }

    const newDependencies = [...this.dependencies, dependency];
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: newDependencies,
      examples: this.examples,
      deprecated: this.deprecated,
      version: this.version
    });
  }

  public addExample(example: string): SharedHook {
    const newExamples = [...this.examples, example];
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: newExamples,
      deprecated: this.deprecated,
      version: this.version
    });
  }

  public markDeprecated(): SharedHook {
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: this.examples,
      deprecated: true,
      version: this.version
    });
  }

  public updateVersion(version: string): SharedHook {
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: this.examples,
      deprecated: this.deprecated,
      version
    });
  }

  public getParametersByOptional(optional: boolean): HookParameter[] {
    return this.parameters.filter(param => param.optional === optional);
  }

  public getRequiredParameters(): HookParameter[] {
    return this.getParametersByOptional(false);
  }

  public getOptionalParameters(): HookParameter[] {
    return this.getParametersByOptional(true);
  }

  public hasParameter(parameterName: string): boolean {
    return this.parameters.some(param => param.name === parameterName);
  }

  public getParameter(parameterName: string): HookParameter | undefined {
    return this.parameters.find(param => param.name === parameterName);
  }

  public generateTypeScriptSignature(): string {
    const paramStrings = this.parameters.map(param => {
      const optional = param.optional ? '?' : '';
      const defaultVal = param.defaultValue !== undefined ? ` = ${JSON.stringify(param.defaultValue)}` : '';
      return `${param.name}${optional}: ${param.type}${defaultVal}`;
    });

    const paramString = paramStrings.length > 0 ? `(${paramStrings.join(', ')})` : '()';
    return `${this.name}${paramString}: ${this.returns.type}`;
  }

  public generateDocumentation(): string {
    let doc = `/**\n * ${this.description}\n *\n`;

    if (this.parameters.length > 0) {
      doc += ' * @param options - Hook options\n';
      this.parameters.forEach(param => {
        const description = param.description || 'No description';
        doc += ` * @param options.${param.name} - ${description}\n`;
      });
      doc += ' *\n';
    }

    doc += ` * @returns ${this.returns.description || this.returns.type}\n`;

    if (this.examples.length > 0) {
      doc += ' *\n * @example\n';
      this.examples.forEach(example => {
        doc += ` * ${example}\n`;
      });
    }

    if (this.deprecated) {
      doc += ' *\n * @deprecated\n';
    }

    doc += ' */';
    return doc;
  }

  public toJSON(): SharedHookData {
    return {
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: this.examples,
      deprecated: this.deprecated,
      version: this.version
    };
  }

  // Static factory methods
  static fromJSON(data: SharedHookData): SharedHook {
    return new SharedHook(data);
  }

  static validate(data: unknown): SharedHookData {
    return SharedHookSchema.parse(data);
  }

  // Builder pattern methods
  static create(name: string, description: string): SharedHookBuilder {
    return new SharedHookBuilder(name, description);
  }
}

// Builder class for easier SharedHook construction
export class SharedHookBuilder {
  private name: string;
  private description: string;
  private category: SharedHookData['category'] = 'utility';
  private platform: SharedHookData['platform'] = 'universal';
  private parameters: HookParameter[] = [];
  private returns: HookReturn = { type: 'void', properties: [] };
  private dependencies: string[] = [];
  private examples: string[] = [];
  private deprecated: boolean = false;
  private version: string = '1.0.0';

  constructor(name: string, description: string) {
    this.name = name;
    this.description = description;
  }

  public withCategory(category: SharedHookData['category']): SharedHookBuilder {
    this.category = category;
    return this;
  }

  public withPlatform(platform: SharedHookData['platform']): SharedHookBuilder {
    this.platform = platform;
    return this;
  }

  public addParameter(
    name: string,
    type: string,
    options: {
      optional?: boolean;
      defaultValue?: any;
      description?: string;
    } = {}
  ): SharedHookBuilder {
    const parameter: HookParameter = {
      name,
      type,
      optional: options.optional || false,
      defaultValue: options.defaultValue,
      description: options.description
    };

    this.parameters.push(parameter);
    return this;
  }

  public withReturnType(
    type: string,
    description?: string,
    properties: Array<{ name: string; type: string; description?: string }> = []
  ): SharedHookBuilder {
    this.returns = {
      type,
      description,
      properties
    };
    return this;
  }

  public addDependency(dependency: string): SharedHookBuilder {
    if (!this.dependencies.includes(dependency)) {
      this.dependencies.push(dependency);
    }
    return this;
  }

  public addExample(example: string): SharedHookBuilder {
    this.examples.push(example);
    return this;
  }

  public markDeprecated(): SharedHookBuilder {
    this.deprecated = true;
    return this;
  }

  public withVersion(version: string): SharedHookBuilder {
    this.version = version;
    return this;
  }

  public build(): SharedHook {
    return new SharedHook({
      name: this.name,
      description: this.description,
      category: this.category,
      platform: this.platform,
      parameters: this.parameters,
      returns: this.returns,
      dependencies: this.dependencies,
      examples: this.examples,
      deprecated: this.deprecated,
      version: this.version
    });
  }
}

// Export schemas for external use
export { SharedHookSchema, HookParameterSchema, HookReturnSchema };

// Common hook patterns
export const commonHookPatterns = {
  stateHook: (name: string, stateType: string) =>
    SharedHook.create(name, `Hook for managing ${stateType} state`)
      .withCategory('state')
      .withReturnType(`[${stateType}, (value: ${stateType}) => void]`, 'State value and setter function')
      .addExample(`const [value, setValue] = ${name}();`),

  apiHook: (name: string, dataType: string) =>
    SharedHook.create(name, `Hook for fetching ${dataType} from API`)
      .withCategory('api')
      .withReturnType(`{ data: ${dataType} | null; loading: boolean; error: Error | null; refetch: () => void }`, 'API state and actions')
      .addExample(`const { data, loading, error, refetch } = ${name}();`),

  utilityHook: (name: string, returnType: string) =>
    SharedHook.create(name, `Utility hook`)
      .withCategory('utility')
      .withReturnType(returnType, 'Utility function or value')
};