import React, { useMemo, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Animated,
  Dimensions,
  StyleSheet,
  Platform,
  AppState,
  BackHandler
} from 'react-native';
import { NavigationContainer, NavigationState, PartialState } from '@react-navigation/native';
import { createBottomTabNavigator, BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { createStackNavigator, CardStyleInterpolators } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Lazy-loaded screens
const HomeScreen = React.lazy(() => import('../screens/HomeScreen'));
const LeaguesScreen = React.lazy(() => import('../screens/LeaguesScreen'));
const DashboardScreen = React.lazy(() => import('../screens/DashboardScreen'));
const AnalyticsScreen = React.lazy(() => import('../screens/AnalyticsScreen'));
const AuthScreen = React.lazy(() => import('../screens/AuthScreen'));
const DraftScreen = React.lazy(() => import('../screens/DraftScreen'));
const LineupScreen = React.lazy(() => import('../screens/LineupScreen'));
const TradesScreen = React.lazy(() => import('../screens/TradesScreen'));
const WaiverScreen = React.lazy(() => import('../screens/WaiverScreen'));
const TradeScreen = React.lazy(() => import('../screens/TradeScreen'));

const { width: screenWidth } = Dimensions.get('window');

// Enhanced Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Draft: { leagueId: string };
  Lineup: { teamId: string; week?: number };
  Trades: { leagueId: string };
  Trade: { tradeId?: string; leagueId: string };
  Waiver: { leagueId: string };
  Analytics: { timeframe?: string };
};

export type MainTabParamList = {
  Home: undefined;
  Leagues: undefined;
  Dashboard: undefined;
  Analytics: undefined;
  More: undefined;
};

interface NavigationState {
  routeNames: string[];
  index: number;
  routes: Array<{ name: string; params?: any }>;
}

// Performance-optimized lazy screen wrapper
const LazyScreen: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <React.Suspense fallback={
      <View style={styles.loadingContainer}>
        <Animated.View style={styles.loadingSpinner} />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    }>
      {children}
    </React.Suspense>
  );
};

// Custom optimized tab bar
const CustomTabBar: React.FC<BottomTabBarProps> = ({ state, descriptors, navigation }) => {
  const tabAnimations = useRef(
    state.routes.map(() => new Animated.Value(0))
  ).current;

  const indicatorAnimation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate indicator
    Animated.spring(indicatorAnimation, {
      toValue: state.index,
      useNativeDriver: true,
      tension: 100,
      friction: 8
    }).start();

    // Animate tabs
    tabAnimations.forEach((anim, index) => {
      Animated.spring(anim, {
        toValue: state.index === index ? 1 : 0,
        useNativeDriver: true,
        tension: 100,
        friction: 8
      }).start();
    });
  }, [state.index]);

  const tabWidth = screenWidth / state.routes.length;

  return (
    <View style={styles.tabBarContainer}>
      {/* Animated indicator */}
      <Animated.View
        style={[
          styles.tabIndicator,
          {
            width: tabWidth * 0.6,
            transform: [
              {
                translateX: indicatorAnimation.interpolate({
                  inputRange: state.routes.map((_, i) => i),
                  outputRange: state.routes.map((_, i) => i * tabWidth + tabWidth * 0.2),
                })
              }
            ]
          }
        ]}
      />

      {state.routes.map((route, index) => {
        const { options } = descriptors[route.key];
        const label = options.tabBarLabel !== undefined
          ? options.tabBarLabel
          : options.title !== undefined
          ? options.title
          : route.name;

        const isFocused = state.index === index;

        const onPress = useCallback(() => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });

          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        }, [isFocused, navigation, route.key, route.name]);

        const onLongPress = useCallback(() => {
          navigation.emit({
            type: 'tabLongPress',
            target: route.key,
          });
        }, [navigation, route.key]);

        const getIconName = useCallback((routeName: string, focused: boolean) => {
          const icons: Record<string, { focused: keyof typeof Ionicons.glyphMap; unfocused: keyof typeof Ionicons.glyphMap }> = {
            Home: { focused: 'home', unfocused: 'home-outline' },
            Leagues: { focused: 'trophy', unfocused: 'trophy-outline' },
            Dashboard: { focused: 'grid', unfocused: 'grid-outline' },
            Analytics: { focused: 'analytics', unfocused: 'analytics-outline' },
            More: { focused: 'menu', unfocused: 'menu-outline' }
          };
          return icons[routeName]?.[focused ? 'focused' : 'unfocused'] || 'help-outline';
        }, []);

        return (
          <TouchableOpacity
            key={route.key}
            accessibilityRole="button"
            accessibilityState={isFocused ? { selected: true } : {}}
            accessibilityLabel={options.tabBarAccessibilityLabel}
            testID={options.tabBarTestID}
            onPress={onPress}
            onLongPress={onLongPress}
            style={styles.tabButton}
            activeOpacity={0.7}
          >
            <Animated.View
              style={[
                styles.tabContent,
                {
                  transform: [
                    {
                      scale: tabAnimations[index].interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 1.1]
                      })
                    }
                  ]
                }
              ]}
            >
              <Animated.View
                style={{
                  opacity: tabAnimations[index].interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.6, 1]
                  })
                }}
              >
                <Ionicons
                  name={getIconName(route.name, isFocused)}
                  size={24}
                  color={isFocused ? '#2563eb' : '#6b7280'}
                />
              </Animated.View>
              <Animated.Text
                style={[
                  styles.tabLabel,
                  {
                    color: isFocused ? '#2563eb' : '#6b7280',
                    opacity: tabAnimations[index].interpolate({
                      inputRange: [0, 1],
                      outputRange: [0.6, 1]
                    }),
                    transform: [
                      {
                        translateY: tabAnimations[index].interpolate({
                          inputRange: [0, 1],
                          outputRange: [2, 0]
                        })
                      }
                    ]
                  }
                ]}
                numberOfLines={1}
                allowFontScaling={false}
              >
                {label}
              </Animated.Text>
            </Animated.View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const Stack = createStackNavigator<RootStackParamList>();

// Memoized tab screen components
const MemoizedHomeScreen = React.memo(() => (
  <LazyScreen><HomeScreen /></LazyScreen>
));

const MemoizedLeaguesScreen = React.memo(() => (
  <LazyScreen><LeaguesScreen /></LazyScreen>
));

const MemoizedDashboardScreen = React.memo(() => (
  <LazyScreen><DashboardScreen /></LazyScreen>
));

const MemoizedAnalyticsScreen = React.memo(() => (
  <LazyScreen><AnalyticsScreen /></LazyScreen>
));

// More screen with additional navigation options
const MoreScreen: React.FC = React.memo(() => {
  return (
    <View style={styles.moreContainer}>
      <Text style={styles.moreTitle}>More Options</Text>
      <TouchableOpacity style={styles.moreItem}>
        <Ionicons name="settings-outline" size={24} color="#6b7280" />
        <Text style={styles.moreItemText}>Settings</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.moreItem}>
        <Ionicons name="help-circle-outline" size={24} color="#6b7280" />
        <Text style={styles.moreItemText}>Help & Support</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.moreItem}>
        <Ionicons name="information-circle-outline" size={24} color="#6b7280" />
        <Text style={styles.moreItemText}>About</Text>
      </TouchableOpacity>
    </View>
  );
});

// Navigation state persistence
const PERSISTENCE_KEY = 'NAVIGATION_STATE';

const getInitialState = async (): Promise<PartialState<NavigationState> | undefined> => {
  try {
    const savedStateString = await AsyncStorage.getItem(PERSISTENCE_KEY);
    const state = savedStateString ? JSON.parse(savedStateString) : undefined;
    return state;
  } catch (error) {
    console.warn('Failed to restore navigation state:', error);
    return undefined;
  }
};

const saveNavigationState = async (state: NavigationState) => {
  try {
    await AsyncStorage.setItem(PERSISTENCE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn('Failed to save navigation state:', error);
  }
};

// Optimized Main Tab Navigator
const MainTabNavigator: React.FC = React.memo(() => {
  return (
    <Tab.Navigator
      tabBar={(props) => <CustomTabBar {...props} />}
      screenOptions={{
        headerShown: false,
        lazy: true,
        unmountOnBlur: false,
        freezeOnBlur: true,
      }}
      initialRouteName="Home"
    >
      <Tab.Screen
        name="Home"
        component={MemoizedHomeScreen}
        options={{
          title: 'Home',
          tabBarLabel: 'Home'
        }}
      />
      <Tab.Screen
        name="Leagues"
        component={MemoizedLeaguesScreen}
        options={{
          title: 'Leagues',
          tabBarLabel: 'Leagues'
        }}
      />
      <Tab.Screen
        name="Dashboard"
        component={MemoizedDashboardScreen}
        options={{
          title: 'Dashboard',
          tabBarLabel: 'Dashboard'
        }}
      />
      <Tab.Screen
        name="Analytics"
        component={MemoizedAnalyticsScreen}
        options={{
          title: 'Analytics',
          tabBarLabel: 'Analytics'
        }}
      />
      <Tab.Screen
        name="More"
        component={MoreScreen}
        options={{
          title: 'More',
          tabBarLabel: 'More'
        }}
      />
    </Tab.Navigator>
  );
});

// Enhanced Root Navigator with optimizations
export const OptimizedTabNavigator: React.FC = () => {
  const [isReady, setIsReady] = React.useState(false);
  const [initialState, setInitialState] = React.useState<PartialState<NavigationState>>();

  // Handle back button for Android
  useEffect(() => {
    if (Platform.OS === 'android') {
      const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
        // Custom back button handling logic
        return false; // Let default behavior handle it
      });

      return () => backHandler.remove();
    }
  }, []);

  // Handle app state changes for performance
  useEffect(() => {
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'background') {
        // App is going to background, save state
        console.log('App backgrounded, saving navigation state');
      } else if (nextAppState === 'active') {
        // App is coming to foreground
        console.log('App foregrounded');
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  }, []);

  React.useEffect(() => {
    const restoreState = async () => {
      try {
        const state = await getInitialState();
        if (state !== undefined) {
          setInitialState(state);
        }
      } finally {
        setIsReady(true);
      }
    };

    if (!isReady) {
      restoreState();
    }
  }, [isReady]);

  const screenOptions = useMemo(() => ({
    headerStyle: {
      backgroundColor: '#2563eb',
      elevation: 0,
      shadowOpacity: 0,
    },
    headerTintColor: '#fff',
    headerTitleStyle: {
      fontWeight: 'bold' as const,
      fontSize: 18,
    },
    cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
    gestureEnabled: true,
    gestureDirection: 'horizontal' as const,
  }), []);

  if (!isReady) {
    return (
      <View style={styles.loadingContainer}>
        <Animated.View style={styles.loadingSpinner} />
        <Text style={styles.loadingText}>Initializing...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer
      initialState={initialState}
      onStateChange={saveNavigationState}
    >
      <Stack.Navigator
        initialRouteName="Auth"
        screenOptions={screenOptions}
      >
        <Stack.Screen
          name="Auth"
          options={{
            headerShown: false,
            cardStyleInterpolator: CardStyleInterpolators.forFadeFromBottomAndroid,
          }}
        >
          {() => <LazyScreen><AuthScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Main"
          component={MainTabNavigator}
          options={{
            headerShown: false,
            cardStyleInterpolator: CardStyleInterpolators.forFadeFromBottomAndroid,
          }}
        />
        <Stack.Screen
          name="Draft"
          options={{
            title: 'Live Draft',
            presentation: 'modal',
            cardStyleInterpolator: CardStyleInterpolators.forModalPresentationIOS,
          }}
        >
          {() => <LazyScreen><DraftScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Lineup"
          options={{
            title: 'Set Lineup',
            cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
          }}
        >
          {() => <LazyScreen><LineupScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Trades"
          options={{
            title: 'Trades',
            cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
          }}
        >
          {() => <LazyScreen><TradesScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Trade"
          options={{
            title: 'Trade Details',
            cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
          }}
        >
          {() => <LazyScreen><TradeScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Waiver"
          options={{
            title: 'Waiver Wire',
            cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
          }}
        >
          {() => <LazyScreen><WaiverScreen /></LazyScreen>}
        </Stack.Screen>
        <Stack.Screen
          name="Analytics"
          options={{
            title: 'Analytics',
            cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
          }}
        >
          {() => <LazyScreen><AnalyticsScreen /></LazyScreen>}
        </Stack.Screen>
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingSpinner: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 3,
    borderColor: '#e5e7eb',
    borderTopColor: '#2563eb',
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  tabBarContainer: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingBottom: Platform.OS === 'ios' ? 20 : 10,
    paddingTop: 8,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    position: 'relative',
  },
  tabIndicator: {
    position: 'absolute',
    top: 0,
    height: 3,
    backgroundColor: '#2563eb',
    borderRadius: 2,
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  tabContent: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
    textAlign: 'center',
  },
  moreContainer: {
    flex: 1,
    backgroundColor: '#f9fafb',
    paddingTop: 20,
  },
  moreTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginHorizontal: 20,
    marginBottom: 20,
  },
  moreItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  moreItemText: {
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
    fontWeight: '500',
  },
});

export default OptimizedTabNavigator;