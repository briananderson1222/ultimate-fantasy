# Visual Regression Testing

## Overview

Visual regression tests use Playwright to capture screenshots of key pages and compare them against baseline images to detect unintended visual changes.

## Setup

Visual tests are configured to run only on Chromium for consistency:

```typescript
// playwright.config.ts
{
  name: 'visual-chromium',
  testMatch: '**/visual.spec.ts',
  use: {
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 720 }
  }
}
```

## Running Tests

```bash
# Run visual tests
npm run test:visual

# Update baseline screenshots
npm run test:visual:update

# Run with UI (for debugging)
npx playwright test --project=visual-chromium --ui
```

## Test Coverage

Visual tests cover key themed pages in both light and dark modes:

- **Homepage** (`/`) - Hero section and navigation
- **Dashboard** (`/dashboard`) - Widget layout and theming
- **Create League** (`/leagues/create`) - Form styling
- **Leagues List** (`/leagues`) - List and empty states
- **Theme Settings** (`/settings/theme`) - Theme controls
- **Players Page** (`/players`) - Data tables and filters

## Generating Baselines

1. Start the backend and frontend services:

   ```bash
   # Terminal 1: Backend
   cd backend/src && uv run uvicorn main:app --host 127.0.0.1 --port 8000

   # Terminal 2: Frontend
   cd frontend && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
   ```

2. Generate baselines:

   ```bash
   # Using the helper script
   ./scripts/generate-visual-baselines.sh

   # Or manually
   cd frontend && npm run test:visual:update
   ```

## CI Integration

Visual tests run automatically in CI on every push and pull request:

- **Job**: `frontend-visual`
- **Browser**: Chromium only (for consistency)
- **Viewport**: 1280x720
- **Threshold**: 0.2 (20% pixel difference tolerance)

## Best Practices

### When to Update Baselines

- After intentional design changes
- When adding new themed components
- After updating CSS tokens or theme variables

### Avoiding Flaky Tests

- Tests wait for `networkidle` state
- Consistent viewport size (1280x720)
- Theme switching with wait time for CSS application
- Dev token set for authenticated pages

### Debugging Failures

1. Run tests locally with `--ui` flag
2. Check the diff images in `test-results/`
3. Verify changes are intentional
4. Update baselines if needed

## File Structure

```
frontend/
├── tests/e2e/
│   ├── visual.spec.ts                    # Visual test definitions
│   └── visual.spec.ts-snapshots/         # Baseline screenshots
│       ├── homepage-light-visual-chromium-linux.png
│       ├── homepage-dark-visual-chromium-linux.png
│       └── ...
├── playwright.config.ts                  # Playwright configuration
└── docs/visual-testing.md               # This documentation
```

## Troubleshooting

### Common Issues

**Screenshots don't match on different OS**

- Baselines are OS-specific (linux, darwin, win32)
- Generate baselines on the same OS as CI (Ubuntu)

**Tests are flaky**

- Increase wait times for dynamic content
- Check for animations that might affect screenshots
- Ensure consistent data state

**Large diff files**

- Consider if changes are intentional
- Check for font rendering differences
- Verify theme tokens are applied correctly

### Updating Configuration

To add new pages to visual testing:

1. Add test cases to `visual.spec.ts`
2. Generate new baselines
3. Commit both test code and baseline images

To change viewport or threshold:

1. Update `playwright.config.ts`
2. Regenerate all baselines
3. Update documentation
