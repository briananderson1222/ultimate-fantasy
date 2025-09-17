import { test, expect } from "@playwright/test";
import { makeHS256 } from "./utils";
import crypto from "node:crypto";

test("Managers tab lists commissioner and joined user", async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const commissioner = crypto.randomUUID();
  const token1 = makeHS256(commissioner, secret);
  const user2 = crypto.randomUUID();
  const token2 = makeHS256(user2, secret);

  const create = await request.post("http://localhost:8000/leagues", {
    headers: { Authorization: `Bearer ${token1}` },
    data: {
      name: "Managers League",
      sport: "basketball",
      league_type: "head_to_head",
      season: "2025",
    },
  });
  expect(create.status()).toBe(201);
  const { league_id } = await create.json();
  console.log("Created League ID:", league_id);

  // Add a small delay to ensure league is committed
  await page.waitForTimeout(1000);

  const joinUrl = `http://localhost:8000/leagues/${league_id}/join`;
  console.log("Join Request URL:", joinUrl);
  const join = await request.post(joinUrl, {
    headers: { Authorization: `Bearer ${token2}` },
  });
  console.log("Join Response Status:", join.status());
  expect(join.status()).toBe(200);

  await page.addInitScript(([t]) => {
    window.localStorage.setItem("uf_token", t);
  }, token2);

  // Delay members fetch to visualize skeleton
  await page.route(`http://localhost:8000/leagues/${league_id}/members`, async (route) => {
    setTimeout(() => route.continue(), 200);
  });

  await page.goto(`/leagues/${league_id}`);
  await page.waitForLoadState('networkidle'); // Add this line
  console.log("Page loaded, checking for Managers tab..."); // Add this line
  const managersTab = page.getByRole("tab", { name: "Managers" });
  console.log("Managers tab visible:", await managersTab.isVisible()); // Add this line
  await managersTab.waitFor({ state: 'visible' });
  await managersTab.waitFor({ state: 'enabled' });
  await managersTab.click(); // Use the variable

  await expect(page.locator(".animate-pulse")).toBeVisible();

  // Expect both user ids (truncated) to appear
  await expect(page.getByText(commissioner.slice(0, 8))).toBeVisible();
  await expect(page.getByText(user2.slice(0, 8))).toBeVisible();
});
