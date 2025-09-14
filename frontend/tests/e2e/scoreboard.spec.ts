import { test, expect } from "@playwright/test";
import { makeHS256 } from "./utils";
import crypto from "node:crypto";

test("scoreboard endpoint returns items (may be empty)", async ({ request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const user = crypto.randomUUID();
  const token = makeHS256(user, secret);

  // Create a league
  const create = await request.post("/leagues", {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: "SB League", sport: "basketball", league_type: "head_to_head", season: "2025" },
  });
  expect(create.status()).toBe(201);
  const { league_id } = await create.json();

  const resp = await request.get(`/leagues/${league_id}/scoreboard`);
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body).toHaveProperty("items");
  expect(Array.isArray(body.items)).toBe(true);
});
