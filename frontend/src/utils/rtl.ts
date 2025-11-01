/**
 * RTL (Right-to-Left) utility functions for internationalization
 */

/**
 * List of RTL locale codes
 * Note: Currently the app only supports en/ru, but this prepares for future RTL languages
 * like Arabic (ar), Hebrew (he), Persian (fa), etc.
 */
const RTL_LOCALES = ['ar', 'he', 'fa', 'ur', 'ps', 'sd']

/**
 * Determines if a locale uses right-to-left text direction
 * @param locale - The locale code (e.g., 'en', 'ru', 'ar')
 * @returns true if the locale is RTL, false for LTR
 */
export function isRTLLocale(locale: string): boolean {
  return RTL_LOCALES.includes(locale.toLowerCase())
}

/**
 * Gets the text direction for a given locale
 * @param locale - The locale code
 * @returns 'rtl' for RTL locales, 'ltr' for LTR locales
 */
export function getTextDirection(locale: string): 'ltr' | 'rtl' {
  return isRTLLocale(locale) ? 'rtl' : 'ltr'
}

/**
 * Gets CSS class names for RTL-aware styling
 * @param locale - The locale code
 * @returns Object with direction-specific class names
 */
export function getDirectionClasses(locale: string) {
  const isRTL = isRTLLocale(locale)
  return {
    direction: getTextDirection(locale),
    isRTL,
    isLTR: !isRTL,
    className: isRTL ? 'rtl' : 'ltr',
  }
}

/**
 * RTL-aware flex direction utility
 * Converts logical flex directions to physical ones based on locale
 */
export function getFlexDirection(
  logicalDirection: 'start' | 'end',
  locale: string
): 'left' | 'right' {
  const isRTL = isRTLLocale(locale)

  if (logicalDirection === 'start') {
    return isRTL ? 'right' : 'left'
  } else {
    return isRTL ? 'left' : 'right'
  }
}

/**
 * RTL-aware margin/padding utilities
 * Converts logical spacing to physical spacing based on locale
 */
export function getLogicalSpacing(locale: string) {
  const isRTL = isRTLLocale(locale)

  return {
    marginStart: isRTL ? 'marginRight' : 'marginLeft',
    marginEnd: isRTL ? 'marginLeft' : 'marginRight',
    paddingStart: isRTL ? 'paddingRight' : 'paddingLeft',
    paddingEnd: isRTL ? 'paddingLeft' : 'paddingRight',
    start: isRTL ? 'right' : 'left',
    end: isRTL ? 'left' : 'right',
  }
}
