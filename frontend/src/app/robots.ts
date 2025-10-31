import type { MetadataRoute } from 'next'

export const dynamic = 'force-dynamic'

const BASE_URL = process.env.APPLICATION_URL

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: '/admin/',
    },
    sitemap: `${BASE_URL}/sitemap.xml`,
  }
}
