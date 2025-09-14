import { test, expect } from '@playwright/test';
import { makeHS256 } from './utils';
import crypto from 'node:crypto';

test('create league via UI shows success toast', async ({ page }) => {
  const secret = process.env.AUTH_DEV_SECRET || 'test-e2e-secret';
  const user = crypto.randomUUID();
  const token = makeHS256(user, secret);

  await page.addInitScript(([t]) => {
    window.localStorage.setItem('uf_token', t);
  }, token);

  await page.goto('/leagues/create');
  await page.getByLabel('Name').fill('UI League');
  await page.getByLabel('Sport').fill('basketball');
  await page.getByLabel('League Type').fill('head_to_head');
  await page.getByLabel('Season').fill('2025');
  await page.getByRole('button', { name: 'Create' }).click();

  await expect(page.getByText('League created')).toBeVisible();
});

