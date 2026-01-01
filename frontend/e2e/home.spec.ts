import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should display the home page', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('Sistema de Prefactibilidad Ambiental Minera');
  });

  test('should navigate to new project', async ({ page }) => {
    await page.goto('/');

    await page.click('text=Nuevo Proyecto');

    await expect(page).toHaveURL(/\/proyecto/);
  });

  test('should navigate to history', async ({ page }) => {
    await page.goto('/');

    await page.click('text=Ver Historial');

    await expect(page).toHaveURL('/historial');
  });
});
