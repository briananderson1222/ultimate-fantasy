import type { Story } from "@ladle/react";
import { ThemeProvider } from "../components/design-system/providers/ThemeProvider";
import { useTheme } from "../components/design-system/hooks/useTheme";

const ThemeDemo = () => {
  const { theme, setTheme, tokens } = useTheme();

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-2xl font-bold">Theme System Demo</h2>

      <div className="flex gap-4">
        <button
          onClick={() => setTheme("light")}
          className={`px-4 py-2 rounded ${theme === "light" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
        >
          Light Theme
        </button>
        <button
          onClick={() => setTheme("dark")}
          className={`px-4 py-2 rounded ${theme === "dark" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
        >
          Dark Theme
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div
          className="p-4 border rounded"
          style={{
            backgroundColor: tokens.colors.surface,
            color: tokens.colors.textPrimary,
            borderColor: tokens.colors.border,
          }}
        >
          <h3 className="font-semibold mb-2">Surface Container</h3>
          <p style={{ color: tokens.colors.textSecondary }}>Secondary text example</p>
        </div>

        <div
          className="p-4 border rounded"
          style={{
            backgroundColor: tokens.colors.primary + "20",
            color: tokens.colors.textPrimary,
            borderColor: tokens.colors.primary,
          }}
        >
          <h3 className="font-semibold mb-2">Primary Accent</h3>
          <p>Primary color: {tokens.colors.primary}</p>
        </div>
      </div>

      <div className="flex gap-2">
        <div
          className="w-16 h-16 rounded flex items-center justify-center text-white text-xs"
          style={{ backgroundColor: tokens.colors.success }}
        >
          Success
        </div>
        <div
          className="w-16 h-16 rounded flex items-center justify-center text-white text-xs"
          style={{ backgroundColor: tokens.colors.warning }}
        >
          Warning
        </div>
        <div
          className="w-16 h-16 rounded flex items-center justify-center text-white text-xs"
          style={{ backgroundColor: tokens.colors.primary }}
        >
          Primary
        </div>
      </div>
    </div>
  );
};

export const Default: Story = () => (
  <ThemeProvider initialTheme="dark">
    <ThemeDemo />
  </ThemeProvider>
);

export const LightTheme: Story = () => (
  <ThemeProvider initialTheme="light">
    <ThemeDemo />
  </ThemeProvider>
);

export const SystemTheme: Story = () => (
  <ThemeProvider enableSystemTheme>
    <ThemeDemo />
  </ThemeProvider>
);

Default.meta = {
  title: "Design System/ThemeProvider",
};
