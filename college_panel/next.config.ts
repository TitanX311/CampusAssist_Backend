import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://172.21.11.121:8080";

const nextConfig: NextConfig = {
  reactCompiler: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
