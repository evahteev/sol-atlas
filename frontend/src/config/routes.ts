/**
 * Route access configuration for authentication middleware
 * Defines which routes are public, semi-protected, or fully protected
 */

export interface RouteConfig {
  /** Routes that are completely public - no authentication required */
  public: string[]
  /** Routes that can be viewed without auth but interactions require authentication */
  semiProtected: string[]
  /** Routes that require full authentication to access */
  fullyProtected: string[]
}

export const routeConfig: RouteConfig = {
  // Public routes - accessible to everyone
  public: [
    '/',
    '/about',
    '/content',
    '/content/*',
    '/login',
    '/aifeed',
    '/aifeed/*',
    '/landing/*',
    '/swap',
    '/swap/*',
  ],

  // Semi-protected routes - viewable by all, but interactions require auth
  semiProtected: [
    '/staking',
    '/staking/*',
    '/tokens',
    '/tokens/*',
    '/analytics',
    '/analytics/*',
    '/leaderboards',
    '/leaderboards/*',
    '/launcher',
    '/launcher/*',
  ],

  // Fully protected routes - require authentication to access
  fullyProtected: [
    '/flow',
    '/flow/*',
    '/agents',
    '/agents/*',
    '/tasks',
    '/tasks/*',
    '/admin',
    '/admin/*',
  ],
}

/**
 * Check if a path matches any of the patterns in the array
 * Supports wildcard matching with '*'
 */
export function matchesPattern(path: string, patterns: string[]): boolean {
  return patterns.some((pattern) => {
    if (pattern.endsWith('/*')) {
      const basePath = pattern.slice(0, -2)
      return path === basePath || path.startsWith(`${basePath}/`)
    }
    return path === pattern
  })
}

/**
 * Determine the route type for a given path
 */
export function getRouteType(path: string): 'public' | 'semiProtected' | 'fullyProtected' {
  if (matchesPattern(path, routeConfig.public)) {
    return 'public'
  }

  if (matchesPattern(path, routeConfig.semiProtected)) {
    return 'semiProtected'
  }

  if (matchesPattern(path, routeConfig.fullyProtected)) {
    return 'fullyProtected'
  }

  // Default to fully protected for unknown routes
  return 'fullyProtected'
}
