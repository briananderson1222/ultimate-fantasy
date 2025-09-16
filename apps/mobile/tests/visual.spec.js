const { device, element, by, expect: detoxExpect } = require('detox');

describe('Mobile Visual Regression Tests', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should match homepage screenshot in light theme', async () => {
    await element(by.id('homeScreen')).tap();
    await detoxExpected(element(by.id('homeScreen'))).toBeVisible();

    // Take screenshot for visual regression
    await device.takeScreenshot('homepage-light');
  });

  it('should match homepage screenshot in dark theme', async () => {
    // Switch to dark theme
    await element(by.id('themeToggle')).tap();
    await element(by.id('homeScreen')).tap();
    await detoxExpected(element(by.id('homeScreen'))).toBeVisible();

    // Take screenshot for visual regression
    await device.takeScreenshot('homepage-dark');
  });

  it('should match dashboard screen in light theme', async () => {
    await element(by.id('dashboardScreen')).tap();
    await detoxExpected(element(by.id('dashboardScreen'))).toBeVisible();

    await device.takeScreenshot('dashboard-light');
  });

  it('should match dashboard screen in dark theme', async () => {
    await element(by.id('themeToggle')).tap();
    await element(by.id('dashboardScreen')).tap();
    await detoxExpected(element(by.id('dashboardScreen'))).toBeVisible();

    await device.takeScreenshot('dashboard-dark');
  });

  it('should match leagues list in light theme', async () => {
    await element(by.id('leaguesScreen')).tap();
    await detoxExpected(element(by.id('leaguesScreen'))).toBeVisible();

    await device.takeScreenshot('leagues-light');
  });

  it('should match leagues list in dark theme', async () => {
    await element(by.id('themeToggle')).tap();
    await element(by.id('leaguesScreen')).tap();
    await detoxExpected(element(by.id('leaguesScreen'))).toBeVisible();

    await device.takeScreenshot('leagues-dark');
  });
});