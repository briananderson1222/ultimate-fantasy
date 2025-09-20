import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { secureStorage } from '../utils/secureStorage';

interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  token: string | null;
}

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    token: null,
  });

  // Initialize authentication state on app start
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const token = await secureStorage.getAuthToken();
      const { userId, email } = await secureStorage.getUserData();

      if (token && userId && email) {
        setState({
          isAuthenticated: true,
          isLoading: false,
          user: { id: userId, email },
          token,
        });
      } else {
        setState(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error initializing auth:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const signIn = useCallback(async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Mock API call - replace with actual authentication
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock successful response
      const mockToken = `jwt_token_${Date.now()}`;
      const mockUserId = `user_${Date.now()}`;

      // Store tokens and user data securely
      await secureStorage.setTokens(mockToken);
      await secureStorage.setUserData(mockUserId, email);

      const user: User = {
        id: mockUserId,
        email,
        name: email.split('@')[0], // Simple name from email
      };

      setState({
        isAuthenticated: true,
        isLoading: false,
        user,
        token: mockToken,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw new Error('Sign in failed. Please check your credentials.');
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string, name?: string) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Mock API call - replace with actual registration
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock successful response
      const mockToken = `jwt_token_${Date.now()}`;
      const mockUserId = `user_${Date.now()}`;

      // Store tokens and user data securely
      await secureStorage.setTokens(mockToken);
      await secureStorage.setUserData(mockUserId, email);

      const user: User = {
        id: mockUserId,
        email,
        name: name || email.split('@')[0],
      };

      setState({
        isAuthenticated: true,
        isLoading: false,
        user,
        token: mockToken,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw new Error('Sign up failed. Please try again.');
    }
  }, []);

  const signOut = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Clear all stored data
      await secureStorage.clear();

      setState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        token: null,
      });
    } catch (error) {
      console.error('Error signing out:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const currentToken = await secureStorage.getAuthToken();
      const refreshTokenValue = await secureStorage.getRefreshToken();

      if (!currentToken || !refreshTokenValue) {
        throw new Error('No tokens available');
      }

      // Mock token refresh - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500));

      const newToken = `jwt_token_refreshed_${Date.now()}`;
      await secureStorage.setTokens(newToken, refreshTokenValue);

      setState(prev => ({ ...prev, token: newToken }));
    } catch (error) {
      console.error('Token refresh failed:', error);
      await signOut();
    }
  }, [signOut]);

  const updateProfile = useCallback(async (updates: Partial<User>) => {
    if (!state.user) return;

    setState(prev => ({
      ...prev,
      isLoading: true,
    }));

    try {
      // Mock API call - replace with actual profile update
      await new Promise(resolve => setTimeout(resolve, 500));

      const updatedUser = { ...state.user, ...updates };

      // Update stored email if changed
      if (updates.email) {
        await secureStorage.setUserData(updatedUser.id, updates.email);
      }

      setState(prev => ({
        ...prev,
        user: updatedUser,
        isLoading: false,
      }));
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw new Error('Profile update failed. Please try again.');
    }
  }, [state.user]);

  const contextValue: AuthContextType = {
    ...state,
    signIn,
    signUp,
    signOut,
    refreshToken,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}