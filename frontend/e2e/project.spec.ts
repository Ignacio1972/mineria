import { test, expect } from '@playwright/test';

test.describe('Project Page', () => {
  test('should display the project view', async ({ page }) => {
    await page.goto('/proyecto');

    // Should have sidebar
    await expect(page.locator('.app-sidebar, [class*="sidebar"]')).toBeVisible();

    // Should have map container
    await expect(page.locator('[class*="map"], .ol-viewport')).toBeVisible();
  });

  test('should display project form in sidebar', async ({ page }) => {
    await page.goto('/proyecto');

    // Look for form elements
    await expect(page.getByPlaceholder(/nombre/i)).toBeVisible();
  });

  test('should have draw tools', async ({ page }) => {
    await page.goto('/proyecto');

    // Look for draw tools
    await expect(page.locator('[class*="draw"], button[aria-label*="dibujar"]').first()).toBeVisible();
  });
});
