import { test, expect } from '@playwright/test';
import { makeHS256 } from './utils';
import crypto from 'node:crypto';

test('waivers page shows recent bid after placing one', async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || 'test-e2e-secret';
  const user = crypto.randomUUID();
  const token = makeHS256(user, secret);

  // Create league and join to get a team_id for this user
  const create = await request.post('/leagues', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'Waivers UI League', sport: 'basketball', league_type: 'head_to_head', season: '2025' },
  });
  expect(create.status()).toBe(201);
  const { league_id } = await create.json();

  const join = await request.post(`/leagues/${league_id}/join`, { headers: { Authorization: `Bearer ${token}` } });
  expect(join.status()).toBe(200);
  const { team_id } = await join.json();

  // Save token for UI
  await page.addInitScript(([t]) => {
    window.localStorage.setItem('uf_token', t);
  }, token);

  // Slightly delay waivers list so skeleton is visible
  await page.route(`http://localhost:8000/waivers?*`, async (route) => {
    setTimeout(() => route.continue(), 200);
  });

  await page.goto('/waivers');

  await page.getByLabel('League ID').fill(league_id);
  await page.getByLabel('Team ID').fill(team_id);
  await page.getByLabel('Player ID').fill(crypto.randomUUID());
  await page.getByLabel('Bid').fill('11');

  await page.getByRole('button', { name: 'Place Bid' }).click();

  // Toast then refreshed list shows the bid
  await expect(page.getByText('Bid placed')).toBeVisible();
  await expect(page.locator('.animate-pulse')).toBeVisible();
  await expect(page.getByText('Bid 11')).toBeVisible();
});

