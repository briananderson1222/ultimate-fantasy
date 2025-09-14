import { test, expect } from "@playwright/test";
import { makeHS256 } from "./utils";
import crypto from "node:crypto";

test("My Leagues list renders after create", async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const user = crypto.randomUUID();
  const token = makeHS256(user, secret);

  // Create league via API using bearer token (commissioner becomes a member)
  const create = await request.post("/leagues", {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      name: "My Leagues UI",
      sport: "basketball",
      league_type: "head_to_head",
      season: "2025",
    },
  });
  expect(create.status()).toBe(201);

  // Inject token into localStorage for the UI
  await page.addInitScript(([t]) => {
    window.localStorage.setItem("uf_token", t);
  }, token);

  // Slow the read call slightly so skeleton is visible
  await page.route("http://localhost:8000/me/leagues", async (route) => {
    setTimeout(() => route.continue(), 200);
  });

  await page.goto("/leagues");

  // Skeleton and list
  await expect(page.locator(".animate-pulse")).toBeVisible();
  await expect(page.getByText("My Leagues UI")).toBeVisible();
});
