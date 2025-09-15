import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../../src/components/design-system/providers/ThemeProvider';
import { useTheme } from '../../src/components/design-system/hooks/useTheme';

// Test component that uses the theme hook
const ThemeTestComponent = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div>
      <div data-testid="current-theme">{theme}</div>
      <button
        data-testid="dark-button"
        onClick={() => setTheme('dark')}
      >
        Dark
      </button>
      <button
        data-testid="light-button"
        onClick={() => setTheme('light')}
      >
        Light
      </button>
      <button
        data-testid="system-button"
        onClick={() => setTheme('system')}
      >
        System
      </button>
    </div>
  );
};

describe('Theme Switching Integration', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it('should switch between light and dark themes', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>
    );

    // Initially should be system theme
    expect(screen.getByTestId('current-theme')).toHaveTextContent('system');

    // Switch to dark theme
    fireEvent.click(screen.getByTestId('dark-button'));
    expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');

    // Switch to light theme
    fireEvent.click(screen.getByTestId('light-button'));
    expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
  });

  it('should persist theme choice in localStorage', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>
    );

    // Switch to dark theme
    fireEvent.click(screen.getByTestId('dark-button'));

    // Check localStorage
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('should apply theme classes to document', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>
    );

    // Switch to dark theme
    fireEvent.click(screen.getByTestId('dark-button'));

    // Check document class
    expect(document.documentElement).toHaveClass('dark');

    // Switch to light theme
    fireEvent.click(screen.getByTestId('light-button'));

    // Check document class
    expect(document.documentElement).toHaveClass('light');
  });

  it('should initialize with saved theme from localStorage', () => {
    // Pre-populate localStorage
    localStorage.setItem('theme', 'dark');

    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
  });

  it('should handle system theme preference changes', () => {
    // Mock matchMedia for system theme
    const mockMatchMedia = vi.fn();
    window.matchMedia = mockMatchMedia;

    mockMatchMedia.mockReturnValue({
      matches: true, // Dark mode
      addListener: vi.fn(),
      removeListener: vi.fn(),
    });

    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>
    );

    // Set to system theme
    fireEvent.click(screen.getByTestId('system-button'));

    // Should follow system preference (dark)
    expect(document.documentElement).toHaveClass('dark');
  });
});