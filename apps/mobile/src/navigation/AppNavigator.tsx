import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';

// Screens
import HomeScreen from '../screens/HomeScreen';
import LeaguesScreen from '../screens/LeaguesScreen';
import DashboardScreen from '../screens/DashboardScreen';
import AuthScreen from '../screens/AuthScreen';
import DraftScreen from '../screens/DraftScreen';
import LineupScreen from '../screens/LineupScreen';
import TradesScreen from '../screens/TradesScreen';

// Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Draft: { leagueId: string };
  Lineup: { teamId: string };
  Trades: { leagueId: string };
};

export type MainTabParamList = {
  Home: undefined;
  Leagues: undefined;
  Dashboard: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// Main Tab Navigator
function MainTabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'Home') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Leagues') {
            iconName = focused ? 'trophy' : 'trophy-outline';
          } else if (route.name === 'Dashboard') {
            iconName = focused ? 'analytics' : 'analytics-outline';
          } else {
            iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#2563eb',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <Tab.Screen
        name="Leagues"
        component={LeaguesScreen}
        options={{ title: 'My Leagues' }}
      />
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: 'Dashboard' }}
      />
    </Tab.Navigator>
  );
}

// Root Stack Navigator
export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Auth"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#2563eb',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="Auth"
          component={AuthScreen}
          options={{
            headerShown: false,
            title: 'Sign In'
          }}
        />
        <Stack.Screen
          name="Main"
          component={MainTabNavigator}
          options={{
            headerShown: false,
            title: 'Ultimate Fantasy'
          }}
        />
        <Stack.Screen
          name="Draft"
          component={DraftScreen}
          options={{
            title: 'Live Draft',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="Lineup"
          component={LineupScreen}
          options={{ title: 'Set Lineup' }}
        />
        <Stack.Screen
          name="Trades"
          component={TradesScreen}
          options={{ title: 'Trades' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}