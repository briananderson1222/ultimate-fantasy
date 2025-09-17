import { renderHook, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../../src/components/design-system/providers/ThemeProvider';
import React from 'react';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(ThemeProvider, { defaultTheme: 'dark' }, children)
);

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset document theme
    document.documentElement.removeAttribute('data-theme');
  });

  it('throws error when used outside ThemeProvider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      renderHook(() => useTheme());
    }).toThrow('useTheme must be used within a ThemeProvider');

    consoleSpy.mockRestore();
  });

  it('provides initial theme value', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.theme).toBe('dark');
    expect(typeof result.current.setTheme).toBe('function');
    expect(result.current.tokens).toBeDefined();
  });

  it('allows theme switching', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('light');
    });

    expect(result.current.theme).toBe('light');
  });

  it('persists theme to localStorage', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('light');
    });

    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('loads theme from localStorage on initialization', () => {
    localStorage.setItem('theme', 'light');

    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.theme).toBe('light');
  });

  it('applies theme to document element', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('light');
    });

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('provides color tokens for current theme', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.tokens.colors).toBeDefined();
    expect(result.current.tokens.colors.primary).toBeDefined();
    expect(result.current.tokens.colors.success).toBeDefined();
  });

  it('updates tokens when theme changes', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    const darkTokens = result.current.tokens.colors;

    act(() => {
      result.current.setTheme('light');
    });

    const lightTokens = result.current.tokens.colors;

    // Tokens should be different for different themes
    expect(darkTokens).not.toEqual(lightTokens);
  });

  it('handles system theme detection', () => {
    // Mock matchMedia
    const mockMatchMedia = vi.fn();
    window.matchMedia = mockMatchMedia;

    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.systemTheme).toBe('dark');
  });

  it('switches to system theme when requested', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('system');
    });

    expect(result.current.theme).toBe('system');
  });

  it('applies CSS custom properties on theme change', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('light');
    });

    // Check that CSS custom properties are set
    const rootStyles = getComputedStyle(document.documentElement);
    expect(document.documentElement.style.getPropertyValue('--color-primary')).toBeTruthy();
  });
});