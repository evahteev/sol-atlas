/**
 * Feature Flag System
 *
 * Environment variable-based feature flags for progressive feature rollout.
 * Provides type-safe flags with client and server-side support.
 *
 * Architecture:
 * - Environment variable-based for simplicity
 * - Client-side accessible (NEXT_PUBLIC_ prefix)
 * - Type-safe with TypeScript enums
 * - Cacheable for performance
 */

export enum FeatureFlag {
  BOT_API_CHAT = 'BOT_API_CHAT',
  // Future flags can be added here
}

type FeatureFlagConfig = {
  key: string
  defaultValue: boolean
  description: string
}

const FEATURE_FLAGS: Record<FeatureFlag, FeatureFlagConfig> = {
  [FeatureFlag.BOT_API_CHAT]: {
    key: 'NEXT_PUBLIC_FEATURE_BOT_API_CHAT',
    defaultValue: true,
    description: 'Enable bot API integration for AIChat (SSE-based)',
  },
}

/**
 * Check if a feature flag is enabled (server-side)
 *
 * Order of precedence:
 * 1. Environment variable
 * 2. Default value from config
 *
 * @param flag - Feature flag to check
 * @returns boolean indicating if flag is enabled
 */
export function isFeatureEnabled(flag: FeatureFlag): boolean {
  const config = FEATURE_FLAGS[flag]
  const envValue = process.env[config.key]

  if (envValue !== undefined) {
    return envValue === 'true' || envValue === '1'
  }

  return config.defaultValue
}

/**
 * Client-side hook for feature flags
 *
 * Uses environment variables injected by Next.js at build time
 */
export function useFeatureFlag(flag: FeatureFlag): boolean {
  const config = FEATURE_FLAGS[flag]

  // Server-side rendering
  if (typeof window === 'undefined') {
    return isFeatureEnabled(flag)
  }

  // Client-side - use process.env which is replaced at build time
  const envValue = process.env[config.key]

  if (envValue !== undefined) {
    return envValue === 'true' || envValue === '1'
  }

  return config.defaultValue
}

/**
 * Get all feature flags (admin/debug use)
 */
export function getAllFeatureFlags(): Record<FeatureFlag, boolean> {
  return Object.keys(FEATURE_FLAGS).reduce(
    (acc, key) => {
      acc[key as FeatureFlag] = isFeatureEnabled(key as FeatureFlag)
      return acc
    },
    {} as Record<FeatureFlag, boolean>
  )
}
