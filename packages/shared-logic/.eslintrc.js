module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'prettier'
  ],
  env: {
    node: true,
    browser: true,
    es2022: true
  },
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  rules: {
    // Fantasy sports specific rules
    'prefer-const': 'error',
    'no-var': 'error',
    'no-console': 'warn',
    'no-debugger': 'error',

    // TypeScript specific
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/prefer-nullish-coalescing': 'error',
    '@typescript-eslint/prefer-optional-chain': 'error',

    // Fantasy sports domain rules
    'no-magic-numbers': ['warn', {
      ignore: [0, 1, -1, 100],
      ignoreArrayIndexes: true,
      enforceConst: true
    }],

    // Naming conventions for fantasy sports
    'camelcase': ['error', {
      properties: 'never',
      ignoreDestructuring: false,
      allow: [
        '^player_id$',
        '^league_id$',
        '^team_id$',
        '^fantasy_points$',
        '^projection_.*',
        '^stats_.*'
      ]
    }]
  },
  overrides: [
    {
      files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts'],
      env: {
        jest: true
      },
      rules: {
        'no-magic-numbers': 'off',
        '@typescript-eslint/no-explicit-any': 'off'
      }
    }
  ]
};