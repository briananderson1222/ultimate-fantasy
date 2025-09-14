import { test, expect } from '@playwright/test';

function getBg(page) {
  return page.evaluate(() => getComputedStyle(document.body).backgroundColor);
}

test('switches between light and dark theme and persists', async ({ page }) => {
  await page.goto('/settings/theme');

  const initialBg = await getBg(page);

  // Switch to dark and check background color changes
  await page.getByRole('button', { name: 'Dark' }).click();
  const darkBg = await getBg(page);
  expect(darkBg).not.toEqual(initialBg);

  // Persist across reloads
  await page.reload();
  const afterReload = await getBg(page);
  expect(afterReload).toEqual(darkBg);
  const theme = await page.evaluate(() => localStorage.getItem('uf_theme'));
  expect(theme && JSON.parse(theme)).toBe('dark');
});

test('applies custom theme variables and persists', async ({ page }) => {
  await page.goto('/settings/theme');

  // Load example custom theme and apply
  await page.getByRole('button', { name: 'Load Example' }).click();
  await page.getByRole('button', { name: 'Apply' }).click();

  const customBg = await getBg(page);
  // PapayaWhip #ffefd5 => rgb(255, 239, 213)
  expect(customBg.replace(/\s+/g, '')).toBe('rgb(255,239,213)');

  // Persist across reloads
  await page.reload();
  const afterReload = await getBg(page);
  expect(afterReload.replace(/\s+/g, '')).toBe('rgb(255,239,213)');
  const theme = await page.evaluate(() => localStorage.getItem('uf_theme'));
  expect(theme && JSON.parse(theme)).toBe('custom');
});

