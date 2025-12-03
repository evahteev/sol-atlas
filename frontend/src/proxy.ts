import { NextRequest, NextResponse } from 'next/server'

import { getRouteType } from '@/config/routes'
import { SESSION_COOKIE_NAME } from '@/config/settings'
import { decrypt } from '@/lib/session'

import { handleI18nMiddleware } from './i18n/middleware'

export default async function proxy(request: NextRequest) {
  const { pathname, search, origin } = request.nextUrl

  // Skip middleware for API routes, static files, and auth routes

  // Redirect root to landing page
  if (pathname === '/') {
    return NextResponse.rewrite(new URL('/landing/index.html', request.url))
  }

  // Handle /landing without trailing slash
  if (pathname === '/landing') {
    return NextResponse.rewrite(new URL('/landing/index.html', request.url))
  }

  // Handle /docs without trailing slash (MkDocs documentation)
  if (pathname === '/docs') {
    return NextResponse.rewrite(new URL('/docs/index.html', request.url))
  }

  // Handle docs pages without .html extension
  if (pathname.startsWith('/docs/') && !pathname.includes('.')) {
    // If path ends with /, serve index.html from that directory
    if (pathname.endsWith('/')) {
      return NextResponse.rewrite(new URL(`${pathname}index.html`, request.url))
    }
    // For all other docs paths, append .html (MkDocs pages)
    return NextResponse.rewrite(new URL(`${pathname}.html`, request.url))
  }

  // Handle landing pages without .html extension
  if (pathname.startsWith('/landing/') && !pathname.includes('.')) {
    // If path ends with /, serve index.html from that directory
    if (pathname.endsWith('/')) {
      return NextResponse.rewrite(new URL(`${pathname}index.html`, request.url))
    }
    // For other landing pages, append .html
    return NextResponse.rewrite(new URL(`${pathname}.html`, request.url))
  }

  // Skip middleware for API routes, static files, landing pages, and auth routes
  if (
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    pathname.includes('.') ||
    pathname === '/login' ||
    pathname.startsWith('/auth/') ||
    pathname.startsWith('/landing/')
  ) {
    return NextResponse.next()
  }

  // Get session from cookie
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME)?.value
  const session = sessionCookie ? await decrypt(sessionCookie) : null

  // Handle i18n with user's language preference from session
  const i18nResponse = await handleI18nMiddleware(request)

  // If i18n middleware returns a response (redirect), use it
  if (i18nResponse) {
    return i18nResponse
  }
  // Determine route type based on configuration
  const routeType = getRouteType(pathname)

  // Handle route access based on authentication status and route type
  if (!session?.userId) {
    // Public routes: Allow access without authentication
    if (routeType === 'public') {
      return NextResponse.next()
    }

    // Semi-protected routes: Allow viewing but interactions will require auth
    if (routeType === 'semiProtected') {
      return NextResponse.next()
    }

    // Fully protected routes: Redirect to login with callback URL
    if (routeType === 'fullyProtected') {
      const callbackUrl = `${pathname}${search}`
      const loginUrl = new URL('/login', origin)
      loginUrl.searchParams.set('callbackUrl', callbackUrl)

      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
