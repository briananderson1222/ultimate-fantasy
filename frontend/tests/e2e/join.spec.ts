import { test, expect } from '@playwright/test';
import { makeHS256 } from './utils';

test('join league via UI', async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || 'test-e2e-secret';
  const user1 = crypto.randomUUID();
  const token = makeHS256(user1, secret);

  // Create league via API using bearer token
  const create = await request.post('/leagues', {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      name: 'Join League',
      sport: 'basketball',
      league_type: 'head_to_head',
      season: '2025',
    },
  });
  expect(create.status()).toBe(201);
  const league = await create.json();

  // Set token in localStorage for UI (not strictly needed by this page yet)
  await page.addInitScript(([t]) => {
    window.localStorage.setItem('uf_token', t);
  }, token);

  await page.goto(`/leagues/${league.league_id}`);

  // Fill userId field and click Join
  const user2 = crypto.randomUUID();
  await page.getByPlaceholder('User ID (UUID)').fill(user2);
  await page.getByRole('button', { name: 'Join' }).click();

  await expect(page.getByText('Joined as')).toBeVisible();
});

