// Flat ESLint config for ESLint 9
// Minimal ruleset to avoid patch compatibility issues in CI.

import tsParser from "@typescript-eslint/parser";
import jsxA11y from "eslint-plugin-jsx-a11y";

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "dist/**",
      "build/**",
      ".turbo/**",
      "coverage/**",
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
    plugins: {
      "jsx-a11y": jsxA11y,
    },
    rules: {
      // Keep a light rule set for now; customize as needed
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      // Basic a11y checks
      "jsx-a11y/alt-text": "warn",
      "jsx-a11y/anchor-is-valid": "warn",
      "jsx-a11y/label-has-associated-control": [
        "warn",
        {
          controlComponents: ["Input"],
          depth: 3,
        },
      ],
      "jsx-a11y/no-autofocus": "warn",
      "jsx-a11y/click-events-have-key-events": "warn",
      "jsx-a11y/no-static-element-interactions": "warn",
      "jsx-a11y/no-noninteractive-element-interactions": "warn",
      "jsx-a11y/no-noninteractive-element-to-interactive-role": "warn",
      "jsx-a11y/interactive-supports-focus": "warn",
      "jsx-a11y/aria-role": "warn",
      "jsx-a11y/aria-props": "warn",
      "jsx-a11y/role-has-required-aria-props": "warn",
      "jsx-a11y/no-redundant-roles": "warn",
      "jsx-a11y/tabindex-no-positive": "warn",
    },
  },
];
