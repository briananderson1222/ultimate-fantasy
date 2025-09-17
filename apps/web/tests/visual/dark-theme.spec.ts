import { test, expect } from '@playwright/test';

test.describe('Dark Theme Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page that will be themed
    await page.goto('/');

    // Set theme to dark
    await page.evaluate(() => {
      localStorage.setItem('theme', 'dark');
      document.documentElement.className = 'dark';
    });
  });

  test('ThemeProvider in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-providers-themeprovider--dark-theme');

    // Wait for theme to be applied
    await page.waitForSelector('[data-theme="dark"]');

    // Take screenshot
    await expect(page).toHaveScreenshot('theme-provider-dark.png');
  });

  test('Button components in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-button--variants');

    // Apply dark theme
    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('button-variants-dark.png');
  });

  test('Card components in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-card--variants');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('card-variants-dark.png');
  });

  test('MatchCard in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-matchcard--completed');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('match-card-dark.png');
  });

  test('PlayerCard in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-playercard--default');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('player-card-dark.png');
  });

  test('TrendingPlayers in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-trendingplayers--default');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('trending-players-dark.png');
  });

  test('LeagueChat in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-leaguechat--default');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('league-chat-dark.png');
  });

  test('SettingsGrid in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-settingsgrid--default');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('settings-grid-dark.png');
  });

  test('ProgressBar in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-progressbar--different-values');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('progress-bar-dark.png');
  });

  test('Color tokens in dark mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-tokens-colors--all-colors');

    await page.evaluate(() => {
      document.documentElement.className = 'dark';
    });

    await expect(page).toHaveScreenshot('color-tokens-dark.png');
  });
});