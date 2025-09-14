# Quickstart: Frontend Shared Logic Extraction

## Overview
This quickstart validates the successful extraction and sharing of frontend logic between NextJS and React Native applications.

## Prerequisites
- Node.js 18+ installed
- Existing NextJS application running
- React Native development environment (for Phase 4)

## Phase 1: API Layer Extraction

### 1.1 Create shared-logic package
```bash
mkdir -p packages/shared-logic/src/api
cd packages/shared-logic
npm init -y
```

### 1.2 Extract first API service
```bash
# Copy existing API call from frontend component to shared package
cp frontend/src/components/[component-with-api].tsx packages/shared-logic/src/api/leagues.ts
```

### 1.3 Test shared API service
```bash
# Run tests to verify API service works
npm test packages/shared-logic/src/api/leagues.test.ts

# Expected: Service exports correctly, types are valid
```

### 1.4 Import in NextJS app
```bash
# Update frontend component to use shared service
# Verify application still works
npm run dev
```

## Phase 2: Business Logic Extraction

### 2.1 Create shared utilities
```bash
mkdir -p packages/shared-logic/src/utils
# Move lib/dashboard.ts to shared package
mv frontend/src/lib/dashboard.ts packages/shared-logic/src/utils/
```

### 2.2 Test shared utilities
```bash
# Run tests to verify utilities work cross-platform
npm test packages/shared-logic/src/utils/dashboard.test.ts

# Expected: Functions export correctly, no platform-specific code
```

### 2.3 Verify NextJS integration
```bash
# Update imports in NextJS app
# Verify dashboard functionality works
npm run build && npm run start
```

## Phase 3: UI Component Extraction

### 3.1 Create ui-components package
```bash
mkdir -p packages/ui-components/src/primitives
cd packages/ui-components
npm init -y
```

### 3.2 Extract first UI component
```bash
# Move Button component to shared package
mv frontend/src/components/ui/button.tsx packages/ui-components/src/primitives/
```

### 3.3 Create platform adapters
```bash
# Create web and mobile versions of styling
touch packages/ui-components/src/adapters/button.web.ts
touch packages/ui-components/src/adapters/button.mobile.ts
```

### 3.4 Test UI component
```bash
# Run component tests
npm test packages/ui-components/src/primitives/button.test.tsx

# Expected: Component renders on web, exports properly
```

### 3.5 Verify NextJS integration
```bash
# Update imports in NextJS app
# Verify buttons still render correctly
npm run dev
```

## Phase 4: Mobile App Setup

### 4.1 Initialize React Native app
```bash
mkdir -p packages/mobile-app
cd packages/mobile-app
npx create-expo-app . --template
```

### 4.2 Install shared packages
```bash
# Add local dependencies
npm install ../shared-logic ../ui-components
```

### 4.3 Test shared imports
```bash
# Create simple test component using shared logic
touch src/components/TestShared.tsx
# Import and use shared API service and UI component
```

### 4.4 Run React Native app
```bash
# Start development server
npm start

# Expected: App loads, shared components render
```

## Validation Tests

### End-to-End Validation
```bash
# Test 1: API calls work on both platforms
npm run test:api

# Test 2: Business logic produces same results
npm run test:logic

# Test 3: UI components render consistently
npm run test:ui

# Test 4: State management syncs properly
npm run test:state
```

### Success Criteria
- [ ] API calls work identically on web and mobile
- [ ] Business logic functions return same results
- [ ] UI components render with platform-appropriate styling
- [ ] Shared state management works across platforms
- [ ] TypeScript types are consistent
- [ ] No code duplication between platforms
- [ ] Existing NextJS functionality unchanged
- [ ] Mobile app successfully consumes all shared packages

### Performance Validation
```bash
# Bundle size analysis
npm run analyze:bundles

# Expected: Shared packages < 50KB each
# Expected: No significant size increase in NextJS app
```

### Troubleshooting

#### Common Issues
1. **Import path errors**: Check tsconfig path mappings
2. **Platform-specific dependencies**: Verify peer dependencies
3. **Styling differences**: Check platform adapter configuration
4. **Build failures**: Verify TypeScript configurations match

#### Quick Fixes
```bash
# Reset to working state
git checkout HEAD~1

# Clear node_modules and reinstall
rm -rf node_modules packages/*/node_modules
npm install

# Verify base functionality
npm run build && npm test
```

## Next Steps
After successful validation:
1. Extract remaining API services (Phase 1 complete)
2. Move all business logic utilities (Phase 2 complete)
3. Extract remaining UI components (Phase 3 complete)
4. Build full mobile app features (Phase 4 complete)
5. Set up continuous integration for shared packages
6. Create migration guides for future developers