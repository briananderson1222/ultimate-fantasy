import { test, expect } from "@playwright/test";

test.describe("Responsive Visual Regression", () => {
  const breakpoints = [
    { name: "mobile", width: 375, height: 667 },
    { name: "tablet", width: 768, height: 1024 },
    { name: "desktop", width: 1200, height: 800 },
  ];

  for (const { name, width, height } of breakpoints) {
    test.describe(`${name} breakpoint (${width}x${height})`, () => {
      test.beforeEach(async ({ page }) => {
        await page.setViewportSize({ width, height });
      });

      test(`MatchCard responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-patterns-matchcard--completed");
        await expect(page).toHaveScreenshot(`match-card-${name}.png`);
      });

      test(`PlayerCard responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-patterns-playercard--default");
        await expect(page).toHaveScreenshot(`player-card-${name}.png`);
      });

      test(`TrendingPlayers responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-patterns-trendingplayers--default");
        await expect(page).toHaveScreenshot(`trending-players-${name}.png`);
      });

      test(`LeagueChat responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-patterns-leaguechat--default");
        await expect(page).toHaveScreenshot(`league-chat-${name}.png`);
      });

      test(`SettingsGrid responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-patterns-settingsgrid--default");
        await expect(page).toHaveScreenshot(`settings-grid-${name}.png`);
      });

      test(`Button variants responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-primitives-button--variants");
        await expect(page).toHaveScreenshot(`button-variants-${name}.png`);
      });

      test(`Card variants responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-primitives-card--variants");
        await expect(page).toHaveScreenshot(`card-variants-${name}.png`);
      });

      test(`ProgressBar responsive at ${name}`, async ({ page }) => {
        await page.goto("/ladle?story=design-system-primitives-progressbar--different-values");
        await expect(page).toHaveScreenshot(`progress-bar-${name}.png`);
      });
    });
  }
});
