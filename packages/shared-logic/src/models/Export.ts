import { z } from 'zod';

// Export validation schema
const ExportSchema = z.object({
  name: z.string().regex(
    /^[a-zA-Z_$][a-zA-Z0-9_$]*$/,
    'Export name must be a valid JavaScript identifier'
  ),
  type: z.enum(['function', 'component', 'hook', 'constant', 'type']),
  signature: z.string().min(1, 'TypeScript signature is required'),
  platform: z.enum(['shared', 'web', 'mobile', 'universal']),
  deprecated: z.boolean().default(false)
});

// TypeScript type
export type ExportData = z.infer<typeof ExportSchema>;

// Export class
export class Export {
  public readonly name: string;
  public readonly type: 'function' | 'component' | 'hook' | 'constant' | 'type';
  public readonly signature: string;
  public readonly platform: 'shared' | 'web' | 'mobile' | 'universal';
  public readonly deprecated: boolean;

  constructor(data: ExportData) {
    // Validate input data
    const validatedData = ExportSchema.parse(data);

    this.name = validatedData.name;
    this.type = validatedData.type;
    this.signature = validatedData.signature;
    this.platform = validatedData.platform;
    this.deprecated = validatedData.deprecated;
  }

  // Helper methods
  public isFunction(): boolean {
    return this.type === 'function';
  }

  public isComponent(): boolean {
    return this.type === 'component';
  }

  public isHook(): boolean {
    return this.type === 'hook';
  }

  public isType(): boolean {
    return this.type === 'type';
  }

  public isConstant(): boolean {
    return this.type === 'constant';
  }

  public isUniversal(): boolean {
    return this.platform === 'universal';
  }

  public isCompatibleWith(platform: 'web' | 'mobile'): boolean {
    return this.platform === platform || this.platform === 'universal';
  }

  public markAsDeprecated(): Export {
    return new Export({
      name: this.name,
      type: this.type,
      signature: this.signature,
      platform: this.platform,
      deprecated: true
    });
  }

  public updateSignature(newSignature: string): Export {
    return new Export({
      name: this.name,
      type: this.type,
      signature: newSignature,
      platform: this.platform,
      deprecated: this.deprecated
    });
  }

  public toJSON(): ExportData {
    return {
      name: this.name,
      type: this.type,
      signature: this.signature,
      platform: this.platform,
      deprecated: this.deprecated
    };
  }

  // Static factory methods
  static fromJSON(data: ExportData): Export {
    return new Export(data);
  }

  static validate(data: unknown): ExportData {
    return ExportSchema.parse(data);
  }

  // Static factory methods for common export types
  static createFunction(
    name: string,
    signature: string,
    platform: 'shared' | 'web' | 'mobile' | 'universal' = 'universal'
  ): Export {
    return new Export({
      name,
      type: 'function',
      signature,
      platform,
      deprecated: false
    });
  }

  static createComponent(
    name: string,
    signature: string,
    platform: 'shared' | 'web' | 'mobile' | 'universal' = 'universal'
  ): Export {
    return new Export({
      name,
      type: 'component',
      signature,
      platform,
      deprecated: false
    });
  }

  static createHook(
    name: string,
    signature: string,
    platform: 'shared' | 'web' | 'mobile' | 'universal' = 'universal'
  ): Export {
    // Validate hook name starts with 'use'
    if (!name.startsWith('use')) {
      throw new Error('Hook name must start with "use"');
    }

    return new Export({
      name,
      type: 'hook',
      signature,
      platform,
      deprecated: false
    });
  }

  static createType(
    name: string,
    signature: string,
    platform: 'shared' | 'web' | 'mobile' | 'universal' = 'universal'
  ): Export {
    return new Export({
      name,
      type: 'type',
      signature,
      platform,
      deprecated: false
    });
  }

  static createConstant(
    name: string,
    signature: string,
    platform: 'shared' | 'web' | 'mobile' | 'universal' = 'universal'
  ): Export {
    return new Export({
      name,
      type: 'constant',
      signature,
      platform,
      deprecated: false
    });
  }
}

// Export schema for external use
export { ExportSchema };