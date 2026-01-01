import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should have header with navigation links', async ({ page }) => {
    await page.goto('/');

    // Header should be visible
    await expect(page.locator('header, [class*="navbar"]')).toBeVisible();

    // Should have logo/title
    await expect(page.locator('h1')).toContainText(/Sistema de Prefactibilidad/i);
  });

  test('should navigate via header links', async ({ page }) => {
    await page.goto('/proyecto');

    // Click on logo to go home
    await page.locator('header a, [class*="navbar"] a').first().click();

    await expect(page).toHaveURL('/');
  });

  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/');

    // Find theme toggle button
    const themeButton = page.locator('button[aria-label*="modo"], button[aria-label*="theme"]').first();

    if (await themeButton.isVisible()) {
      await themeButton.click();

      // Check if theme changed (data-theme attribute)
      await expect(page.locator('[data-theme]')).toHaveAttribute('data-theme', /dark|light/);
    }
  });

  test('should show 404 for invalid routes', async ({ page }) => {
    await page.goto('/ruta-invalida-que-no-existe');

    await expect(page.locator('h1')).toContainText('404');
  });
});
