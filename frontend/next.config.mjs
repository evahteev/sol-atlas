/** @type {import('next').NextConfig} */

const nextConfig = {
  experimental: { instrumentationHook: true, esmExternals: 'loose' },
  images: {
    formats: ['image/webp'],
    minimumCacheTTL: 2592000,
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
      },
      { protocol: 'https', hostname: 'img.burning.meme', pathname: '/images/*' },
      { protocol: 'https', hostname: '*.amazonaws.com' },
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
  generateBuildId: async () => {
    // Use a fixed ID for non-Git builds, or create a unique one
    return 'build-' + Date.now().toString();
  },

  ...nextConfig,
}

export default fullNextConfig
