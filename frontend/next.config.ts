import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "assets.nhle.com",
        pathname: "/logos/nhl/svg/**",
      },
    ],
  },
};

export default nextConfig;
