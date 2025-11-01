import { getRequestConfig } from 'next-intl/server'

import { getTranslationBundleSize, i18nPerformanceMonitor } from '@/utils/i18n-performance'

import { routing } from './routing'

// Cache for loaded messages to avoid repeated imports
const messageCache = new Map<string, Record<string, unknown>>()

export default getRequestConfig(async ({ requestLocale }) => {
  // This typically corresponds to the `[locale]` segment
  let locale = await requestLocale

  // Ensure that a valid locale is used
  if (!locale || !routing.locales.includes(locale as 'en' | 'ru')) {
    locale = routing.defaultLocale
  }

  // Check cache first for performance optimization
  if (messageCache.has(locale)) {
    i18nPerformanceMonitor.recordCacheHit()
    return {
      locale,
      messages: messageCache.get(locale),
    }
  }

  // Load messages and cache them
  i18nPerformanceMonitor.recordCacheMiss()
  const startTime = performance.now()

  const messages = (await import(`../../messages/${locale}.json`)).default
  messageCache.set(locale, messages)

  const endTime = performance.now()
  i18nPerformanceMonitor.recordTranslationLoadTime(endTime - startTime)

  // Record bundle size and translation count in development
  if (process.env.NODE_ENV === 'development') {
    const bundleSize = getTranslationBundleSize(messages)
    const translationCount = Object.keys(messages).reduce((count, namespace) => {
      return (
        count +
        (typeof messages[namespace] === 'object' ? Object.keys(messages[namespace]).length : 1)
      )
    }, 0)

    i18nPerformanceMonitor.recordTranslationsLoaded(translationCount)
    console.log(
      `🌐 Loaded ${locale} translations: ${translationCount} keys, ${(bundleSize / 1024).toFixed(2)}KB`
    )
  }

  return {
    locale,
    messages,
    onError: (error) => {
      console.error('🌐 Translation error:', error)
      // In production, log to monitoring service
      if (process.env.NODE_ENV === 'production') {
        // Log to external service if needed
      }
    },
    getMessageFallback: ({ namespace, key, error }) => {
      console.warn(`🌐 Missing/invalid translation: ${namespace}.${key}`, error)
      return `${namespace}.${key}`
    },
    formats: {
      // Add default formats to handle various parameter types
      number: {
        currency: {
          style: 'currency',
          currency: 'USD',
        },
      },
    },
    // Disable strict mode for ICU MessageFormat to handle edge cases
    defaultTranslationValues: {
      // Provide default values for common parameters
      appName: 'GuruNetwork',
      currency: 'TOKEN',
    },
  }
})
