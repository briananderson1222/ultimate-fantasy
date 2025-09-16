import { DesignToken } from '../models/DesignToken';

// Design system tokens for Ultimate Fantasy platform
export class DesignTokenSystem {
  private tokens: Map<string, DesignToken> = new Map();

  constructor() {
    this.initializeTokens();
  }

  private initializeTokens(): void {
    // Color tokens
    this.addToken(DesignToken.createColor('primary-blue', '#1D4ED8', '#1D4ED8', '#1D4ED8'));
    this.addToken(DesignToken.createColor('primary-blue-light', '#3B82F6', '#3B82F6', '#3B82F6'));
    this.addToken(DesignToken.createColor('primary-blue-dark', '#1E40AF', '#1E40AF', '#1E40AF'));

    this.addToken(DesignToken.createColor('secondary-green', '#059669', '#059669', '#059669'));
    this.addToken(DesignToken.createColor('secondary-green-light', '#10B981', '#10B981', '#10B981'));
    this.addToken(DesignToken.createColor('secondary-green-dark', '#047857', '#047857', '#047857'));

    this.addToken(DesignToken.createColor('danger-red', '#DC2626', '#DC2626', '#DC2626'));
    this.addToken(DesignToken.createColor('warning-yellow', '#D97706', '#D97706', '#D97706'));
    this.addToken(DesignToken.createColor('success-green', '#059669', '#059669', '#059669'));
    this.addToken(DesignToken.createColor('info-blue', '#0284C7', '#0284C7', '#0284C7'));

    // Neutral colors
    this.addToken(DesignToken.createColor('neutral-50', '#F8FAFC', '#F8FAFC', '#F8FAFC'));
    this.addToken(DesignToken.createColor('neutral-100', '#F1F5F9', '#F1F5F9', '#F1F5F9'));
    this.addToken(DesignToken.createColor('neutral-200', '#E2E8F0', '#E2E8F0', '#E2E8F0'));
    this.addToken(DesignToken.createColor('neutral-300', '#CBD5E1', '#CBD5E1', '#CBD5E1'));
    this.addToken(DesignToken.createColor('neutral-400', '#94A3B8', '#94A3B8', '#94A3B8'));
    this.addToken(DesignToken.createColor('neutral-500', '#64748B', '#64748B', '#64748B'));
    this.addToken(DesignToken.createColor('neutral-600', '#475569', '#475569', '#475569'));
    this.addToken(DesignToken.createColor('neutral-700', '#334155', '#334155', '#334155'));
    this.addToken(DesignToken.createColor('neutral-800', '#1E293B', '#1E293B', '#1E293B'));
    this.addToken(DesignToken.createColor('neutral-900', '#0F172A', '#0F172A', '#0F172A'));

    // Spacing tokens
    this.addToken(DesignToken.createSpacing('space-1', { px: 4, rem: 0.25 }, { rem: 0.25 }, { points: 4 }));
    this.addToken(DesignToken.createSpacing('space-2', { px: 8, rem: 0.5 }, { rem: 0.5 }, { points: 8 }));
    this.addToken(DesignToken.createSpacing('space-3', { px: 12, rem: 0.75 }, { rem: 0.75 }, { points: 12 }));
    this.addToken(DesignToken.createSpacing('space-4', { px: 16, rem: 1 }, { rem: 1 }, { points: 16 }));
    this.addToken(DesignToken.createSpacing('space-5', { px: 20, rem: 1.25 }, { rem: 1.25 }, { points: 20 }));
    this.addToken(DesignToken.createSpacing('space-6', { px: 24, rem: 1.5 }, { rem: 1.5 }, { points: 24 }));
    this.addToken(DesignToken.createSpacing('space-8', { px: 32, rem: 2 }, { rem: 2 }, { points: 32 }));
    this.addToken(DesignToken.createSpacing('space-10', { px: 40, rem: 2.5 }, { rem: 2.5 }, { points: 40 }));
    this.addToken(DesignToken.createSpacing('space-12', { px: 48, rem: 3 }, { rem: 3 }, { points: 48 }));
    this.addToken(DesignToken.createSpacing('space-16', { px: 64, rem: 4 }, { rem: 4 }, { points: 64 }));

    // Typography tokens
    this.addToken(DesignToken.createTypography('text-xs', {
      fontSize: { px: 12, rem: 0.75 },
      lineHeight: 1.5,
      fontWeight: '400'
    }));

    this.addToken(DesignToken.createTypography('text-sm', {
      fontSize: { px: 14, rem: 0.875 },
      lineHeight: 1.5,
      fontWeight: '400'
    }));

    this.addToken(DesignToken.createTypography('text-base', {
      fontSize: { px: 16, rem: 1 },
      lineHeight: 1.5,
      fontWeight: '400'
    }));

    this.addToken(DesignToken.createTypography('text-lg', {
      fontSize: { px: 18, rem: 1.125 },
      lineHeight: 1.4,
      fontWeight: '400'
    }));

    this.addToken(DesignToken.createTypography('text-xl', {
      fontSize: { px: 20, rem: 1.25 },
      lineHeight: 1.4,
      fontWeight: '500'
    }));

    this.addToken(DesignToken.createTypography('text-2xl', {
      fontSize: { px: 24, rem: 1.5 },
      lineHeight: 1.3,
      fontWeight: '600'
    }));

    this.addToken(DesignToken.createTypography('text-3xl', {
      fontSize: { px: 30, rem: 1.875 },
      lineHeight: 1.2,
      fontWeight: '700'
    }));

    // Shadow tokens
    this.addToken(DesignToken.createShadow('shadow-sm', {
      offsetX: 0,
      offsetY: 1,
      blurRadius: 2,
      color: { hex: '#00000010' }
    }, {
      offsetX: 0,
      offsetY: 1,
      blurRadius: 2,
      color: '#00000010'
    }, {
      elevation: 1
    }));

    this.addToken(DesignToken.createShadow('shadow-md', {
      offsetX: 0,
      offsetY: 4,
      blurRadius: 6,
      color: { hex: '#00000015' }
    }, {
      offsetX: 0,
      offsetY: 4,
      blurRadius: 6,
      color: '#00000015'
    }, {
      elevation: 3
    }));

    this.addToken(DesignToken.createShadow('shadow-lg', {
      offsetX: 0,
      offsetY: 10,
      blurRadius: 15,
      color: { hex: '#00000020' }
    }, {
      offsetX: 0,
      offsetY: 10,
      blurRadius: 15,
      color: '#00000020'
    }, {
      elevation: 5
    }));
  }

  private addToken(token: DesignToken): void {
    this.tokens.set(token.name, token);
  }

  // Public API
  getToken(name: string): DesignToken | undefined {
    return this.tokens.get(name);
  }

  getTokenValue(name: string, platform: 'web' | 'mobile' = 'web'): any {
    const token = this.getToken(name);
    return token?.getValueForPlatform(platform);
  }

  getColorTokens(): DesignToken[] {
    return Array.from(this.tokens.values()).filter(token => token.isColor());
  }

  getSpacingTokens(): DesignToken[] {
    return Array.from(this.tokens.values()).filter(token => token.isSpacing());
  }

  getTypographyTokens(): DesignToken[] {
    return Array.from(this.tokens.values()).filter(token => token.isTypography());
  }

  getShadowTokens(): DesignToken[] {
    return Array.from(this.tokens.values()).filter(token => token.isShadow());
  }

  getAllTokens(): DesignToken[] {
    return Array.from(this.tokens.values());
  }

  // Generate CSS custom properties for web
  generateCSSCustomProperties(): string {
    const webTokens = this.getAllTokens();
    const cssProperties = webTokens.map(token => {
      const cssValue = token.toCSSCustomProperty();
      return `  --uf-${token.name}: ${cssValue};`;
    });

    return `:root {\n${cssProperties.join('\n')}\n}`;
  }

  // Generate React Native StyleSheet for mobile
  generateReactNativeStyles(): Record<string, any> {
    const mobileTokens = this.getAllTokens();
    const styles: Record<string, any> = {};

    mobileTokens.forEach(token => {
      const rnStyle = token.toReactNativeStyle();
      styles[token.name.replace(/-/g, '_')] = rnStyle;
    });

    return styles;
  }

  // Generate TypeScript type definitions
  generateTypeDefinitions(): string {
    const tokenNames = Array.from(this.tokens.keys());
    const tokenNamesType = tokenNames.map(name => `'${name}'`).join(' | ');

    return `
export type DesignTokenName = ${tokenNamesType};

export interface DesignTokens {
  ${tokenNames.map(name => `'${name}': any;`).join('\n  ')}
}
`;
  }

  // Theme support
  createThemeVariant(variantName: string, overrides: Record<string, any>): Map<string, DesignToken> {
    const variantTokens = new Map<string, DesignToken>();

    this.tokens.forEach((token, name) => {
      if (overrides[name]) {
        // Create a new token with overridden values
        const newToken = new DesignToken({
          name,
          category: token.category,
          value: overrides[name].value || token.value,
          webValue: overrides[name].webValue || token.webValue,
          mobileValue: overrides[name].mobileValue || token.mobileValue
        });
        variantTokens.set(name, newToken);
      } else {
        variantTokens.set(name, token);
      }
    });

    return variantTokens;
  }

  // Utility functions for common use cases
  getColorValue(name: string, platform: 'web' | 'mobile' = 'web'): string {
    const token = this.getToken(name);
    if (!token || !token.isColor()) {
      throw new Error(`Color token '${name}' not found`);
    }
    return token.getValueForPlatform(platform);
  }

  getSpacingValue(name: string, platform: 'web' | 'mobile' = 'web'): number | string {
    const token = this.getToken(name);
    if (!token || !token.isSpacing()) {
      throw new Error(`Spacing token '${name}' not found`);
    }
    return token.getValueForPlatform(platform);
  }

  getTypographyStyle(name: string, platform: 'web' | 'mobile' = 'web'): any {
    const token = this.getToken(name);
    if (!token || !token.isTypography()) {
      throw new Error(`Typography token '${name}' not found`);
    }

    if (platform === 'web') {
      return token.toCSSCustomProperty();
    } else {
      return token.toReactNativeStyle();
    }
  }
}

// Singleton instance
export const designTokens = new DesignTokenSystem();

// Export common token collections
export const colors = {
  primary: {
    blue: designTokens.getColorValue('primary-blue'),
    blueLight: designTokens.getColorValue('primary-blue-light'),
    blueDark: designTokens.getColorValue('primary-blue-dark'),
  },
  secondary: {
    green: designTokens.getColorValue('secondary-green'),
    greenLight: designTokens.getColorValue('secondary-green-light'),
    greenDark: designTokens.getColorValue('secondary-green-dark'),
  },
  status: {
    danger: designTokens.getColorValue('danger-red'),
    warning: designTokens.getColorValue('warning-yellow'),
    success: designTokens.getColorValue('success-green'),
    info: designTokens.getColorValue('info-blue'),
  },
  neutral: {
    50: designTokens.getColorValue('neutral-50'),
    100: designTokens.getColorValue('neutral-100'),
    200: designTokens.getColorValue('neutral-200'),
    300: designTokens.getColorValue('neutral-300'),
    400: designTokens.getColorValue('neutral-400'),
    500: designTokens.getColorValue('neutral-500'),
    600: designTokens.getColorValue('neutral-600'),
    700: designTokens.getColorValue('neutral-700'),
    800: designTokens.getColorValue('neutral-800'),
    900: designTokens.getColorValue('neutral-900'),
  },
};

export const spacing = {
  1: designTokens.getSpacingValue('space-1'),
  2: designTokens.getSpacingValue('space-2'),
  3: designTokens.getSpacingValue('space-3'),
  4: designTokens.getSpacingValue('space-4'),
  5: designTokens.getSpacingValue('space-5'),
  6: designTokens.getSpacingValue('space-6'),
  8: designTokens.getSpacingValue('space-8'),
  10: designTokens.getSpacingValue('space-10'),
  12: designTokens.getSpacingValue('space-12'),
  16: designTokens.getSpacingValue('space-16'),
};

// Export factory function for custom design systems
export function createDesignTokenSystem(): DesignTokenSystem {
  return new DesignTokenSystem();
}