import { test, expect } from "@playwright/test";

test("widget settings persist for scoreboard", async ({ page }) => {
  await page.goto("/dashboard");

  // Open settings for Scoreboard
  await page.getByLabel("Settings for Scoreboard").click();
  const input = page.getByPlaceholder("optional league uuid");
  await input.fill("00000000-0000-0000-0000-00000000abcd");
  await page.getByRole("button", { name: "Save" }).click();

  // Reload and verify it persisted (open again and check value)
  await page.reload();
  await page.getByLabel("Settings for Scoreboard").click();
  await expect(input).toHaveValue("00000000-0000-0000-0000-00000000abcd");
});
