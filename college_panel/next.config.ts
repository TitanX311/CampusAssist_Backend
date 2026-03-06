import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://10.111.75.2:8080";

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
