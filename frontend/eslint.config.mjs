import eslint from '@eslint/js'
import pluginQuery from '@tanstack/eslint-plugin-query'
import nextConfig from 'eslint-config-next'
import eslintPluginPrettierRecommended from 'eslint-plugin-prettier/recommended'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  // Ignore patterns
  {
    ignores: [
      'node_modules/',
      '.next',
      '**/lib',
      'src/providers/yandexMetrica.tsx',
      'public/landing',
      './entrypoint.js',
      'public/landing',
    ],
  },
  // Base ESLint recommended rules
  eslint.configs.recommended,
  // TypeScript ESLint recommended rules
  ...tseslint.configs.recommended,
  // Next.js rules
  nextConfig,
  // TanStack Query rules
  ...pluginQuery.configs['flat/recommended'],
  // Prettier integration (should be last)
  eslintPluginPrettierRecommended,
  // Custom overrides
  {
    files: ['next-env.d.ts'],
    rules: {
      '@typescript-eslint/triple-slash-reference': 'off',
    },
  },
  {
    rules: {
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/refs': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/purity': 'off',
      'react-hooks/preserve-manual-memoization': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
    },
  }
)
