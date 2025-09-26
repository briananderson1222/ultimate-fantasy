const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

// Find the project and workspace directories
const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// 1. Watch all files within the monorepo
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(monorepoRoot, "node_modules"),
];

// 3. Force Metro to resolve (sub)dependencies only from the `nodeModulesPaths`
config.resolver.disableHierarchicalLookup = true;

// Performance optimizations for mobile bundle
config.transformer = {
  ...config.transformer,
  // Enable Hermes bytecode generation for better performance
  hermesCommand: "hermesc",

  // Optimize asset bundling
  assetRegistryPath: "react-native/Libraries/Image/AssetRegistry",

  // Enable minification for production builds
  minifierConfig: {
    mangle: {
      keep_fnames: true,
    },
    output: {
      ascii_only: true,
      quote_style: 3,
      wrap_iife: true,
    },
    sourceMap: {
      includeSources: false,
    },
    toplevel: false,
    compress: {
      drop_console: process.env.NODE_ENV === "production",
      reduce_funcs: false,
    },
  },
};

// Bundle splitting for better performance
config.serializer = {
  ...config.serializer,

  // Create separate bundles for common modules
  createModuleIdFactory: () => {
    const projectRoot = config.projectRoot;
    return (path) => {
      let name = path.substr(projectRoot.length + 1);

      // Use shorter names for frequently imported modules
      const commonModules = {
        "node_modules/react/index.js": "react",
        "node_modules/react-native/index.js": "react-native",
        "packages/shared-logic/src/index.ts": "shared-logic",
        "packages/ui-components/src/index.ts": "ui-components",
      };

      if (commonModules[name]) {
        return commonModules[name];
      }

      // Hash long paths to reduce bundle size
      if (name.length > 50) {
        const crypto = require("crypto");
        return crypto.createHash("md5").update(name).digest("hex").substr(0, 8);
      }

      return name;
    };
  },

  // Optimize bundle output
  processModuleFilter: (module) => {
    // Filter out unnecessary files from bundle
    const filePath = module.path;

    // Exclude test files and stories
    if (
      filePath.includes("__tests__") ||
      filePath.includes("test.") ||
      filePath.includes(".test.") ||
      filePath.includes(".stories.") ||
      filePath.includes("storybook")
    ) {
      return false;
    }

    // Exclude development-only modules in production
    if (process.env.NODE_ENV === "production") {
      if (
        filePath.includes("reactotron") ||
        filePath.includes("flipper") ||
        filePath.includes("react-devtools")
      ) {
        return false;
      }
    }

    return true;
  },
};

// Cache configuration for faster builds
config.cacheStores = [
  {
    name: "filesystem",
    type: "FileStore",
    root: path.join(projectRoot, ".metro-cache"),
  },
];

// Asset optimization
config.resolver.assetExts = [
  ...config.resolver.assetExts,
  "lottie", // Lottie animations
  "webp", // WebP images for better compression
];

// Platform-specific optimizations
config.resolver.platforms = ["ios", "android", "native", "web"];

// Source map configuration
config.symbolicator = {
  ...config.symbolicator,
  customizeFrame: (frame) => {
    // Simplify stack traces for better debugging
    if (frame.file && frame.file.includes("node_modules")) {
      const match = frame.file.match(/node_modules\/([^\/]+)/);
      if (match) {
        frame.file = `node_modules/${match[1]}`;
      }
    }
    return frame;
  },
};

// 4. Alias specific modules to versions compatible with Expo's runtime.
// Some toolchain packages expect pretty-format@29 (with CJS default export),
// but monorepo hoisting may expose v30 at the root which breaks HMR on web.
try {
  const prettyFormatRoot = require.resolve(
    "@expo/metro-runtime/node_modules/pretty-format/build/index.js",
  );
  // 4a. Ensure any import of `pretty-format` resolves to Expo's bundled v29.
  config.resolver.resolveRequest = (context, moduleName, platform) => {
    if (moduleName === "pretty-format") {
      return {
        type: "sourceFile",
        filePath: prettyFormatRoot,
      };
    }
    // Defer to Metro's default resolver
    return require("metro-resolver").resolve(context, moduleName, platform);
  };
} catch (_) {
  // Fallback: if resolution fails, keep default behavior.
}

module.exports = config;
// Note: Avoid custom transformers unless strictly required.
// By not re-exporting Zustand from shared-logic root, we avoid bundling
// libraries that reference `import.meta.env` on web.
