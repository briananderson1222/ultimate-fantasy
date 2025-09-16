// Platform adapter system for cross-platform UI components

export type Platform = 'web' | 'mobile';

export interface PlatformAdapter<TWebProps = any, TMobileProps = any> {
  web: (props: TWebProps) => React.ReactElement;
  mobile: (props: TMobileProps) => React.ReactElement;
}

export interface StyleAdapter {
  web: (styles: any) => string | object;
  mobile: (styles: any) => object;
}

// Platform detection utilities
export function getPlatform(): Platform {
  // Check for React Native environment
  if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
    return 'mobile';
  }

  // Check for React Native Web
  if (typeof window !== 'undefined' && 'ReactNativeWebView' in window) {
    return 'mobile';
  }

  // Check for React Native runtime (Expo)
  if (typeof global !== 'undefined' && global.expo) {
    return 'mobile';
  }

  // Check for Metro bundler (React Native)
  if (typeof __DEV__ !== 'undefined' && typeof require !== 'undefined') {
    try {
      require('react-native');
      return 'mobile';
    } catch {
      // react-native not available, continue
    }
  }

  // Default to web
  return 'web';
}

export function isWeb(): boolean {
  return getPlatform() === 'web';
}

export function isMobile(): boolean {
  return getPlatform() === 'mobile';
}

// Component adapter factory
export function createPlatformComponent<TWebProps, TMobileProps>(
  adapter: PlatformAdapter<TWebProps, TMobileProps>
) {
  return function PlatformComponent(props: TWebProps | TMobileProps) {
    const platform = getPlatform();

    if (platform === 'web') {
      return adapter.web(props as TWebProps);
    } else {
      return adapter.mobile(props as TMobileProps);
    }
  };
}

// Style adapter for converting between Tailwind CSS and React Native StyleSheet
export class StylePlatformAdapter {
  private webClassMap: Map<string, string> = new Map();
  private mobileStyleMap: Map<string, object> = new Map();

  constructor() {
    this.initializeStyleMaps();
  }

  private initializeStyleMaps(): void {
    // Common style mappings between Tailwind and React Native
    this.webClassMap.set('flex', 'flex');
    this.webClassMap.set('flex-row', 'flex flex-row');
    this.webClassMap.set('flex-col', 'flex flex-col');
    this.webClassMap.set('justify-center', 'justify-center');
    this.webClassMap.set('items-center', 'items-center');
    this.webClassMap.set('p-4', 'p-4');
    this.webClassMap.set('m-4', 'm-4');
    this.webClassMap.set('bg-blue-500', 'bg-blue-500');
    this.webClassMap.set('text-white', 'text-white');
    this.webClassMap.set('rounded', 'rounded');
    this.webClassMap.set('shadow', 'shadow');

    this.mobileStyleMap.set('flex', { display: 'flex' });
    this.mobileStyleMap.set('flex-row', { flexDirection: 'row' });
    this.mobileStyleMap.set('flex-col', { flexDirection: 'column' });
    this.mobileStyleMap.set('justify-center', { justifyContent: 'center' });
    this.mobileStyleMap.set('items-center', { alignItems: 'center' });
    this.mobileStyleMap.set('p-4', { padding: 16 });
    this.mobileStyleMap.set('m-4', { margin: 16 });
    this.mobileStyleMap.set('bg-blue-500', { backgroundColor: '#3B82F6' });
    this.mobileStyleMap.set('text-white', { color: '#FFFFFF' });
    this.mobileStyleMap.set('rounded', { borderRadius: 4 });
    this.mobileStyleMap.set('shadow', { elevation: 2, shadowOpacity: 0.1 });
  }

  adaptStylesForWeb(styles: string[] | object): string {
    if (Array.isArray(styles)) {
      return styles
        .map(style => this.webClassMap.get(style) || style)
        .join(' ');
    }

    // If it's already a CSS class string, return as-is
    if (typeof styles === 'string') {
      return styles;
    }

    // Convert object styles to Tailwind classes (basic implementation)
    return '';
  }

  adaptStylesForMobile(styles: string[] | object): object {
    if (Array.isArray(styles)) {
      return styles.reduce((acc, style) => {
        const mobileStyle = this.mobileStyleMap.get(style);
        if (mobileStyle) {
          return { ...acc, ...mobileStyle };
        }
        return acc;
      }, {});
    }

    if (typeof styles === 'object') {
      return styles;
    }

    // Convert CSS class string to React Native styles (basic implementation)
    if (typeof styles === 'string') {
      const classList = styles.split(' ');
      return this.adaptStylesForMobile(classList);
    }

    return {};
  }
}

// Singleton style adapter
export const styleAdapter = new StylePlatformAdapter();

// Event adapter for handling different event patterns
export class EventAdapter {
  static adaptClickEvent(webOnClick?: () => void, mobileOnPress?: () => void) {
    return {
      onClick: webOnClick,
      onPress: mobileOnPress || webOnClick, // Fallback to onClick for mobile
    };
  }

  static adaptTouchEvents(
    webEvents?: {
      onMouseDown?: () => void;
      onMouseUp?: () => void;
      onMouseMove?: () => void;
    },
    mobileEvents?: {
      onTouchStart?: () => void;
      onTouchEnd?: () => void;
      onTouchMove?: () => void;
    }
  ) {
    return {
      // Web events
      onMouseDown: webEvents?.onMouseDown,
      onMouseUp: webEvents?.onMouseUp,
      onMouseMove: webEvents?.onMouseMove,
      // Mobile events
      onTouchStart: mobileEvents?.onTouchStart,
      onTouchEnd: mobileEvents?.onTouchEnd,
      onTouchMove: mobileEvents?.onTouchMove,
    };
  }
}

// Navigation adapter for different routing systems
export interface NavigationAdapter {
  navigate: (path: string, params?: Record<string, any>) => void;
  goBack: () => void;
  replace: (path: string, params?: Record<string, any>) => void;
}

export function createWebNavigationAdapter(router: any): NavigationAdapter {
  return {
    navigate: (path: string, params?: Record<string, any>) => {
      if (params) {
        const searchParams = new URLSearchParams(params as Record<string, string>);
        router.push(`${path}?${searchParams.toString()}`);
      } else {
        router.push(path);
      }
    },
    goBack: () => router.back(),
    replace: (path: string, params?: Record<string, any>) => {
      if (params) {
        const searchParams = new URLSearchParams(params as Record<string, string>);
        router.replace(`${path}?${searchParams.toString()}`);
      } else {
        router.replace(path);
      }
    },
  };
}

export function createMobileNavigationAdapter(navigation: any): NavigationAdapter {
  return {
    navigate: (path: string, params?: Record<string, any>) => {
      navigation.navigate(path, params);
    },
    goBack: () => navigation.goBack(),
    replace: (path: string, params?: Record<string, any>) => {
      navigation.replace(path, params);
    },
  };
}

// Component props adapter for handling platform-specific props
export function adaptProps<TWebProps, TMobileProps>(
  props: TWebProps | TMobileProps,
  webAdapter?: (props: TWebProps | TMobileProps) => TWebProps,
  mobileAdapter?: (props: TWebProps | TMobileProps) => TMobileProps
): TWebProps | TMobileProps {
  const platform = getPlatform();

  if (platform === 'web' && webAdapter) {
    return webAdapter(props);
  }

  if (platform === 'mobile' && mobileAdapter) {
    return mobileAdapter(props);
  }

  return props;
}

// Higher-order component for platform adaptation
export function withPlatformAdapter<TWebProps, TMobileProps>(
  WebComponent: React.ComponentType<TWebProps>,
  MobileComponent: React.ComponentType<TMobileProps>,
  propsAdapter?: {
    web?: (props: any) => TWebProps;
    mobile?: (props: any) => TMobileProps;
  }
) {
  return function AdaptedComponent(props: TWebProps | TMobileProps) {
    const platform = getPlatform();

    if (platform === 'web') {
      const adaptedProps = propsAdapter?.web ? propsAdapter.web(props) : (props as TWebProps);
      return React.createElement(WebComponent, adaptedProps);
    } else {
      const adaptedProps = propsAdapter?.mobile ? propsAdapter.mobile(props) : (props as TMobileProps);
      return React.createElement(MobileComponent, adaptedProps);
    }
  };
}

// Singleton platform adapter instance
export class PlatformAdapter {
  private static instance: PlatformAdapter;
  private currentPlatform: Platform;

  private constructor() {
    this.currentPlatform = getPlatform();
  }

  static getInstance(): PlatformAdapter {
    if (!PlatformAdapter.instance) {
      PlatformAdapter.instance = new PlatformAdapter();
    }
    return PlatformAdapter.instance;
  }

  static getCurrentPlatform(): Platform {
    return PlatformAdapter.getInstance().currentPlatform;
  }

  static isWeb(): boolean {
    return PlatformAdapter.getCurrentPlatform() === 'web';
  }

  static isMobile(): boolean {
    return PlatformAdapter.getCurrentPlatform() === 'mobile';
  }

  // Force platform for testing
  static setPlatform(platform: Platform): void {
    PlatformAdapter.getInstance().currentPlatform = platform;
  }
}

// Export utility functions
export { EventAdapter };