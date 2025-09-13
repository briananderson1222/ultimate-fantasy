import { test, expect } from '@playwright/test';
import { makeHS256 } from './utils';
import crypto from 'node:crypto';

test('place waiver bid via API returns 201', async ({ request }) => {
  const secret = process.env.AUTH_DEV_SECRET || 'test-e2e-secret';
  const user = crypto.randomUUID();
  const token = makeHS256(user, secret);

  // Create a league and join to get team id
  const create = await request.post('/leagues', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'Waivers League', sport: 'basketball', league_type: 'head_to_head', season: '2025' },
  });
  expect(create.status()).toBe(201);
  const { league_id } = await create.json();

  const user2 = crypto.randomUUID();
  const token2 = makeHS256(user2, secret);
  const join = await request.post(`/leagues/${league_id}/join`, { headers: { Authorization: `Bearer ${token2}` } });
  expect(join.status()).toBe(200);
  const { team_id } = await join.json();

  // Place bid (player_id arbitrary in sqlite dev)
  const bid = await request.post('/waivers/bids', {
    headers: { Authorization: `Bearer ${token}` },
    data: { league_id, team_id, player_id: crypto.randomUUID(), bid: 11 },
  });
  expect(bid.status()).toBe(201);
  const body = await bid.json();
  expect(body).toHaveProperty('waiver_id');
});
