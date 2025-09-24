import React from "react";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";
import Constants from "expo-constants";
import { httpClient } from "@ultimate-fantasy/api-client";

// Import navigation and auth
import AppNavigator from "./src/navigation/AppNavigator";
import { AuthProvider } from "./src/contexts/AuthContext";

const DEFAULT_HTTP_PORT = 8000;

const resolveApiBaseUrl = (): string => {
  const env =
    (typeof process !== "undefined" && process?.env) ||
    ({} as NodeJS.ProcessEnv);

  const candidates = [
    env.EXPO_PUBLIC_API_BASE_URL,
    env.NEXT_PUBLIC_API_BASE_URL,
    env.API_BASE_URL,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim().length > 0) {
      return value.trim().replace(/\/+$/, "");
    }
  }

  const extra = (Constants.expoConfig?.extra ??
    (Constants.manifest as { extra?: { apiBaseUrl?: string } })?.extra) as
    | { apiBaseUrl?: string }
    | undefined;

  if (typeof extra?.apiBaseUrl === "string" && extra.apiBaseUrl.trim()) {
    return extra.apiBaseUrl.trim().replace(/\/+$/, "");
  }

  const debuggerHost =
    Constants.expoConfig?.hostUri ??
    (Constants.expoConfig as { debuggerHost?: string })?.debuggerHost ??
    (Constants.manifest as { debuggerHost?: string })?.debuggerHost ??
    null;

  if (typeof debuggerHost === "string" && debuggerHost.length > 0) {
    const [host] = debuggerHost.split(":");
    if (host) {
      return `http://${host}:${DEFAULT_HTTP_PORT}`;
    }
  }

  return `http://localhost:${DEFAULT_HTTP_PORT}`;
};

// Configure API client before components mount to avoid race conditions
httpClient.updateConfig({ baseUrl: resolveApiBaseUrl() });

// Create query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export default function App() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AppNavigator />
          <StatusBar style="light" />
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
