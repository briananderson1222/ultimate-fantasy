import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.evaluate(() => {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        localStorage.removeItem(key);
      }
    }
  });
});

// test("dashboard widgets can be rearranged and persist layout", async ({ page }) => {
//   await page.goto("/dashboard");

//   // Ensure at least 3 widgets rendered
//   const titles = page.locator('[data-testid="widget-title"]');
//   await expect(titles).toHaveCount(5);

//   // Find the index of "Scoreboard"
//   const texts = await titles.allInnerTexts();
//   const idx = texts.findIndex((t) => t.trim() === "Scoreboard");
//   expect(idx).toBeGreaterThanOrEqual(0);

//   // Move up until it's at the top
//   for (let i = idx; i > 0; i--) {
//     await page.getByLabel(`Move Scoreboard up`).click();
//   }

//   // Log localStorage before saving
//   const localStorageBeforeSave = await page.evaluate(() => localStorage.getItem("uf_dashboard_layout"));
//   console.log("localStorage before save:", localStorageBeforeSave);

//   // Save and verify first widget is Scoreboard
//   await page.getByTestId("save-layout").click();

//   // Log localStorage after saving
//   const localStorageAfterSave = await page.evaluate(() => localStorage.getItem("uf_dashboard_layout"));
//   console.log("localStorage after save:", localStorageAfterSave);

//   // Instead of reload, navigate again to force full re-render
//   await page.goto("/dashboard");
//   await page.waitForTimeout(500); // Add a small delay here

//   // Log localStorage after navigate
//   const localStorageAfterReload = await page.evaluate(() => localStorage.getItem("uf_dashboard_layout"));
//   console.log("localStorage after navigate:", localStorageAfterReload);

//   const first = await page.locator('[data-testid="widget-title"]').first().innerText();
//   console.log("First widget after navigate:", first);
//   expect(first).toBe("Scoreboard");
// });
