const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

// Find the project and workspace directories
const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

// 1. Watch all files within the monorepo
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

// 3. Force Metro to resolve (sub)dependencies only from the `nodeModulesPaths`
config.resolver.disableHierarchicalLookup = true;

// 4. Alias specific modules to versions compatible with Expo's runtime.
// Some toolchain packages expect pretty-format@29 (with CJS default export),
// but monorepo hoisting may expose v30 at the root which breaks HMR on web.
try {
  const prettyFormatRoot = require.resolve(
    '@expo/metro-runtime/node_modules/pretty-format/build/index.js'
  );
  // 4a. Ensure any import of `pretty-format` resolves to Expo's bundled v29.
  config.resolver.resolveRequest = (context, moduleName, platform) => {
    if (moduleName === 'pretty-format') {
      return {
        type: 'sourceFile',
        filePath: prettyFormatRoot,
      };
    }
    // Defer to Metro's default resolver
    return require('metro-resolver').resolve(context, moduleName, platform);
  };
} catch (_) {
  // Fallback: if resolution fails, keep default behavior.
}

module.exports = config;
// Note: Avoid custom transformers unless strictly required.
// By not re-exporting Zustand from shared-logic root, we avoid bundling
// libraries that reference `import.meta.env` on web.
