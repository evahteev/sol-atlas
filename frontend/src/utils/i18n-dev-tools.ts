/**
 * Development tools for internationalization debugging and optimization
 * These utilities should only be used in development environment
 */

/**
 * Analyze translation usage and find potential optimizations
 */
export class I18nAnalyzer {
  private usedKeys = new Set<string>()
  private availableKeys = new Set<string>()
  private loadedNamespaces = new Set<string>()

  /**
   * Record that a translation key was used
   */
  recordKeyUsage(key: string, namespace?: string) {
    const fullKey = namespace ? `${namespace}.${key}` : key
    this.usedKeys.add(fullKey)
  }

  /**
   * Record available translation keys from messages
   */
  recordAvailableKeys(messages: Record<string, unknown>, namespace = '') {
    for (const [key, value] of Object.entries(messages)) {
      const fullKey = namespace ? `${namespace}.${key}` : key

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        this.recordAvailableKeys(value as Record<string, unknown>, fullKey)
        this.loadedNamespaces.add(key)
      } else {
        this.availableKeys.add(fullKey)
      }
    }
  }

  /**
   * Find unused translation keys
   */
  getUnusedKeys(): string[] {
    return Array.from(this.availableKeys).filter((key) => !this.usedKeys.has(key))
  }

  /**
   * Find missing translation keys (used but not available)
   */
  getMissingKeys(): string[] {
    return Array.from(this.usedKeys).filter((key) => !this.availableKeys.has(key))
  }

  /**
   * Get translation usage statistics
   */
  getUsageStats() {
    const total = this.availableKeys.size
    const used = this.usedKeys.size
    const unused = this.getUnusedKeys().length
    const missing = this.getMissingKeys().length

    return {
      total,
      used,
      unused,
      missing,
      usageRate: total > 0 ? (used / total) * 100 : 0,
      loadedNamespaces: Array.from(this.loadedNamespaces),
    }
  }

  /**
   * Generate a report of translation usage
   */
  generateReport(): string {
    const stats = this.getUsageStats()
    const unusedKeys = this.getUnusedKeys()
    const missingKeys = this.getMissingKeys()

    let report = '🌐 Translation Usage Report\n'
    report += '========================\n\n'

    report += `📊 Statistics:\n`
    report += `  Total keys: ${stats.total}\n`
    report += `  Used keys: ${stats.used}\n`
    report += `  Unused keys: ${stats.unused}\n`
    report += `  Missing keys: ${stats.missing}\n`
    report += `  Usage rate: ${stats.usageRate.toFixed(1)}%\n\n`

    report += `📦 Loaded namespaces: ${stats.loadedNamespaces.join(', ')}\n\n`

    if (unusedKeys.length > 0) {
      report += `🗑️  Unused keys (consider removing):\n`
      unusedKeys.slice(0, 10).forEach((key) => {
        report += `  - ${key}\n`
      })
      if (unusedKeys.length > 10) {
        report += `  ... and ${unusedKeys.length - 10} more\n`
      }
      report += '\n'
    }

    if (missingKeys.length > 0) {
      report += `❌ Missing keys (need translation):\n`
      missingKeys.forEach((key) => {
        report += `  - ${key}\n`
      })
      report += '\n'
    }

    return report
  }

  /**
   * Reset analyzer state
   */
  reset() {
    this.usedKeys.clear()
    this.availableKeys.clear()
    this.loadedNamespaces.clear()
  }
}

// Global analyzer instance for development
export const i18nAnalyzer = new I18nAnalyzer()

/**
 * Development hook to track translation usage
 * Only active in development mode
 */
export function trackTranslationUsage(key: string, namespace?: string) {
  if (process.env.NODE_ENV === 'development') {
    i18nAnalyzer.recordKeyUsage(key, namespace)
  }
}

/**
 * Log translation analysis to console
 * Only active in development mode
 */
export function logTranslationAnalysis() {
  if (process.env.NODE_ENV === 'development') {
    console.log(i18nAnalyzer.generateReport())
  }
}

/**
 * Validate that all required translation keys exist
 */
export function validateRequiredTranslations(
  requiredKeys: string[],
  messages: Record<string, unknown>,
  locale: string
): { valid: boolean; missingKeys: string[] } {
  const missingKeys: string[] = []

  for (const key of requiredKeys) {
    const keyPath = key.split('.')
    let current: unknown = messages

    for (const segment of keyPath) {
      if (current && typeof current === 'object' && !Array.isArray(current) && segment in current) {
        current = (current as Record<string, unknown>)[segment]
      } else {
        missingKeys.push(key)
        break
      }
    }
  }

  if (missingKeys.length > 0 && process.env.NODE_ENV === 'development') {
    console.warn(`🌐 Missing required translations for ${locale}:`, missingKeys)
  }

  return {
    valid: missingKeys.length === 0,
    missingKeys,
  }
}

/**
 * Check for translation consistency across locales
 */
export function checkTranslationConsistency(
  enMessages: Record<string, unknown>,
  otherMessages: Record<string, unknown>,
  otherLocale: string
): { missingInOther: string[]; extraInOther: string[] } {
  const enKeys = getAllTranslationKeys(enMessages)
  const otherKeys = getAllTranslationKeys(otherMessages)

  const missingInOther = enKeys.filter((key) => !otherKeys.includes(key))
  const extraInOther = otherKeys.filter((key) => !enKeys.includes(key))

  if (process.env.NODE_ENV === 'development') {
    if (missingInOther.length > 0) {
      console.warn(`🌐 Keys missing in ${otherLocale}:`, missingInOther)
    }
    if (extraInOther.length > 0) {
      console.warn(`🌐 Extra keys in ${otherLocale}:`, extraInOther)
    }
  }

  return { missingInOther, extraInOther }
}

/**
 * Recursively get all translation keys from a messages object
 */
function getAllTranslationKeys(messages: Record<string, unknown>, prefix = ''): string[] {
  const keys: string[] = []

  for (const [key, value] of Object.entries(messages)) {
    const fullKey = prefix ? `${prefix}.${key}` : key

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      keys.push(...getAllTranslationKeys(value as Record<string, unknown>, fullKey))
    } else {
      keys.push(fullKey)
    }
  }

  return keys
}
