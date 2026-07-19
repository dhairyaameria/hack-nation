import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Dev HMR when opening the app via 127.0.0.1 instead of localhost
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
