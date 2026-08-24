/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // API routing in production is handled entirely by vercel.json rewrites
  // (/api/* → api/index.py). Do NOT add Next.js rewrites for /api here —
  // they conflict with vercel.json and send requests to a dead URL.
};

export default nextConfig;
