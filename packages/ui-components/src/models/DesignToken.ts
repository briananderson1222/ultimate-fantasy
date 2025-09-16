import { z } from 'zod';

// Design token validation schema
const DesignTokenSchema = z.object({
  name: z.string().regex(
    /^[a-z][a-z0-9-]*$/,
    'Token name must be kebab-case'
  ),
  category: z.enum(['color', 'spacing', 'typography', 'shadow']),
  value: z.any(),
  webValue: z.any().optional(),
  mobileValue: z.any().optional()
});

// TypeScript type
export type DesignTokenData = z.infer<typeof DesignTokenSchema>;

// Token category types
export type TokenCategory = 'color' | 'spacing' | 'typography' | 'shadow';

// Platform-specific value types
export interface ColorValue {
  hex?: string;
  rgb?: { r: number; g: number; b: number };
  hsl?: { h: number; s: number; l: number };
  css?: string;
  native?: number; // React Native color
}

export interface SpacingValue {
  px?: number;
  rem?: number;
  em?: number;
  points?: number; // React Native points
}

export interface TypographyValue {
  fontSize?: SpacingValue;
  fontWeight?: string | number;
  lineHeight?: number;
  fontFamily?: string;
  letterSpacing?: number;
}

export interface ShadowValue {
  offsetX?: number;
  offsetY?: number;
  blurRadius?: number;
  spreadRadius?: number;
  color?: ColorValue;
  elevation?: number; // Android elevation
}

// DesignToken class
export class DesignToken {
  public readonly name: string;
  public readonly category: TokenCategory;
  public readonly value: any;
  public readonly webValue?: any;
  public readonly mobileValue?: any;

  constructor(data: DesignTokenData) {
    // Validate input data
    const validatedData = DesignTokenSchema.parse(data);

    this.name = validatedData.name;
    this.category = validatedData.category;
    this.value = validatedData.value;
    this.webValue = validatedData.webValue;
    this.mobileValue = validatedData.mobileValue;

    // Validate category-specific value structure
    this.validateCategoryValue();
  }

  private validateCategoryValue(): void {
    switch (this.category) {
      case 'color':
        this.validateColorValue();
        break;
      case 'spacing':
        this.validateSpacingValue();
        break;
      case 'typography':
        this.validateTypographyValue();
        break;
      case 'shadow':
        this.validateShadowValue();
        break;
    }
  }

  private validateColorValue(): void {
    if (typeof this.value === 'string') {
      // Simple hex/css color
      return;
    }

    if (typeof this.value === 'object') {
      const colorValue = this.value as ColorValue;
      if (!colorValue.hex && !colorValue.rgb && !colorValue.hsl && !colorValue.css) {
        throw new Error('Color token must have at least one color format');
      }
    }
  }

  private validateSpacingValue(): void {
    if (typeof this.value === 'number') {
      // Simple pixel value
      return;
    }

    if (typeof this.value === 'object') {
      const spacingValue = this.value as SpacingValue;
      if (!spacingValue.px && !spacingValue.rem && !spacingValue.em && !spacingValue.points) {
        throw new Error('Spacing token must have at least one unit format');
      }
    }
  }

  private validateTypographyValue(): void {
    if (typeof this.value !== 'object') {
      throw new Error('Typography token must be an object');
    }
  }

  private validateShadowValue(): void {
    if (typeof this.value !== 'object') {
      throw new Error('Shadow token must be an object');
    }
  }

  // Helper methods
  public isColor(): boolean {
    return this.category === 'color';
  }

  public isSpacing(): boolean {
    return this.category === 'spacing';
  }

  public isTypography(): boolean {
    return this.category === 'typography';
  }

  public isShadow(): boolean {
    return this.category === 'shadow';
  }

  public getValueForPlatform(platform: 'web' | 'mobile'): any {
    if (platform === 'web' && this.webValue !== undefined) {
      return this.webValue;
    }

    if (platform === 'mobile' && this.mobileValue !== undefined) {
      return this.mobileValue;
    }

    return this.value;
  }

  public getWebValue(): any {
    return this.getValueForPlatform('web');
  }

  public getMobileValue(): any {
    return this.getValueForPlatform('mobile');
  }

  // CSS generation for web
  public toCSSCustomProperty(): string {
    const webValue = this.getWebValue();

    if (this.isColor()) {
      return this.colorToCSSValue(webValue);
    }

    if (this.isSpacing()) {
      return this.spacingToCSSValue(webValue);
    }

    if (this.isTypography()) {
      return this.typographyToCSSValue(webValue);
    }

    if (this.isShadow()) {
      return this.shadowToCSSValue(webValue);
    }

    return String(webValue);
  }

  private colorToCSSValue(value: any): string {
    if (typeof value === 'string') {
      return value;
    }

    const colorValue = value as ColorValue;
    if (colorValue.css) return colorValue.css;
    if (colorValue.hex) return colorValue.hex;
    if (colorValue.rgb) {
      const { r, g, b } = colorValue.rgb;
      return `rgb(${r}, ${g}, ${b})`;
    }
    if (colorValue.hsl) {
      const { h, s, l } = colorValue.hsl;
      return `hsl(${h}, ${s}%, ${l}%)`;
    }

    return String(value);
  }

  private spacingToCSSValue(value: any): string {
    if (typeof value === 'number') {
      return `${value}px`;
    }

    const spacingValue = value as SpacingValue;
    if (spacingValue.rem) return `${spacingValue.rem}rem`;
    if (spacingValue.em) return `${spacingValue.em}em`;
    if (spacingValue.px) return `${spacingValue.px}px`;

    return String(value);
  }

  private typographyToCSSValue(value: any): string {
    const typographyValue = value as TypographyValue;
    const parts: string[] = [];

    if (typographyValue.fontWeight) {
      parts.push(String(typographyValue.fontWeight));
    }

    if (typographyValue.fontSize) {
      parts.push(this.spacingToCSSValue(typographyValue.fontSize));
    }

    if (typographyValue.lineHeight) {
      parts.push(`/ ${typographyValue.lineHeight}`);
    }

    if (typographyValue.fontFamily) {
      parts.push(typographyValue.fontFamily);
    }

    return parts.join(' ');
  }

  private shadowToCSSValue(value: any): string {
    const shadowValue = value as ShadowValue;
    const parts: string[] = [];

    parts.push(`${shadowValue.offsetX || 0}px`);
    parts.push(`${shadowValue.offsetY || 0}px`);
    parts.push(`${shadowValue.blurRadius || 0}px`);

    if (shadowValue.spreadRadius) {
      parts.push(`${shadowValue.spreadRadius}px`);
    }

    if (shadowValue.color) {
      parts.push(this.colorToCSSValue(shadowValue.color));
    }

    return parts.join(' ');
  }

  // React Native StyleSheet generation
  public toReactNativeStyle(): any {
    const mobileValue = this.getMobileValue();

    if (this.isColor()) {
      return this.colorToRNValue(mobileValue);
    }

    if (this.isSpacing()) {
      return this.spacingToRNValue(mobileValue);
    }

    if (this.isTypography()) {
      return this.typographyToRNValue(mobileValue);
    }

    if (this.isShadow()) {
      return this.shadowToRNValue(mobileValue);
    }

    return mobileValue;
  }

  private colorToRNValue(value: any): any {
    if (typeof value === 'string') {
      return value;
    }

    const colorValue = value as ColorValue;
    if (colorValue.native !== undefined) return colorValue.native;
    if (colorValue.hex) return colorValue.hex;
    if (colorValue.css) return colorValue.css;

    return value;
  }

  private spacingToRNValue(value: any): number {
    if (typeof value === 'number') {
      return value;
    }

    const spacingValue = value as SpacingValue;
    if (spacingValue.points) return spacingValue.points;
    if (spacingValue.px) return spacingValue.px;

    return 0;
  }

  private typographyToRNValue(value: any): any {
    const typographyValue = value as TypographyValue;
    const rnStyle: any = {};

    if (typographyValue.fontSize) {
      rnStyle.fontSize = this.spacingToRNValue(typographyValue.fontSize);
    }

    if (typographyValue.fontWeight) {
      rnStyle.fontWeight = typographyValue.fontWeight;
    }

    if (typographyValue.lineHeight) {
      rnStyle.lineHeight = typographyValue.lineHeight;
    }

    if (typographyValue.fontFamily) {
      rnStyle.fontFamily = typographyValue.fontFamily;
    }

    if (typographyValue.letterSpacing) {
      rnStyle.letterSpacing = typographyValue.letterSpacing;
    }

    return rnStyle;
  }

  private shadowToRNValue(value: any): any {
    const shadowValue = value as ShadowValue;

    // Android elevation
    if (shadowValue.elevation !== undefined) {
      return { elevation: shadowValue.elevation };
    }

    // iOS shadow
    const rnStyle: any = {};

    if (shadowValue.offsetX !== undefined || shadowValue.offsetY !== undefined) {
      rnStyle.shadowOffset = {
        width: shadowValue.offsetX || 0,
        height: shadowValue.offsetY || 0
      };
    }

    if (shadowValue.blurRadius !== undefined) {
      rnStyle.shadowRadius = shadowValue.blurRadius;
    }

    if (shadowValue.color) {
      rnStyle.shadowColor = this.colorToRNValue(shadowValue.color);
    }

    return rnStyle;
  }

  public toJSON(): DesignTokenData {
    return {
      name: this.name,
      category: this.category,
      value: this.value,
      webValue: this.webValue,
      mobileValue: this.mobileValue
    };
  }

  // Static factory methods
  static fromJSON(data: DesignTokenData): DesignToken {
    return new DesignToken(data);
  }

  static validate(data: unknown): DesignTokenData {
    return DesignTokenSchema.parse(data);
  }

  // Static factory methods for common token types
  static createColor(
    name: string,
    value: ColorValue | string,
    webValue?: ColorValue | string,
    mobileValue?: ColorValue | string
  ): DesignToken {
    return new DesignToken({
      name,
      category: 'color',
      value,
      webValue,
      mobileValue
    });
  }

  static createSpacing(
    name: string,
    value: SpacingValue | number,
    webValue?: SpacingValue | number,
    mobileValue?: SpacingValue | number
  ): DesignToken {
    return new DesignToken({
      name,
      category: 'spacing',
      value,
      webValue,
      mobileValue
    });
  }

  static createTypography(
    name: string,
    value: TypographyValue,
    webValue?: TypographyValue,
    mobileValue?: TypographyValue
  ): DesignToken {
    return new DesignToken({
      name,
      category: 'typography',
      value,
      webValue,
      mobileValue
    });
  }

  static createShadow(
    name: string,
    value: ShadowValue,
    webValue?: ShadowValue,
    mobileValue?: ShadowValue
  ): DesignToken {
    return new DesignToken({
      name,
      category: 'shadow',
      value,
      webValue,
      mobileValue
    });
  }
}

// Export schema for external use
export { DesignTokenSchema };