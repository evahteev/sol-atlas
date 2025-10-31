import { NextRequest, NextResponse } from 'next/server'

import createIntlMiddleware from 'next-intl/middleware'

import { routing } from './routing'

// Create the intl middleware instance
const intlMiddleware = createIntlMiddleware(routing)

/**
 * Determines the appropriate locale for a user based on their preferences and browser settings
 */
export function getUserLocale(
  userLanguageCode?: string | null,
  acceptLanguage?: string | null
): string {
  let locale = routing.defaultLocale

  // Priority 1: Use authenticated user's language_code
  if (userLanguageCode) {
    const userLang = userLanguageCode.toLowerCase()
    if (userLang.startsWith('ru')) {
      locale = 'ru'
    } else if (userLang.startsWith('en')) {
      locale = 'en'
    }
    // Add more language mappings as needed:
    // else if (userLang.startsWith('es')) { locale = 'es' }
  }
  // Priority 2: Fall back to browser language detection
  else if (acceptLanguage) {
    if (acceptLanguage.includes('ru')) {
      locale = 'ru'
    } else if (acceptLanguage.includes('en')) {
      locale = 'en'
    }
  }

  return locale
}

/**
 * Get the default locale from environment variable
 */
export function getDefaultLocale(): string {
  return process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'en'
}

/**
 * Handles locale detection and redirection for internationalization
 * Can be composed with other middleware functions
 */
export async function handleI18nMiddleware(
  request: NextRequest,
  _userLanguageCode?: string | null
): Promise<NextResponse | null> {
  // The next-intl middleware with localePrefix: 'as-needed' handles this automatically
  // It will:
  // - Show default locale content at root paths (/)
  // - Show non-default locale content at prefixed paths (/ru)
  // - Handle redirects automatically

  // Apply intl middleware for locale-based routing
  return intlMiddleware(request)
}

/**
 * Standalone i18n middleware (for use when no other middleware is needed)
 */
export async function i18nMiddleware(request: NextRequest): Promise<NextResponse> {
  const response = await handleI18nMiddleware(request)
  return response || NextResponse.next()
}
