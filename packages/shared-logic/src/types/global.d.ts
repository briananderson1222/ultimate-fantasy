// Global type declarations for cross-platform compatibility

declare global {
  // React Native global variables
  var __DEV__: boolean | undefined;

  // Expo global
  interface Global {
    expo?: any;
  }

  // Node.js global
  var global: Global;
}

export {};