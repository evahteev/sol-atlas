import { getLocale, getTranslations } from 'next-intl/server'

import { getDefaultLocale } from '@/i18n/middleware'

type LocaleMetadataProps = {
  title?: string
  description?: string
  path?: string
}

/**
 * Generates SEO-friendly metadata for internationalized pages
 * Handles canonical URLs, hreflang tags, and Open Graph localization
 */
export async function LocaleMetadata({ title, description, path = '/' }: LocaleMetadataProps = {}) {
  const locale = await getLocale()
  const defaultLocale = getDefaultLocale()
  const t = await getTranslations('Metadata')

  // Build base URL - you'll need to set this env var
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://yoursite.com'

  // Canonical URL logic:
  // - Default locale: canonical points to root path
  // - Non-default locale: canonical points to prefixed path
  const canonicalUrl =
    locale === defaultLocale ? `${baseUrl}${path}` : `${baseUrl}/${locale}${path}`

  // Alternate URLs for hreflang
  const alternateUrls = {
    en: locale === 'en' || defaultLocale === 'en' ? `${baseUrl}${path}` : `${baseUrl}/en${path}`,
    ru: locale === 'ru' || defaultLocale === 'ru' ? `${baseUrl}${path}` : `${baseUrl}/ru${path}`,
    'x-default':
      defaultLocale === 'en' ? `${baseUrl}${path}` : `${baseUrl}/${defaultLocale}${path}`,
  }

  return {
    title: title || t('defaultTitle'),
    description: description || t('defaultDescription'),
    canonical: canonicalUrl,
    languageAlternates: alternateUrls,
    openGraph: {
      title: title || t('defaultTitle'),
      description: description || t('defaultDescription'),
      url: canonicalUrl,
      locale: locale,
      alternateLocale: locale === 'en' ? 'ru' : 'en',
    },
    other: {
      // Prevent duplicate content issues
      robots: 'index,follow',
    },
  }
}

/**
 * Component to render hreflang and canonical tags in page head
 */
export function LocaleLinks({
  canonicalUrl,
  alternateUrls,
}: {
  canonicalUrl: string
  alternateUrls: Record<string, string>
}) {
  return (
    <>
      <link rel="canonical" href={canonicalUrl} />
      {Object.entries(alternateUrls).map(([hreflang, href]) => (
        <link key={hreflang} rel="alternate" hrefLang={hreflang} href={href} />
      ))}
    </>
  )
}
