import type { NextConfig } from 'next'

import CopyPlugin from 'copy-webpack-plugin'
import CssLayeringPlugin from 'css-layering-webpack-plugin'
import fs from 'fs'
import createNextIntlPlugin from 'next-intl/plugin'
import path from 'path'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

const nextConfig: NextConfig = {
  images: {
    formats: ['image/webp'],
    minimumCacheTTL: 2592000,
    remotePatterns: [
      { protocol: 'https', hostname: 'pbs.twimg.com' },
      { protocol: 'https', hostname: 'img.burning.meme' },
      { protocol: 'https', hostname: '*.gurunetwork.ai' },
      { protocol: 'https', hostname: '*.dexguru.biz' },
      { protocol: 'https', hostname: '*.dex.guru' },
      { protocol: 'https', hostname: '*.amazonaws.com' },
      { protocol: 'https', hostname: 'ipfs.io', pathname: '/ipfs/*' },
    ],
  },
}

const fullNextConfig: NextConfig = {
  webpack(config) {
    // Grab the existing rule that handles SVG imports
    // @ts-expect-error webpack config ts
    const fileLoaderRule = config.module.rules.find((rule) => rule.test?.test?.('.svg'))

    config.module.rules.push(
      // Reapply the existing rule, but only for .file.svg imports for using as src
      {
        ...fileLoaderRule,
        test: /\.file\.svg$/i,
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        exclude: /\.file\.svg$/i, // exclude if *.file.svg
        use: ['@svgr/webpack'],
      }
    )

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i

    config.plugins.push(
      new CssLayeringPlugin({
        layers: [
          { name: 'reset' },
          { name: 'default' },
          { path: '**/src/components/atoms/**/*.module.scss', name: 'atoms' },
          { path: '**/src/components/ui/**/*.module.scss', name: 'components' },
          { name: 'variants' },
          { path: '**/src/components/composed/**/*.module.scss', name: 'composed' },
          { path: '**/src/components/page/**/*.module.scss', name: 'composed' },
          { path: '**/src/components/feature/**/*.module.scss', name: 'features' },
          { path: '**/src/app/**/layout.module.scss', name: 'layouts' },
          { path: '**/src/app/**/page.module.scss', name: 'pages' },
          { name: 'utility' },
          { name: 'override' },
        ],
      })
    )

    const theme = process.env.APP_SKIN_NAME || process.env.NEXT_PUBLIC_CI_PROJECT_NAME || 'dexguru'

    if (process.env.NODE_ENV === 'development') {
      const devSource = path.resolve(__dirname, `skins/${theme}`)
      const devTarget = path.resolve(__dirname, `skins/theme`)

      console.log(`🛠  [DEV] Copying theme '${theme}' to 'theme' directory...`)

      if (fs.existsSync(devTarget)) {
        fs.rmSync(devTarget, { recursive: true, force: true })
      }
      fs.mkdirSync(devTarget, { recursive: true })

      fs.readdirSync(devSource).forEach((file) => {
        const srcPath = path.join(devSource, file)
        const destPath = path.join(devTarget, file)
        fs.cpSync(srcPath, destPath, { recursive: true })
      })
    }

    config.plugins.push(
      new CopyPlugin({
        patterns: [
          {
            from: path.resolve(__dirname, `skins/theme/public`),
            to: path.resolve(__dirname, `public`),
          },
        ],
      })
    )

    config.externals.push('pino-pretty', 'lokijs', 'encoding')

    return config
  },
  generateBuildId: () => `${process.env.NEXT_PUBLIC_GIT_COMMIT}`,

  ...nextConfig,
}

export default withNextIntl(fullNextConfig)
