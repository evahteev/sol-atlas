/**
 * Safe i18n utilities to prevent INVALID_MESSAGE errors
 * Provides helper functions to safely handle translation parameters
 */

/**
 * Safely sanitize translation parameters to prevent undefined/null values
 */
export function sanitizeTranslationParams(
  params?: Record<string, unknown>
): Record<string, string> {
  if (!params) return {}

  const sanitized: Record<string, string> = {}

  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined) {
      sanitized[key] = ''
    } else if (typeof value === 'string') {
      sanitized[key] = value
    } else {
      sanitized[key] = String(value)
    }
  }

  return sanitized
}

/**
 * Create a safe translation function that validates parameters
 */
export function createSafeTranslation<T extends (...args: unknown[]) => string>(
  translationFunction: T
) {
  return function safeT(key: Parameters<T>[0], params?: Record<string, unknown>): string {
    try {
      const sanitizedParams = sanitizeTranslationParams(params)
      return translationFunction(key, sanitizedParams)
    } catch (error) {
      console.error('🌐 Safe translation error:', error, { key, params })
      return `[${key}]`
    }
  }
}

/**
 * Validate that required parameters are present and not empty
 */
export function validateTranslationParams(
  params: Record<string, unknown>,
  requiredKeys: string[]
): { valid: boolean; missing: string[] } {
  const missing: string[] = []

  for (const key of requiredKeys) {
    const value = params[key]
    if (value === null || value === undefined || value === '') {
      missing.push(key)
    }
  }

  return {
    valid: missing.length === 0,
    missing,
  }
}

/**
 * Safe currency parameter handling for translations
 */
export function safeCurrencyParam(currency?: string | null): string {
  if (!currency || currency.trim() === '') {
    return 'TOKEN'
  }
  return currency.trim()
}

/**
 * Safe app name parameter handling for translations
 */
export function safeAppNameParam(appName?: string | null): string {
  if (!appName || appName.trim() === '') {
    return 'Axioma 24'
  }
  return appName.trim()
}
