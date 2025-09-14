import { test, expect } from "@playwright/test";

// Helper to set theme
async function setTheme(page: any, theme: "light" | "dark") {
  await page.evaluate((theme: string) => {
    document.documentElement.setAttribute("data-theme", theme);
  }, theme);
  await page.waitForTimeout(100); // Allow theme to apply
}

// Helper to set dev token
async function setDevToken(page: any) {
  await page.evaluate(() => {
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20ifQ.test";
    localStorage.setItem("uf_token", token);
  });
}

test.describe("Visual Regression Tests", () => {
  test("Homepage - Light Theme", async ({ page }) => {
    await page.goto("/");
    await setDevToken(page);
    await setTheme(page, "light");
    await expect(page).toHaveScreenshot("homepage-light.png");
  });

  test("Homepage - Dark Theme", async ({ page }) => {
    await page.goto("/");
    await setDevToken(page);
    await setTheme(page, "dark");
    await expect(page).toHaveScreenshot("homepage-dark.png");
  });

  test("Dashboard - Light Theme", async ({ page }) => {
    await page.goto("/dashboard");
    await setDevToken(page);
    await setTheme(page, "light");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("dashboard-light.png");
  });

  test("Dashboard - Dark Theme", async ({ page }) => {
    await page.goto("/dashboard");
    await setDevToken(page);
    await setTheme(page, "dark");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("dashboard-dark.png");
  });

  test("Create League - Light Theme", async ({ page }) => {
    await page.goto("/leagues/create");
    await setDevToken(page);
    await setTheme(page, "light");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("create-league-light.png");
  });

  test("Create League - Dark Theme", async ({ page }) => {
    await page.goto("/leagues/create");
    await setDevToken(page);
    await setTheme(page, "dark");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("create-league-dark.png");
  });

  test("Leagues List - Light Theme", async ({ page }) => {
    await page.goto("/leagues");
    await setDevToken(page);
    await setTheme(page, "light");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("leagues-list-light.png");
  });

  test("Leagues List - Dark Theme", async ({ page }) => {
    await page.goto("/leagues");
    await setDevToken(page);
    await setTheme(page, "dark");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("leagues-list-dark.png");
  });

  test("Theme Settings - Light Theme", async ({ page }) => {
    await page.goto("/settings/theme");
    await setDevToken(page);
    await setTheme(page, "light");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("theme-settings-light.png");
  });

  test("Theme Settings - Dark Theme", async ({ page }) => {
    await page.goto("/settings/theme");
    await setDevToken(page);
    await setTheme(page, "dark");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("theme-settings-dark.png");
  });

  test("Players Page - Light Theme", async ({ page }) => {
    await page.goto("/players");
    await setDevToken(page);
    await setTheme(page, "light");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("players-light.png");
  });

  test("Players Page - Dark Theme", async ({ page }) => {
    await page.goto("/players");
    await setDevToken(page);
    await setTheme(page, "dark");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("players-dark.png");
  });
});
