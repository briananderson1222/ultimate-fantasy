import { test, expect } from '@playwright/test';
import { makeHS256 } from './utils';

test('set lineup via UI', async ({ page, request }) => {
  const secret = process.env.AUTH_DEV_SECRET || 'test-e2e-secret';
  const user1 = crypto.randomUUID();
  const token = makeHS256(user1, secret);

  // Create league via API
  const create = await request.post('/leagues', {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      name: 'Lineup League',
      sport: 'basketball',
      league_type: 'head_to_head',
      season: '2025',
    },
  });
  expect(create.status()).toBe(201);
  const league = await create.json();

  // Join to get a team_id
  const user2 = crypto.randomUUID();
  const join = await request.post(`/leagues/${league.league_id}/join`, {
    headers: { 'x-user-id': user2 },
  });
  expect(join.status()).toBe(200);
  const { team_id } = await join.json();

  // Navigate to lineup page and fill form
  await page.addInitScript(([t]) => {
    window.localStorage.setItem('uf_token', t);
  }, token);
  await page.goto('/lineup');

  await page.getByPlaceholder('00000000-0000-0000-0000-000000000001').fill(user2);
  await page.getByPlaceholder('team uuid').fill(team_id);
  const today = new Date().toISOString().slice(0, 10);
  await page.getByLabel('Game Day').fill(today);
  // Players
  const p1 = crypto.randomUUID();
  const p2 = crypto.randomUUID();
  await page.getByPlaceholder('player uuid').first().fill(p1);
  await page.getByPlaceholder('position (e.g., PG)').first().fill('G');
  await page.getByRole('button', { name: 'Add Player' }).click();
  const playerInputs = page.getByPlaceholder('player uuid');
  await playerInputs.nth(1).fill(p2);
  const posInputs = page.getByPlaceholder('position (e.g., PG)');
  await posInputs.nth(1).fill('F');

  await page.getByRole('button', { name: 'Save Lineup' }).click();
  await expect(page.getByText(/Lineup Saved/)).toBeVisible();
});

