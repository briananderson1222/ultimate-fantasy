import React from "react";
import { ThemeProvider } from "./ThemeProvider";

export default { title: "Design System/Providers/ThemeProvider" };

export const Default = () => (
  <ThemeProvider>
    <div className="p-4 bg-background text-foreground">
      <h3 className="text-lg font-semibold">Theme Provider Test</h3>
      <p>This text should adapt to the current theme.</p>
    </div>
  </ThemeProvider>
);

export const DarkTheme = () => (
  <ThemeProvider defaultTheme="dark">
    <div className="p-4 bg-background text-foreground">
      <h3 className="text-lg font-semibold">Dark Theme</h3>
      <p>This content is rendered with dark theme.</p>
      <div className="mt-2 p-2 bg-card text-card-foreground rounded">
        Card background in dark theme
      </div>
    </div>
  </ThemeProvider>
);

export const LightTheme = () => (
  <ThemeProvider defaultTheme="light">
    <div className="p-4 bg-background text-foreground">
      <h3 className="text-lg font-semibold">Light Theme</h3>
      <p>This content is rendered with light theme.</p>
      <div className="mt-2 p-2 bg-card text-card-foreground rounded">
        Card background in light theme
      </div>
    </div>
  </ThemeProvider>
);

export const SystemTheme = () => (
  <ThemeProvider defaultTheme="system">
    <div className="p-4 bg-background text-foreground">
      <h3 className="text-lg font-semibold">System Theme</h3>
      <p>This content follows the system preference.</p>
    </div>
  </ThemeProvider>
);
