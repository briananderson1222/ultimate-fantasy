"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ThemeProvider } from "./theme";
import { I18nProvider } from "./i18n";
import { ToastProvider } from "../components/ui/toast";
import CommandPalette from "../components/CommandPalette";
import { PreferencesProvider } from "../lib/preferences";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <PreferencesProvider>
        <ThemeProvider>
          <I18nProvider>
            <ToastProvider>
              {children}
              <CommandPalette />
            </ToastProvider>
          </I18nProvider>
        </ThemeProvider>
      </PreferencesProvider>
    </QueryClientProvider>
  );
}
