import type { NextConfig } from "next";

const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  // El navegador llama a /api/... y Next.js lo reenvía al backend (evita CORS).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
