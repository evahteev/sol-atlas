/**
 * Testing utilities for internationalization
 * Provides helpers for testing translation functionality
 */
import { routing } from '@/i18n/routing'

/**
 * Test data for internationalization testing
 */
export const I18N_TEST_DATA = {
  locales: routing.locales,
  defaultLocale: routing.defaultLocale,
  sampleTranslationKeys: [
    'ProfileBar.joinUs',
    'ProfileBar.telegram',
    'AIFeed.title',
    'Tasks.title',
    'Staking.title',
    'Tokens.title',
    'Swap.loading.warmingUp',
  ],
  sampleMetadataKeys: [
    'Metadata.defaultTitle',
    'Metadata.pages.aifeed.title',
    'Metadata.pages.tasks.title',
    'Metadata.pages.staking.title',
  ],
}

/**
 * Mock translation function for testing
 */
export function createMockTranslationFunction(locale: string = 'en') {
  return function mockT(key: string, params?: Record<string, unknown>): string {
    // Return a test translation that includes the key and locale for verification
    let translation = `[${locale}:${key}]`

    // Handle parameters if provided
    if (params) {
      Object.entries(params).forEach(([paramKey, value]) => {
        translation = translation.replace(`{{${paramKey}}}`, String(value))
      })
    }

    return translation
  }
}

/**
 * Test helper to validate translation key structure
 */
export function validateTranslationKeyStructure(
  messages: Record<string, unknown>,
  expectedNamespaces: string[]
): { valid: boolean; issues: string[] } {
  const issues: string[] = []

  // Check if all expected namespaces exist
  for (const namespace of expectedNamespaces) {
    if (!(namespace in messages)) {
      issues.push(`Missing namespace: ${namespace}`)
    } else if (typeof messages[namespace] !== 'object') {
      issues.push(`Invalid namespace type: ${namespace} should be an object`)
    }
  }

  // Check for empty namespaces
  for (const [namespace, content] of Object.entries(messages)) {
    if (typeof content === 'object' && content !== null) {
      const keys = Object.keys(content)
      if (keys.length === 0) {
        issues.push(`Empty namespace: ${namespace}`)
      }
    }
  }

  return {
    valid: issues.length === 0,
    issues,
  }
}

/**
 * Test helper to validate locale consistency
 */
export function validateLocaleConsistency(
  primaryMessages: Record<string, unknown>,
  secondaryMessages: Record<string, unknown>,
  primaryLocale: string,
  secondaryLocale: string
): { consistent: boolean; issues: string[] } {
  const issues: string[] = []

  // Get all keys from both locales
  const primaryKeys = getAllTranslationKeysFlat(primaryMessages)
  const secondaryKeys = getAllTranslationKeysFlat(secondaryMessages)

  // Find missing keys in secondary locale
  const missingInSecondary = primaryKeys.filter((key) => !secondaryKeys.includes(key))
  if (missingInSecondary.length > 0) {
    issues.push(`Keys missing in ${secondaryLocale}: ${missingInSecondary.join(', ')}`)
  }

  // Find extra keys in secondary locale
  const extraInSecondary = secondaryKeys.filter((key) => !primaryKeys.includes(key))
  if (extraInSecondary.length > 0) {
    issues.push(`Extra keys in ${secondaryLocale}: ${extraInSecondary.join(', ')}`)
  }

  return {
    consistent: issues.length === 0,
    issues,
  }
}

/**
 * Helper to get all translation keys in flat format
 */
function getAllTranslationKeysFlat(messages: Record<string, unknown>, prefix = ''): string[] {
  const keys: string[] = []

  for (const [key, value] of Object.entries(messages)) {
    const fullKey = prefix ? `${prefix}.${key}` : key

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      keys.push(...getAllTranslationKeysFlat(value as Record<string, unknown>, fullKey))
    } else {
      keys.push(fullKey)
    }
  }

  return keys
}

/**
 * Test utility to simulate locale switching
 */
export function simulateLocaleSwitch(
  fromLocale: string,
  toLocale: string,
  currentPath: string
): { newPath: string; validTransition: boolean } {
  const validLocales = routing.locales
  const validTransition =
    validLocales.includes(fromLocale as 'en' | 'ru') &&
    validLocales.includes(toLocale as 'en' | 'ru')

  let newPath = currentPath

  if (validTransition) {
    // Handle locale prefix logic
    if (routing.localePrefix === 'as-needed') {
      const defaultLocale = routing.defaultLocale

      // Remove current locale prefix if it exists
      const localePattern = new RegExp(`^/(${validLocales.join('|')})(/|$)`)
      const pathWithoutLocale = currentPath.replace(localePattern, '$2') || '/'

      // Add new locale prefix if not default locale
      if (toLocale !== defaultLocale) {
        newPath = `/${toLocale}${pathWithoutLocale === '/' ? '' : pathWithoutLocale}`
      } else {
        newPath = pathWithoutLocale
      }
    }
  }

  return { newPath, validTransition }
}

/**
 * Test helper for metadata validation
 */
export function validateMetadataTranslations(messages: Record<string, unknown>): {
  valid: boolean
  issues: string[]
} {
  const issues: string[] = []

  // Check if Metadata namespace exists
  if (!messages.Metadata) {
    issues.push('Missing Metadata namespace')
    return { valid: false, issues }
  }

  const metadata = messages.Metadata as Record<string, unknown>

  // Check required metadata fields
  const requiredFields = ['defaultTitle', 'defaultDescription', 'siteTitle', 'siteDescription']
  for (const field of requiredFields) {
    if (!(field in metadata) || typeof metadata[field] !== 'string') {
      issues.push(`Missing or invalid metadata field: ${field}`)
    }
  }

  // Check pages metadata
  if (!metadata.pages || typeof metadata.pages !== 'object') {
    issues.push('Missing or invalid pages metadata')
  } else {
    const pages = metadata.pages as Record<string, unknown>
    const expectedPages = ['aifeed', 'tasks', 'staking', 'tokens', 'swap']
    for (const page of expectedPages) {
      if (!pages[page]) {
        issues.push(`Missing metadata for page: ${page}`)
      } else {
        const pageMetadata = pages[page] as Record<string, unknown>
        if (!pageMetadata.title || !pageMetadata.description) {
          issues.push(`Incomplete metadata for page: ${page}`)
        }
      }
    }
  }

  return {
    valid: issues.length === 0,
    issues,
  }
}

/**
 * Performance test helper
 */
export function measureTranslationPerformance(
  translationFunction: (key: string) => string,
  keys: string[],
  iterations: number = 100
): { averageTime: number; totalTime: number; keysPerSecond: number } {
  const startTime = performance.now()

  for (let i = 0; i < iterations; i++) {
    for (const key of keys) {
      translationFunction(key)
    }
  }

  const endTime = performance.now()
  const totalTime = endTime - startTime
  const averageTime = totalTime / iterations
  const totalKeysProcessed = keys.length * iterations
  const keysPerSecond = (totalKeysProcessed / totalTime) * 1000

  return {
    averageTime,
    totalTime,
    keysPerSecond,
  }
}

/**
 * Test helper to validate environment configuration
 */
export function validateI18nEnvironment(): { valid: boolean; issues: string[] } {
  const issues: string[] = []

  // Check if default locale environment variable is set
  const defaultLocale = process.env.NEXT_PUBLIC_DEFAULT_LOCALE
  if (!defaultLocale) {
    issues.push('NEXT_PUBLIC_DEFAULT_LOCALE environment variable not set')
  } else if (!routing.locales.includes(defaultLocale as 'en' | 'ru')) {
    issues.push(
      `Invalid default locale: ${defaultLocale}. Must be one of: ${routing.locales.join(', ')}`
    )
  }

  // Check if routing configuration is valid
  if (!routing.locales || routing.locales.length < 1) {
    issues.push('No locales configured in routing')
  }

  if (!routing.defaultLocale) {
    issues.push('No default locale configured in routing')
  }

  return {
    valid: issues.length === 0,
    issues,
  }
}
