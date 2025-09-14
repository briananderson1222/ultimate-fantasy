import { test, expect } from "@playwright/test";
import { makeHS256 } from "./utils";
import crypto from "node:crypto";

test("Managers tab lists commissioner and joined user", async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const commissioner = crypto.randomUUID();
  const token1 = makeHS256(commissioner, secret);
  const user2 = crypto.randomUUID();
  const token2 = makeHS256(user2, secret);

  const create = await request.post("/leagues", {
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

  const join = await request.post(`/leagues/${league_id}/join`, {
    headers: { Authorization: `Bearer ${token2}` },
  });
  expect(join.status()).toBe(200);

  await page.addInitScript(([t]) => {
    window.localStorage.setItem("uf_token", t);
  }, token2);

  // Delay members fetch to visualize skeleton
  await page.route(`http://localhost:8000/leagues/${league_id}/members`, async (route) => {
    setTimeout(() => route.continue(), 200);
  });

  await page.goto(`/leagues/${league_id}`);
  await page.getByRole("tab", { name: "Managers" }).click();

  await expect(page.locator(".animate-pulse")).toBeVisible();

  // Expect both user ids (truncated) to appear
  await expect(page.getByText(commissioner.slice(0, 8))).toBeVisible();
  await expect(page.getByText(user2.slice(0, 8))).toBeVisible();
});
