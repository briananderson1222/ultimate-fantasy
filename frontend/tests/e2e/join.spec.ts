import { test, expect } from "@playwright/test";
import { makeHS256 } from "./utils";
import crypto from "node:crypto";

test("join league via UI", async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const user1 = crypto.randomUUID();
  const token1 = makeHS256(user1, secret);

  // Create league via API using bearer token
  const create = await request.post("/leagues", {
    headers: { Authorization: `Bearer ${token1}` },
    data: {
      name: "Join League",
      sport: "basketball",
      league_type: "head_to_head",
      season: "2025",
    },
  });
  expect(create.status()).toBe(201);
  const league = await create.json();

  // Use a different user for joining via UI
  const user2 = crypto.randomUUID();
  const token2 = makeHS256(user2, secret);
  await page.addInitScript(([t]) => {
    window.localStorage.setItem("uf_token", t);
  }, token2);

  await page.goto(`/leagues/${league.league_id}`);

  // Click Join and confirm dialog
  await page.getByRole("button", { name: "Join" }).click();
  await page.getByRole("button", { name: "Confirm Join" }).click();

  await expect(page.getByText("Joined as")).toBeVisible();
});
