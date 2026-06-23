/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Static export for Vercel/Netlify
  distDir: 'dist',   // Output directory
  images: {
    unoptimized: true,  // Required for static export
  },
  // API rewrites to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
