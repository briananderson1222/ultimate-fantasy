import { test, expect } from "@playwright/test";

test("dashboard widgets can be rearranged and persist layout", async ({ page }) => {
  await page.goto("/dashboard");

  // Ensure at least 3 widgets rendered
  const titles = page.locator('[data-testid="widget-title"]');
  await expect(titles).toHaveCount(5);

  // Find the index of "Scoreboard"
  const texts = await titles.allInnerTexts();
  const idx = texts.findIndex((t) => t.trim() === "Scoreboard");
  expect(idx).toBeGreaterThanOrEqual(0);

  // Move up until it's at the top
  for (let i = idx; i > 0; i--) {
    await page.getByLabel(`Move Scoreboard up`).click();
  }

  // Save and verify first widget is Scoreboard
  await page.getByTestId("save-layout").click();
  await page.reload();
  const first = await page.locator('[data-testid="widget-title"]').first().innerText();
  expect(first).toBe("Scoreboard");
});
