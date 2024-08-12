/** @type {import('next').NextConfig} */
import nextBuildId from 'next-build-id'

const {
  CAMUNDA_URL,
  BOT_URL,
  SYS_KEY,
  AUTH_SECRET,
  DEPLOY_ENVIRONMENT,
} = process.env

export const sourcePrefixes = {
  camundaRestApi: '/api/engine',
  telegramBotApi: '/bot',
}

const nextConfig = {
  reactStrictMode: false,
  experimental: { instrumentationHook: true, esmExternals: 'loose' },
  images: {
    formats: ['image/webp'],
    minimumCacheTTL: 3600,

    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.dex.guru',
      },
      { protocol: 'https', hostname: '*.amazonaws.com' },
      { protocol: 'https', hostname: 'ipfs.io', pathname: '/ipfs/*' },
    ],
  },
}

const fullNextConfig = {
  webpack(config, { webpack, buildId }) {
    // Grab the existing rule that handles SVG imports
    const fileLoaderRule = config.module.rules.find((rule) => rule.test?.test?.('.svg'))

    config.module.rules.push(
      // Reapply the existing rule, but only for svg imports ending in ?url
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // *.svg?url
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        resourceQuery: { not: [...fileLoaderRule.resourceQuery.not, /url/] }, // exclude if *.svg?url
        use: ['@svgr/webpack'],
      }
    )

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i

    config.plugins.push(
      new webpack.DefinePlugin({
        'process.env.GIT_COMMIT': JSON.stringify(buildId),
      })
    )

    config.externals.push('pino-pretty', 'lokijs', 'encoding')
    return config
  },
  rewrites: async () => {
    return [
      {
        source: `${sourcePrefixes.camundaRestApi}/:path*`,
        destination: `${CAMUNDA_URL}/:path*`,
      },
      // {
      //   source: `${sourcePrefixes.telegramBotApi}/:path*`,
      //   destination: `${BOT_URL}/:path*`,
      // },
    ]
  },
  env: {
    CAMUNDA_URL,
    BOT_URL,
    SYS_KEY,
    AUTH_SECRET,
    DEPLOY_ENVIRONMENT,
  },
  generateBuildId: () => nextBuildId.sync().slice(0, 7),

  ...nextConfig,
}

export default fullNextConfig
