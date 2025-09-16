import { z } from 'zod';

// Package export item validation schema
const PackageExportSchema = z.object({
  name: z.string().regex(/^[a-zA-Z_$][a-zA-Z0-9_$]*$/, 'Export name must be a valid JavaScript identifier'),
  type: z.enum(['function', 'component', 'hook', 'constant', 'type']),
  signature: z.string().min(1, 'TypeScript signature is required'),
  platform: z.enum(['shared', 'web', 'mobile', 'universal']),
  deprecated: z.boolean().default(false)
});

// SharedPackage validation schema
const SharedPackageSchema = z.object({
  name: z.string().regex(
    /^[@a-z0-9-~][a-z0-9-._~]*\/[a-z0-9-._~]*$/,
    'Package name must follow npm conventions'
  ),
  version: z.string().regex(
    /^\d+\.\d+\.\d+$/,
    'Version must follow semantic versioning (MAJOR.MINOR.PATCH)'
  ),
  platform: z.enum(['shared', 'web', 'mobile', 'universal']),
  dependencies: z.array(z.string()).default([]),
  exports: z.array(PackageExportSchema).default([])
});

// TypeScript types
export type PackageExportType = z.infer<typeof PackageExportSchema>;
export type SharedPackageData = z.infer<typeof SharedPackageSchema>;

// SharedPackage class
export class SharedPackage {
  public readonly name: string;
  public readonly version: string;
  public readonly platform: 'shared' | 'web' | 'mobile' | 'universal';
  public readonly dependencies: string[];
  public readonly exports: PackageExportType[];

  constructor(data: SharedPackageData) {
    // Validate input data
    const validatedData = SharedPackageSchema.parse(data);

    this.name = validatedData.name;
    this.version = validatedData.version;
    this.platform = validatedData.platform;
    this.dependencies = validatedData.dependencies;
    this.exports = validatedData.exports;
  }

  // Helper methods
  public addExport(exportItem: PackageExportType): SharedPackage {
    const newExports = [...this.exports, exportItem];
    return new SharedPackage({
      name: this.name,
      version: this.version,
      platform: this.platform,
      dependencies: this.dependencies,
      exports: newExports
    });
  }

  public addDependency(dependency: string): SharedPackage {
    if (this.dependencies.includes(dependency)) {
      return this;
    }

    const newDependencies = [...this.dependencies, dependency];
    return new SharedPackage({
      name: this.name,
      version: this.version,
      platform: this.platform,
      dependencies: newDependencies,
      exports: this.exports
    });
  }

  public getExportsByType(type: PackageExportType['type']): PackageExportType[] {
    return this.exports.filter(exp => exp.type === type);
  }

  public getExportsByPlatform(platform: PackageExportType['platform']): PackageExportType[] {
    return this.exports.filter(exp => exp.platform === platform || exp.platform === 'universal');
  }

  public toJSON(): SharedPackageData {
    return {
      name: this.name,
      version: this.version,
      platform: this.platform,
      dependencies: this.dependencies,
      exports: this.exports
    };
  }

  // Static factory methods
  static fromJSON(data: SharedPackageData): SharedPackage {
    return new SharedPackage(data);
  }

  static validate(data: unknown): SharedPackageData {
    return SharedPackageSchema.parse(data);
  }
}

// Export schemas for external use
export { SharedPackageSchema, PackageExportSchema };