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
  webpack: (config) => {
    config.externals = config.externals || {};
    config.externals["react-native"] = "react-native";
    return config;
  },
};

export default nextConfig;
