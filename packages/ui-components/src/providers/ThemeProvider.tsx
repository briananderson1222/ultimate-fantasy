import React, { createContext, useContext, ReactNode } from 'react';
import { designTokens, DesignTokenSystem } from '../tokens/design-tokens';

export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  spacing: {
    xs: number | string;
    sm: number | string;
    md: number | string;
    lg: number | string;
    xl: number | string;
  };
  typography: {
    h1: any;
    h2: any;
    h3: any;
    body: any;
    caption: any;
  };
  shadows: {
    sm: any;
    md: any;
    lg: any;
  };
}

export interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  platform: 'web' | 'mobile';
  toggleTheme: () => void;
  setTheme: (themeName: string) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Light theme
const lightTheme: Theme = {
  name: 'light',
  colors: {
    primary: designTokens.getColorValue('primary-blue'),
    secondary: designTokens.getColorValue('secondary-green'),
    background: designTokens.getColorValue('neutral-50'),
    surface: '#ffffff',
    text: designTokens.getColorValue('neutral-800'),
    textSecondary: designTokens.getColorValue('neutral-600'),
    border: designTokens.getColorValue('neutral-200'),
    success: designTokens.getColorValue('success-green'),
    warning: designTokens.getColorValue('warning-yellow'),
    error: designTokens.getColorValue('danger-red'),
    info: designTokens.getColorValue('info-blue'),
  },
  spacing: {
    xs: designTokens.getSpacingValue('space-1'),
    sm: designTokens.getSpacingValue('space-2'),
    md: designTokens.getSpacingValue('space-4'),
    lg: designTokens.getSpacingValue('space-6'),
    xl: designTokens.getSpacingValue('space-8'),
  },
  typography: {
    h1: designTokens.getTypographyStyle('text-3xl'),
    h2: designTokens.getTypographyStyle('text-2xl'),
    h3: designTokens.getTypographyStyle('text-xl'),
    body: designTokens.getTypographyStyle('text-base'),
    caption: designTokens.getTypographyStyle('text-sm'),
  },
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  },
};

// Dark theme
const darkTheme: Theme = {
  name: 'dark',
  colors: {
    primary: '#60a5fa', // lighter blue for dark mode
    secondary: '#34d399', // lighter green for dark mode
    background: designTokens.getColorValue('neutral-900'),
    surface: designTokens.getColorValue('neutral-800'),
    text: designTokens.getColorValue('neutral-100'),
    textSecondary: designTokens.getColorValue('neutral-400'),
    border: designTokens.getColorValue('neutral-700'),
    success: '#10b981',
    warning: '#f59e0b',
    error: '#f87171',
    info: '#38bdf8',
  },
  spacing: {
    xs: designTokens.getSpacingValue('space-1'),
    sm: designTokens.getSpacingValue('space-2'),
    md: designTokens.getSpacingValue('space-4'),
    lg: designTokens.getSpacingValue('space-6'),
    xl: designTokens.getSpacingValue('space-8'),
  },
  typography: {
    h1: designTokens.getTypographyStyle('text-3xl'),
    h2: designTokens.getTypographyStyle('text-2xl'),
    h3: designTokens.getTypographyStyle('text-xl'),
    body: designTokens.getTypographyStyle('text-base'),
    caption: designTokens.getTypographyStyle('text-sm'),
  },
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px rgba(0, 0, 0, 0.4)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.5)',
  },
};

export interface ThemeProviderProps {
  children: ReactNode;
  initialTheme?: 'light' | 'dark';
  platform?: 'web' | 'mobile';
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  initialTheme = 'light',
  platform = 'web'
}) => {
  const [currentTheme, setCurrentTheme] = React.useState<'light' | 'dark'>(initialTheme);

  const theme = currentTheme === 'dark' ? darkTheme : lightTheme;
  const isDark = currentTheme === 'dark';

  const toggleTheme = React.useCallback(() => {
    setCurrentTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, []);

  const setTheme = React.useCallback((themeName: string) => {
    if (themeName === 'light' || themeName === 'dark') {
      setCurrentTheme(themeName);
    }
  }, []);

  const contextValue = React.useMemo(() => ({
    theme,
    isDark,
    platform,
    toggleTheme,
    setTheme,
  }), [theme, isDark, platform, toggleTheme, setTheme]);

  // Apply theme to body for web
  React.useEffect(() => {
    if (platform === 'web' && typeof document !== 'undefined') {
      const root = document.documentElement;

      // Set CSS custom properties for the theme
      root.style.setProperty('--uf-color-primary', theme.colors.primary);
      root.style.setProperty('--uf-color-secondary', theme.colors.secondary);
      root.style.setProperty('--uf-color-background', theme.colors.background);
      root.style.setProperty('--uf-color-surface', theme.colors.surface);
      root.style.setProperty('--uf-color-text', theme.colors.text);
      root.style.setProperty('--uf-color-text-secondary', theme.colors.textSecondary);
      root.style.setProperty('--uf-color-border', theme.colors.border);
      root.style.setProperty('--uf-color-success', theme.colors.success);
      root.style.setProperty('--uf-color-warning', theme.colors.warning);
      root.style.setProperty('--uf-color-error', theme.colors.error);
      root.style.setProperty('--uf-color-info', theme.colors.info);

      // Set data attribute for theme-based styling
      root.setAttribute('data-theme', currentTheme);

      // Set background color
      document.body.style.backgroundColor = theme.colors.background;
      document.body.style.color = theme.colors.text;
    }
  }, [theme, currentTheme, platform]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Higher-order component for theme injection
export function withTheme<P extends object>(
  Component: React.ComponentType<P & { theme: Theme }>
): React.FC<P> {
  return (props: P) => {
    const { theme } = useTheme();
    return <Component {...props} theme={theme} />;
  };
}

// Hook for responsive design
export const useResponsive = () => {
  const { platform } = useTheme();
  const [dimensions, setDimensions] = React.useState({
    width: 0,
    height: 0,
    isMobile: platform === 'mobile'
  });

  React.useEffect(() => {
    if (platform === 'web' && typeof window !== 'undefined') {
      const updateDimensions = () => {
        setDimensions({
          width: window.innerWidth,
          height: window.innerHeight,
          isMobile: window.innerWidth < 768
        });
      };

      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    } else if (platform === 'mobile') {
      // For React Native, you would use Dimensions from react-native
      try {
        const { Dimensions } = require('react-native');
        const { width, height } = Dimensions.get('window');
        setDimensions({ width, height, isMobile: true });
      } catch {
        // Fallback if react-native is not available
        setDimensions({ width: 375, height: 667, isMobile: true });
      }
    }
  }, [platform]);

  return {
    ...dimensions,
    isTablet: dimensions.width >= 768 && dimensions.width < 1024,
    isDesktop: dimensions.width >= 1024,
    breakpoint: dimensions.width < 768 ? 'mobile' :
                dimensions.width < 1024 ? 'tablet' : 'desktop'
  };
};

// Utility functions for theme-aware styling
export const createThemedStyles = (styleFunction: (theme: Theme) => any) => {
  return () => {
    const { theme } = useTheme();
    return React.useMemo(() => styleFunction(theme), [theme]);
  };
};

// Theme-aware color utility
export const useThemedColor = (colorKey: keyof Theme['colors']) => {
  const { theme } = useTheme();
  return theme.colors[colorKey];
};

// Theme-aware spacing utility
export const useThemedSpacing = (spacingKey: keyof Theme['spacing']) => {
  const { theme } = useTheme();
  return theme.spacing[spacingKey];
};

export default ThemeProvider;