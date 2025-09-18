import React from 'react';
import { z } from 'zod';

// ComponentProp validation schema
const ComponentPropSchema = z.object({
  name: z.string().regex(
    /^[a-zA-Z_$][a-zA-Z0-9_$]*$/,
    'Property name must be a valid JavaScript identifier'
  ),
  type: z.string().min(1, 'TypeScript type is required'),
  required: z.boolean(),
  defaultValue: z.any().optional(),
  description: z.string().optional()
});

// Platform validation schema
const PlatformSchema = z.object({
  name: z.enum(['web', 'mobile']),
  styling: z.enum(['tailwind', 'stylesheet']),
  imports: z.array(z.string()).default([]),
  adapters: z.array(z.string()).default([])
});

// UIComponent validation schema
const UIComponentSchema = z.object({
  name: z.string().regex(
    /^[A-Z][a-zA-Z0-9]*$/,
    'Component name must be PascalCase'
  ),
  props: z.array(ComponentPropSchema).default([]),
  platforms: z.array(PlatformSchema).min(1, 'At least one platform is required'),
  variants: z.array(z.string()).default([]),
  dependencies: z.array(z.string()).default([])
});

// TypeScript types
export type ComponentPropData = z.infer<typeof ComponentPropSchema>;
export type PlatformData = z.infer<typeof PlatformSchema>;
export type UIComponentData = z.infer<typeof UIComponentSchema>;

// Base props interface for UI components
export interface UIComponentProps {
  className?: string;
  style?: React.CSSProperties | object;
  children?: React.ReactNode;
}

// UIComponent class
export class UIComponent {
  public readonly name: string;
  public readonly props: ComponentPropData[];
  public readonly platforms: PlatformData[];
  public readonly variants: string[];
  public readonly dependencies: string[];

  constructor(data: UIComponentData) {
    // Validate input data
    const validatedData = UIComponentSchema.parse(data);

    // Additional validation
    this.validatePlatforms(validatedData.platforms);

    this.name = validatedData.name;
    this.props = validatedData.props;
    this.platforms = validatedData.platforms;
    this.variants = validatedData.variants;
    this.dependencies = validatedData.dependencies;
  }

  private validatePlatforms(platforms: PlatformData[]): void {
    // Validate platform names
    platforms.forEach(platform => {
      if (!['web', 'mobile'].includes(platform.name)) {
        throw new Error('Platform name must be web or mobile');
      }
    });

    // Validate styling approach per platform
    const webPlatforms = platforms.filter(p => p.name === 'web');
    const mobilePlatforms = platforms.filter(p => p.name === 'mobile');

    webPlatforms.forEach(platform => {
      if (platform.styling !== 'tailwind') {
        throw new Error('Web platforms should use tailwind styling');
      }
    });

    mobilePlatforms.forEach(platform => {
      if (platform.styling !== 'stylesheet') {
        throw new Error('Mobile platforms should use stylesheet styling');
      }
    });
  }

  // Helper methods
  public supportsWeb(): boolean {
    return this.platforms.some(platform => platform.name === 'web');
  }

  public supportsMobile(): boolean {
    return this.platforms.some(platform => platform.name === 'mobile');
  }

  public isUniversal(): boolean {
    return this.supportsWeb() && this.supportsMobile();
  }

  public getRequiredProps(): ComponentPropData[] {
    return this.props.filter(prop => prop.required);
  }

  public getOptionalProps(): ComponentPropData[] {
    return this.props.filter(prop => !prop.required);
  }

  public getProp(name: string): ComponentPropData | undefined {
    return this.props.find(prop => prop.name === name);
  }

  public hasProp(name: string): boolean {
    return this.getProp(name) !== undefined;
  }

  public getPlatform(name: 'web' | 'mobile'): PlatformData | undefined {
    return this.platforms.find(platform => platform.name === name);
  }

  public getWebPlatform(): PlatformData | undefined {
    return this.getPlatform('web');
  }

  public getMobilePlatform(): PlatformData | undefined {
    return this.getPlatform('mobile');
  }

  public hasVariant(variant: string): boolean {
    return this.variants.includes(variant);
  }

  public addProp(prop: ComponentPropData): UIComponent {
    // Validate prop name doesn't already exist
    if (this.hasProp(prop.name)) {
      throw new Error(`Property '${prop.name}' already exists`);
    }

    const newProps = [...this.props, prop];
    return new UIComponent({
      name: this.name,
      props: newProps,
      platforms: this.platforms,
      variants: this.variants,
      dependencies: this.dependencies
    });
  }

  public addVariant(variant: string): UIComponent {
    if (this.hasVariant(variant)) {
      return this;
    }

    const newVariants = [...this.variants, variant];
    return new UIComponent({
      name: this.name,
      props: this.props,
      platforms: this.platforms,
      variants: newVariants,
      dependencies: this.dependencies
    });
  }

  public addPlatform(platform: PlatformData): UIComponent {
    // Check if platform already exists
    if (this.getPlatform(platform.name)) {
      throw new Error(`Platform '${platform.name}' already exists`);
    }

    const newPlatforms = [...this.platforms, platform];
    return new UIComponent({
      name: this.name,
      props: this.props,
      platforms: newPlatforms,
      variants: this.variants,
      dependencies: this.dependencies
    });
  }

  public toJSON(): UIComponentData {
    return {
      name: this.name,
      props: this.props,
      platforms: this.platforms,
      variants: this.variants,
      dependencies: this.dependencies
    };
  }

  // Static factory methods
  static fromJSON(data: UIComponentData): UIComponent {
    return new UIComponent(data);
  }

  static validate(data: unknown): UIComponentData {
    return UIComponentSchema.parse(data);
  }

  // Builder pattern
  static create(name: string): UIComponentBuilder {
    return new UIComponentBuilder(name);
  }

  // Generate TypeScript interface
  public generateTypeScriptInterface(): string {
    const interfaceName = `${this.name}Props`;
    const props = this.props.map(prop => {
      const optional = prop.required ? '' : '?';
      return `  ${prop.name}${optional}: ${prop.type};`;
    }).join('\n');

    return `export interface ${interfaceName} {\n${props}\n}`;
  }

  // Generate Storybook story template
  public generateStorybookStory(): string {
    const defaultProps = this.props.reduce((acc, prop) => {
      if (prop.defaultValue !== undefined) {
        acc[prop.name] = prop.defaultValue;
      }
      return acc;
    }, {} as Record<string, any>);

    return `
import type { Meta, StoryObj } from '@storybook/react';
import { ${this.name} } from './${this.name}';

const meta: Meta<typeof ${this.name}> = {
  title: 'Components/${this.name}',
  component: ${this.name},
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: ${JSON.stringify(defaultProps, null, 2)},
};

${this.variants.map(variant => `
export const ${variant.charAt(0).toUpperCase() + variant.slice(1)}: Story = {
  args: {
    ...Default.args,
    variant: '${variant}',
  },
};`).join('')}
`;
  }
}

// Builder class for easier UIComponent construction
export class UIComponentBuilder {
  private name: string;
  private props: ComponentPropData[] = [];
  private platforms: PlatformData[] = [];
  private variants: string[] = [];
  private dependencies: string[] = [];

  constructor(name: string) {
    this.name = name;
  }

  public addProp(
    name: string,
    type: string,
    required = false,
    defaultValue?: any,
    description?: string
  ): UIComponentBuilder {
    this.props.push({
      name,
      type,
      required,
      defaultValue,
      description
    });
    return this;
  }

  public addWebPlatform(imports: string[] = [], adapters: string[] = []): UIComponentBuilder {
    this.platforms.push({
      name: 'web',
      styling: 'tailwind',
      imports,
      adapters
    });
    return this;
  }

  public addMobilePlatform(imports: string[] = [], adapters: string[] = []): UIComponentBuilder {
    this.platforms.push({
      name: 'mobile',
      styling: 'stylesheet',
      imports,
      adapters
    });
    return this;
  }

  public addVariant(variant: string): UIComponentBuilder {
    if (!this.variants.includes(variant)) {
      this.variants.push(variant);
    }
    return this;
  }

  public addDependency(dependency: string): UIComponentBuilder {
    if (!this.dependencies.includes(dependency)) {
      this.dependencies.push(dependency);
    }
    return this;
  }

  public build(): UIComponent {
    return new UIComponent({
      name: this.name,
      props: this.props,
      platforms: this.platforms,
      variants: this.variants,
      dependencies: this.dependencies
    });
  }
}

// Export schemas for external use
export { UIComponentSchema, ComponentPropSchema, PlatformSchema };