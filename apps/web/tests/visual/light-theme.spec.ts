import { test, expect } from '@playwright/test';

test.describe('Light Theme Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a page that will be themed
    await page.goto('/');

    // Set theme to light
    await page.evaluate(() => {
      localStorage.setItem('theme', 'light');
      document.documentElement.className = 'light';
    });
  });

  test('ThemeProvider in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-providers-themeprovider--light-theme');

    // Wait for theme to be applied
    await page.waitForSelector('[data-theme="light"]');

    // Take screenshot
    await expect(page).toHaveScreenshot('theme-provider-light.png');
  });

  test('Button components in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-button--variants');

    // Apply light theme
    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('button-variants-light.png');
  });

  test('Card components in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-card--variants');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('card-variants-light.png');
  });

  test('MatchCard in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-matchcard--completed');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('match-card-light.png');
  });

  test('PlayerCard in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-playercard--default');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('player-card-light.png');
  });

  test('TrendingPlayers in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-trendingplayers--default');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('trending-players-light.png');
  });

  test('LeagueChat in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-leaguechat--default');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('league-chat-light.png');
  });

  test('SettingsGrid in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-patterns-settingsgrid--default');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('settings-grid-light.png');
  });

  test('ProgressBar in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-primitives-progressbar--different-values');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('progress-bar-light.png');
  });

  test('Color tokens in light mode', async ({ page }) => {
    await page.goto('/ladle?story=design-system-tokens-colors--all-colors');

    await page.evaluate(() => {
      document.documentElement.className = 'light';
    });

    await expect(page).toHaveScreenshot('color-tokens-light.png');
  });
});