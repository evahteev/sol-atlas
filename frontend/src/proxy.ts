import { NextRequest, NextResponse } from 'next/server'

import { auth } from './auth'
import { getRouteType } from './config/routes'
import { handleI18nMiddleware } from './i18n/middleware'

export default async function proxy(request: NextRequest) {
  // Get session to access user's language preference
  const session = await auth()

  const { pathname, search, origin } = request.nextUrl

  // Redirect root to landing page
  if (pathname === '/') {
    return NextResponse.rewrite(new URL('/landing/index.html', request.url))
  }

  // Handle landing pages without .html extension
  if (pathname.startsWith('/landing/') && !pathname.includes('.')) {
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

  // Handle i18n with user's language preference from session
  const i18nResponse = await handleI18nMiddleware(request, session?.user?.language_code)

  // If i18n middleware returns a response (redirect), use it
  if (i18nResponse) {
    return i18nResponse
  }
  // Determine route type based on configuration
  const routeType = getRouteType(pathname)

  // Handle route access based on authentication status and route type
  if (!session?.user) {
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

  // Run auth middleware
  const authResponse = await (
    auth as unknown as (request: NextRequest) => Promise<NextResponse | undefined>
  )(request)

  // Return auth response or continue
  return authResponse || NextResponse.next()
}

export const config = {
  // Matcher ignoring `/_next/` and `/api/`
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
}
