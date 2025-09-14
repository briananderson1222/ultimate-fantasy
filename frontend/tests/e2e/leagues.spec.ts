import { test, expect } from "@playwright/test";
import crypto from "node:crypto";

function base64url(input: Buffer | string): string {
  const b = Buffer.isBuffer(input) ? input : Buffer.from(input);
  return b.toString("base64").replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function signHS256(data: string, secret: string): string {
  const mac = crypto.createHmac("sha256", secret).update(data).digest();
  return base64url(mac);
}

function makeHS256(sub: string, secret: string): string {
  const header = base64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = base64url(JSON.stringify({ sub }));
  const signingInput = `${header}.${payload}`;
  const sig = signHS256(signingInput, secret);
  return `${signingInput}.${sig}`;
}

test("create league via API responds 201", async ({ request }) => {
  const secret = process.env.AUTH_DEV_SECRET || "test-e2e-secret";
  const sub = crypto.randomUUID();
  const token = makeHS256(sub, secret);

  const resp = await request.post("/leagues", {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      name: "E2E League",
      sport: "basketball",
      league_type: "head_to_head",
      season: "2025",
    },
  });
  expect(resp.status()).toBe(201);
  const body = await resp.json();
  expect(body).toHaveProperty("league_id");
});
