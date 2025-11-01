import { createNavigation } from 'next-intl/navigation'
import { defineRouting } from 'next-intl/routing'

// Get default locale from environment variable, fallback to 'en'
const DEFAULT_LOCALE = process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'en'

export const routing = defineRouting({
  // A list of all locales that are supported
  locales: ['en', 'ru'],

  // Used when no locale matches - controlled by env var
  defaultLocale: DEFAULT_LOCALE as 'en' | 'ru',

  // Hide default locale in URL
  localePrefix: 'as-needed',

  // The `pathnames` object holds pairs of internal and
  // external paths. The external paths are shown in the URL.
  pathnames: {
    // If all locales use the same pathname, a single
    // external path can be provided.
    '/': '/',
    '/aifeed': '/aifeed',
    '/tasks': '/tasks',
    '/agents': '/agents',
    '/staking': '/staking',
    '/tokens': '/tokens',
    '/profile': '/profile',
    '/login': '/login',

    // Dynamic routes work too
    '/flow/[key]': '/flow/[key]',
    '/tokens/[address]': '/tokens/[address]',
    '/quests/[id]': '/quests/[id]',
  },
})

// Lightweight wrappers around Next.js' navigation APIs
// that will consider the routing configuration
export const { Link, redirect, usePathname, useRouter } = createNavigation(routing)
