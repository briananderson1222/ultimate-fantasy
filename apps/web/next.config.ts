import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  outputFileTracingRoot: path.join(__dirname, ".."),
  transpilePackages: [
    "@ultimate-fantasy/api-client",
    "@ultimate-fantasy/shared-logic",
    "@ultimate-fantasy/ui-components"
  ],

  // Performance optimizations
  experimental: {
    optimizePackageImports: ['@ultimate-fantasy/ui-components', 'lucide-react'],
    webVitalsAttribution: ['CLS', 'LCP', 'FCP', 'FID', 'TTFB'],
    optimisticClientCache: true,
    serverComponentsExternalPackages: ['sharp'],
  },

  // Code splitting and bundle optimization
  webpack: (config, { dev, isServer }) => {
    config.externals = config.externals || {};
    config.externals["react-native"] = "react-native";

    if (!dev && !isServer) {
      // Split vendor chunks for better caching
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks?.cacheGroups,
          default: false,
          vendors: false,
          // Framework chunk (React, Next.js)
          framework: {
            chunks: 'all',
            name: 'framework',
            test: /(?<!node_modules.*)[\\/]node_modules[\\/](react|react-dom|scheduler|prop-types|use-subscription)[\\/]/,
            priority: 40,
            enforce: true,
          },
          // UI components chunk
          ui: {
            chunks: 'all',
            name: 'ui-components',
            test: /(?<!node_modules.*)[\\/]node_modules[\\/](@ultimate-fantasy\/ui-components|lucide-react|@radix-ui)[\\/]/,
            priority: 30,
            enforce: true,
          },
          // Shared logic chunk
          shared: {
            chunks: 'all',
            name: 'shared-logic',
            test: /(?<!node_modules.*)[\\/]node_modules[\\/](@ultimate-fantasy\/shared-logic|@ultimate-fantasy\/api-client)[\\/]/,
            priority: 25,
            enforce: true,
          },
          // Common vendor libraries
          commons: {
            chunks: 'all',
            name: 'commons',
            test: /(?<!node_modules.*)[\\/]node_modules[\\/]/,
            priority: 20,
            minChunks: 2,
            reuseExistingChunk: true,
          },
        },
      };

      // Optimize for production
      config.optimization.minimize = true;
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;

      // Tree shaking optimization
      config.module.rules.push({
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['next/babel'],
            plugins: [
              ['import', { libraryName: 'lodash', libraryDirectory: '', camel2DashComponentName: false }, 'lodash'],
              ['import', { libraryName: 'date-fns', libraryDirectory: '', camel2DashComponentName: false }, 'date-fns'],
            ],
          },
        },
      });
    }

    // Add bundle analyzer in development
    if (dev && process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'server',
          analyzerPort: 8888,
          openAnalyzer: true,
        })
      );
    }

    return config;
  },

  // Compression and caching
  compress: true,
  generateEtags: true,

  // Image optimization
  images: {
    domains: ['localhost', 'ui-avatars.com'],
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },

  // Headers for performance
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=300, s-maxage=600' },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400' },
        ],
      },
    ];
  },

  // Rewrites for API optimization
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
