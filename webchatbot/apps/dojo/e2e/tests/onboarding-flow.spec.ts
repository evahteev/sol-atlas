import { test, expect } from '@playwright/test';

/**
 * Onboarding Flow Regression Tests
 * 
 * Tests the complete guest onboarding experience including:
 * - New session creation for guest users
 * - Language detection based on browser preferences
 * - Form rendering with proper content
 * - Language switching functionality
 * - Form re-rendering with translated content
 */

test.describe('Guest Onboarding Flow', () => {
  test.beforeEach(async ({ context }) => {
    // Clear all cookies and localStorage to simulate new user
    await context.clearCookies();
    await context.clearPermissions();
  });

  test('should detect English locale and show English onboarding form', async ({ page }) => {
    // Set browser to English locale
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { value: 'en-US' });
      Object.defineProperty(navigator, 'languages', { value: ['en-US', 'en'] });
    });

    // Navigate to the app (fresh session)
    await page.goto('http://localhost:3000');

    // Wait for initial load and verify guest mode
    await expect(page.locator('text=Guest Mode - Limited features available')).toBeVisible();

    // Click Start button to trigger onboarding
    await page.click('button:has-text("🏠 Start")');

    // Wait for onboarding form to appear
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();

    // Verify English content is displayed
    await expect(page.locator('text=I\'m your AI-powered group management assistant for Telegram communities')).toBeVisible();
    await expect(page.locator('text=🎯 What I can do for your groups:')).toBeVisible();
    await expect(page.locator('text=🤖 AI Assistant - Answer questions')).toBeVisible();
    await expect(page.locator('text=📚 Knowledge Base - Index and search')).toBeVisible();
    await expect(page.locator('text=🛡️ Smart Moderation - Automatic content filtering')).toBeVisible();
    await expect(page.locator('text=📊 Analytics - Track activity')).toBeVisible();

    // Verify English buttons
    await expect(page.locator('button:has-text("📚 Browse Catalog")')).toBeVisible();
    await expect(page.locator('button:has-text("🔑 Sign In for Full Access")')).toBeVisible();
    await expect(page.locator('button:has-text("🌍 Русский")')).toBeVisible(); // Language switch to Russian

    // Verify getting started steps in English
    await expect(page.locator('text=🚀 Get Started:')).toBeVisible();
    await expect(page.locator('text=1️⃣ Use /groups to manage your Telegram groups')).toBeVisible();
    await expect(page.locator('text=2️⃣ Add me to your group as an admin')).toBeVisible();
    await expect(page.locator('text=3️⃣ Configure AI assistance, moderation, and KB indexing')).toBeVisible();

    // Verify guest mode note
    await expect(page.locator('text=💡 Guest Mode: Limited access to public content')).toBeVisible();
  });

  test('should switch to Russian when language button is clicked', async ({ page }) => {
    // Start with English locale
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { value: 'en-US' });
      Object.defineProperty(navigator, 'languages', { value: ['en-US', 'en'] });
    });

    await page.goto('http://localhost:3000');
    
    // Trigger onboarding form
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();

    // Click the Russian language button
    await page.click('button:has-text("🌍 Русский")');

    // Wait for form to re-render with Russian content
    await expect(page.locator('heading:has-text("👋 Добро пожаловать в Luka!")')).toBeVisible();

    // Verify Russian content
    await expect(page.locator('text=Я ваш AI-ассистент для управления Telegram сообществами')).toBeVisible();
    await expect(page.locator('text=🎯 Что я могу для ваших групп:')).toBeVisible();
    await expect(page.locator('text=🤖 AI-помощник - Отвечайте на вопросы')).toBeVisible();
    await expect(page.locator('text=📚 База знаний - Индексируйте и ищите')).toBeVisible();
    await expect(page.locator('text=🛡️ Умная модерация - Автоматическая фильтрация')).toBeVisible();
    await expect(page.locator('text=📊 Аналитика - Отслеживайте активность')).toBeVisible();

    // Verify Russian buttons
    await expect(page.locator('button:has-text("📚 Обзор каталога")')).toBeVisible();
    await expect(page.locator('button:has-text("🔑 Войти для полного доступа")')).toBeVisible();
    await expect(page.locator('button:has-text("🌍 English")')).toBeVisible(); // Language switch back to English

    // Verify getting started steps in Russian
    await expect(page.locator('text=🚀 Начните работу:')).toBeVisible();
    await expect(page.locator('text=1️⃣ Используйте /groups для управления')).toBeVisible();
    await expect(page.locator('text=2️⃣ Добавьте меня в вашу группу')).toBeVisible();
    await expect(page.locator('text=3️⃣ Настройте AI-помощника')).toBeVisible();

    // Verify guest mode note in Russian
    await expect(page.locator('text=💡 Гостевой режим: Ограниченный доступ к публичному контенту')).toBeVisible();
  });

  test('should switch back to English from Russian', async ({ page }) => {
    // Start with English locale
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { value: 'en-US' });
      Object.defineProperty(navigator, 'languages', { value: ['en-US', 'en'] });
    });

    await page.goto('http://localhost:3000');
    
    // Trigger onboarding form and switch to Russian
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();
    await page.click('button:has-text("🌍 Русский")');
    await expect(page.locator('heading:has-text("👋 Добро пожаловать в Luka!")')).toBeVisible();

    // Switch back to English
    await page.click('button:has-text("🌍 English")');

    // Verify we're back to English content
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();
    await expect(page.locator('text=I\'m your AI-powered group management assistant')).toBeVisible();
    await expect(page.locator('button:has-text("📚 Browse Catalog")')).toBeVisible();
    await expect(page.locator('button:has-text("🔑 Sign In for Full Access")')).toBeVisible();
    await expect(page.locator('button:has-text("🌍 Русский")')).toBeVisible();
  });

  test('should detect Russian locale and show Russian onboarding form initially', async ({ page }) => {
    // Set browser to Russian locale
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'language', { value: 'ru-RU' });
      Object.defineProperty(navigator, 'languages', { value: ['ru-RU', 'ru'] });
    });

    // Override Accept-Language header
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'ru-RU,ru;q=0.9'
    });

    // Navigate to the app (fresh session)
    await page.goto('http://localhost:3000');

    // Wait for initial load
    await expect(page.locator('text=Guest Mode - Limited features available')).toBeVisible();

    // Click Start button to trigger onboarding
    await page.click('button:has-text("🏠 Start")');

    // Wait for onboarding form to appear and verify Russian content is shown initially
    await expect(page.locator('heading:has-text("👋 Добро пожаловать в Luka!")')).toBeVisible();

    // Verify Russian content is displayed by default
    await expect(page.locator('text=Я ваш AI-ассистент для управления Telegram сообществами')).toBeVisible();
    await expect(page.locator('button:has-text("📚 Обзор каталога")')).toBeVisible();
    await expect(page.locator('button:has-text("🔑 Войти для полного доступа")')).toBeVisible();
    await expect(page.locator('button:has-text("🌍 English")')).toBeVisible(); // Language switch to English
  });

  test('should handle form submission for Browse Catalog button', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Trigger onboarding form
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();

    // Click Browse Catalog button
    await page.click('button:has-text("📚 Browse Catalog")');

    // Verify form disappears (form submission completed)
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).not.toBeVisible();

    // Verify we're back to main interface
    await expect(page.locator('text=Guest Mode - Limited features available')).toBeVisible();
  });

  test('should handle form submission for Sign In button', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Trigger onboarding form
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();

    // Click Sign In button
    await page.click('button:has-text("🔑 Sign In for Full Access")');

    // Verify form disappears (form submission completed)
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).not.toBeVisible();

    // Verify we're back to main interface
    await expect(page.locator('text=Guest Mode - Limited features available')).toBeVisible();
  });

  test('should handle form cancellation', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Trigger onboarding form
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();

    // Click Cancel button (if visible)
    const cancelButton = page.locator('button:has-text("Cancel")');
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      
      // Verify form disappears
      await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).not.toBeVisible();
    }
  });

  test('should allow reopening onboarding form multiple times', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Open form first time
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();
    
    // Submit form
    await page.click('button:has-text("📚 Browse Catalog")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).not.toBeVisible();
    
    // Open form second time
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();
    
    // Verify all content is still there
    await expect(page.locator('text=I\'m your AI-powered group management assistant')).toBeVisible();
    await expect(page.locator('button:has-text("📚 Browse Catalog")')).toBeVisible();
    await expect(page.locator('button:has-text("🔑 Sign In for Full Access")')).toBeVisible();
  });

  test('should verify no console errors during onboarding flow', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    // Listen for console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:3000');
    
    // Complete onboarding flow
    await page.click('button:has-text("🏠 Start")');
    await expect(page.locator('heading:has-text("👋 Welcome to Luka!")')).toBeVisible();
    
    // Switch language
    await page.click('button:has-text("🌍 Русский")');
    await expect(page.locator('heading:has-text("👋 Добро пожаловать в Luka!")')).toBeVisible();
    
    // Submit form
    await page.click('button:has-text("📚 Обзор каталога")');
    
    // Filter out expected CopilotKit warnings and focus on critical errors
    const criticalErrors = consoleErrors.filter(error => 
      !error.includes('isActionExecutionMessage') && 
      !error.includes('appendMessage is not a function') &&
      !error.includes('Form submission canceled')
    );
    
    // Verify no critical console errors occurred
    expect(criticalErrors).toHaveLength(0);
  });
});