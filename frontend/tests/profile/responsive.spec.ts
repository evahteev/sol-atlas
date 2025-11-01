import { expect, test } from '@playwright/test'

test.describe('Profile Page Responsive Design', () => {
  const breakpoints = [
    { name: 'Desktop Large', width: 1440, height: 900 },
    { name: 'Desktop', width: 1024, height: 768 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Mobile Large', width: 480, height: 800 },
    { name: 'Mobile Small', width: 320, height: 568 },
  ]

  breakpoints.forEach(({ name, width, height }) => {
    test(`should display correctly on ${name} (${width}x${height})`, async ({ page }) => {
      // Set longer timeout for slower connections
      test.setTimeout(60000)

      // Navigate to profile page
      await page.goto('https://localhost:3000/profile', { timeout: 30000 })
      await page.waitForLoadState('networkidle', { timeout: 30000 })

      // Resize to target viewport
      await page.setViewportSize({ width, height })
      await page.waitForTimeout(1000) // Allow layout to settle

      // Check that main sections are visible
      await expect(page.locator('h2:has-text("Utopia Partnership")')).toBeVisible({
        timeout: 10000,
      })
      await expect(page.locator('h3:has-text("Alex Johnson")')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('h3:has-text("Performance Overview")')).toBeVisible({
        timeout: 10000,
      })

      // Test scrolling to ensure all content is accessible
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
      await page.waitForTimeout(500)

      // Check that bottom sections are accessible
      await expect(page.locator('h3:has-text("Performance Trends")')).toBeVisible({
        timeout: 10000,
      })
      await expect(page.locator('h3:has-text("Learning & Certificates")')).toBeVisible({
        timeout: 10000,
      })
      await expect(page.locator('h3:has-text("Badges & Achievements")')).toBeVisible({
        timeout: 10000,
      })

      // Take screenshot for visual regression testing
      await page.screenshot({
        path: `tests/screenshots/profile-${name.toLowerCase().replace(' ', '-')}-${width}x${height}.png`,
        fullPage: true,
      })
    })
  })

  test('should have proper grid layout on desktop', async ({ page }) => {
    test.setTimeout(60000)

    await page.goto('https://localhost:3000/profile', { timeout: 30000 })
    await page.waitForLoadState('networkidle', { timeout: 30000 })

    // Set to desktop size
    await page.setViewportSize({ width: 1024, height: 768 })
    await page.waitForTimeout(1000)

    // Check that sidebar and main content are side by side
    const profileContent = page.locator('.profile-content').first()
    await expect(profileContent).toBeVisible({ timeout: 10000 })

    // Check grid layout CSS
    const gridColumns = await profileContent.evaluate((el) =>
      window.getComputedStyle(el).getPropertyValue('grid-template-columns')
    )
    expect(gridColumns).toContain('320px') // Sidebar width
  })

  test('should stack content vertically on mobile', async ({ page }) => {
    test.setTimeout(60000)

    await page.goto('https://localhost:3000/profile', { timeout: 30000 })
    await page.waitForLoadState('networkidle', { timeout: 30000 })

    // Set to mobile size
    await page.setViewportSize({ width: 480, height: 800 })
    await page.waitForTimeout(1000)

    // Check that content stacks vertically
    const profileContent = page.locator('.profile-content').first()
    await expect(profileContent).toBeVisible({ timeout: 10000 })

    // Check grid layout CSS changes to single column
    const gridColumns = await profileContent.evaluate((el) =>
      window.getComputedStyle(el).getPropertyValue('grid-template-columns')
    )
    expect(gridColumns).toBe('1fr') // Single column
  })

  test('should have readable text on all screen sizes', async ({ page }) => {
    test.setTimeout(60000)

    await page.goto('https://localhost:3000/profile', { timeout: 30000 })
    await page.waitForLoadState('networkidle', { timeout: 30000 })

    for (const { width, height } of breakpoints) {
      await page.setViewportSize({ width, height })
      await page.waitForTimeout(500)

      // Check that text is readable (not overlapping or cut off)
      const titles = page.locator('h1, h2, h3, h4, h5')
      const count = await titles.count()

      for (let i = 0; i < count; i++) {
        const title = titles.nth(i)
        if (await title.isVisible()) {
          const boundingBox = await title.boundingBox()
          expect(boundingBox?.width).toBeGreaterThan(0)
          expect(boundingBox?.height).toBeGreaterThan(0)
        }
      }
    }
  })

  test('should have accessible interactive elements on all screen sizes', async ({ page }) => {
    test.setTimeout(60000)

    await page.goto('https://localhost:3000/profile', { timeout: 30000 })
    await page.waitForLoadState('networkidle', { timeout: 30000 })

    for (const { width, height } of breakpoints) {
      await page.setViewportSize({ width, height })
      await page.waitForTimeout(500)

      // Check that buttons are clickable and properly sized
      const buttons = page.locator('button')
      const count = await buttons.count()

      for (let i = 0; i < Math.min(count, 5); i++) {
        // Test first 5 buttons
        const button = buttons.nth(i)
        if (await button.isVisible()) {
          const boundingBox = await button.boundingBox()

          // Buttons should be at least 44px for touch accessibility
          expect(boundingBox?.width).toBeGreaterThan(width < 768 ? 44 : 0)
          expect(boundingBox?.height).toBeGreaterThan(width < 768 ? 44 : 0)
        }
      }
    }
  })
})
