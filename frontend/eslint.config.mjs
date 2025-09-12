// Flat ESLint config for ESLint 9
// Minimal ruleset to avoid patch compatibility issues in CI.

import tsParser from '@typescript-eslint/parser';

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'dist/**',
      'build/**',
      '.turbo/**',
      'coverage/**',
    ],
  },
  {
    files: ["**/*.{js,jsx,ts,tsx}", "**/*.cjs", "**/*.mjs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        project: false,
      },
    },
    rules: {
      // Keep a light rule set for now; customize as needed
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
];
