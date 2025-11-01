/**
 * Performance monitoring utilities for internationalization
 */

interface I18nPerformanceMetrics {
  translationLoadTime: number
  translationCacheHits: number
  translationCacheMisses: number
  totalTranslations: number
}

class I18nPerformanceMonitor {
  private metrics: I18nPerformanceMetrics = {
    translationLoadTime: 0,
    translationCacheHits: 0,
    translationCacheMisses: 0,
    totalTranslations: 0,
  }

  /**
   * Record translation loading time
   */
  recordTranslationLoadTime(time: number) {
    this.metrics.translationLoadTime += time
  }

  /**
   * Record cache hit
   */
  recordCacheHit() {
    this.metrics.translationCacheHits++
  }

  /**
   * Record cache miss
   */
  recordCacheMiss() {
    this.metrics.translationCacheMisses++
  }

  /**
   * Record total translations loaded
   */
  recordTranslationsLoaded(count: number) {
    this.metrics.totalTranslations = count
  }

  /**
   * Get current metrics
   */
  getMetrics(): I18nPerformanceMetrics {
    return { ...this.metrics }
  }

  /**
   * Get cache hit ratio
   */
  getCacheHitRatio(): number {
    const total = this.metrics.translationCacheHits + this.metrics.translationCacheMisses
    return total > 0 ? this.metrics.translationCacheHits / total : 0
  }

  /**
   * Reset metrics
   */
  reset() {
    this.metrics = {
      translationLoadTime: 0,
      translationCacheHits: 0,
      translationCacheMisses: 0,
      totalTranslations: 0,
    }
  }

  /**
   * Log performance summary to console (development only)
   */
  logPerformanceSummary() {
    if (process.env.NODE_ENV === 'development') {
      console.group('🌐 I18n Performance Metrics')
      console.log(`Translation Load Time: ${this.metrics.translationLoadTime.toFixed(2)}ms`)
      console.log(`Cache Hit Ratio: ${(this.getCacheHitRatio() * 100).toFixed(1)}%`)
      console.log(`Total Translations: ${this.metrics.totalTranslations}`)
      console.log(`Cache Hits: ${this.metrics.translationCacheHits}`)
      console.log(`Cache Misses: ${this.metrics.translationCacheMisses}`)
      console.groupEnd()
    }
  }
}

// Global performance monitor instance
export const i18nPerformanceMonitor = new I18nPerformanceMonitor()

/**
 * Higher-order function to measure translation loading performance
 */
export function withTranslationPerformanceTracking<T extends (...args: unknown[]) => unknown>(
  fn: T,
  name: string
): T {
  return ((...args: unknown[]) => {
    const startTime = performance.now()
    const result = fn(...args)

    if (result instanceof Promise) {
      return result.then((value) => {
        const endTime = performance.now()
        i18nPerformanceMonitor.recordTranslationLoadTime(endTime - startTime)

        if (process.env.NODE_ENV === 'development') {
          console.log(`🌐 Translation ${name} took ${(endTime - startTime).toFixed(2)}ms`)
        }

        return value
      })
    } else {
      const endTime = performance.now()
      i18nPerformanceMonitor.recordTranslationLoadTime(endTime - startTime)

      if (process.env.NODE_ENV === 'development') {
        console.log(`🌐 Translation ${name} took ${(endTime - startTime).toFixed(2)}ms`)
      }

      return result
    }
  }) as T
}

/**
 * Utility to measure bundle size impact of translations
 */
export function getTranslationBundleSize(messages: Record<string, unknown>): number {
  return JSON.stringify(messages).length
}

/**
 * Performance-optimized translation key checker
 * Validates translation keys exist without loading full translation object
 */
export function validateTranslationKeys(
  keys: string[],
  messages: Record<string, unknown>,
  namespace?: string
): { valid: string[]; invalid: string[] } {
  const valid: string[] = []
  const invalid: string[] = []

  const targetMessages = namespace ? messages[namespace] : messages

  for (const key of keys) {
    const keyPath = key.split('.')
    let current = targetMessages

    let isValid = true
    for (const segment of keyPath) {
      if (current && typeof current === 'object' && !Array.isArray(current) && segment in current) {
        current = (current as Record<string, unknown>)[segment]
      } else {
        isValid = false
        break
      }
    }

    if (isValid && typeof current === 'string') {
      valid.push(key)
    } else {
      invalid.push(key)
    }
  }

  return { valid, invalid }
}
