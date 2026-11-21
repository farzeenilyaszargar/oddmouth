import type { NextConfig } from 'next';

const localReview = process.env.NODE_ENV === 'development';
const config: NextConfig = {
  ...(localReview ? {
    async rewrites() {
      return [{ source: '/training-files/:path*', destination: 'http://127.0.0.1:3001/:path*' }];
    },
  } : { output: 'export' }),
  trailingSlash: true,
  devIndicators: false,
  turbopack: { root: process.cwd() },
};

export default config;
