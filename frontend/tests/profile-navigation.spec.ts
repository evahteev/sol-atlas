import { expect, test } from '@playwright/test'

test.describe('Profile Navigation', () => {
  test('should navigate to profile page when clicking user icon in ProfileBar', async ({
    page,
  }) => {
    // Set longer timeout for slower connections
    test.setTimeout(60000) // 60 seconds

    // Navigate to the main page
    await page.goto('https://localhost:3000', { timeout: 30000 })

    // Wait for the page to load with longer timeout
    await page.waitForLoadState('networkidle', { timeout: 30000 })

    // Find the user icon in the ProfileBar (header)
    const userIcon = page
      .locator(
        '[data-testid="profile-toggle"], .profile-toggle, button[aria-label*="profile"], button[aria-label*="user"]'
      )
      .first()

    // Verify the user icon exists
    await expect(userIcon).toBeVisible({ timeout: 10000 })

    // Click on the user icon
    await userIcon.click()

    // Wait for navigation to complete with longer timeout
    await page.waitForURL('**/profile', { timeout: 30000 })

    // Verify we're on the profile page
    await expect(page).toHaveURL(/.*\/profile/)

    // Verify profile page content is visible
    await expect(page.locator('h1, .profile-title, [data-testid="profile-title"]')).toBeVisible({
      timeout: 10000,
    })
  })
})
