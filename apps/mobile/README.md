# Ultimate Fantasy Mobile App

React Native mobile application built with Expo for the Ultimate Fantasy Sports Platform.

## Features

- Cross-platform compatibility (iOS and Android)
- Shared UI components with web application
- React Navigation for screen management
- React Query for data fetching
- Integration with shared business logic

## Getting Started

### Prerequisites

- Node.js 20+
- Expo CLI
- iOS Simulator (for iOS development)
- Android Studio/Emulator (for Android development)

### Installation

From the root directory:

```bash
npm install
```

### Running the App

```bash
# Start the development server
npm run dev:mobile

# Or from the mobile directory
cd apps/mobile
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on web
npm run web
```

### Project Structure

```
apps/mobile/
├── src/
│   └── screens/          # Screen components
│       ├── HomeScreen.tsx
│       ├── DashboardScreen.tsx
│       └── LeaguesScreen.tsx
├── App.tsx              # Root component
├── metro.config.js      # Metro bundler configuration
└── package.json
```

### Shared Dependencies

This mobile app uses shared packages from the monorepo:

- `@ultimate-fantasy/shared-logic` - Business logic and utilities
- `@ultimate-fantasy/api-client` - API service layer
- `@ultimate-fantasy/ui-components` - Cross-platform UI components

### Development

The mobile app is designed to work seamlessly with the shared codebase. Components automatically adapt to the mobile platform using the platform adapter system.

Key features:
- Platform-aware storage (AsyncStorage for mobile, localStorage for web)
- Cross-platform UI components that work on both web and mobile
- Shared dashboard utilities and state management
- Consistent API client across platforms

### Building for Production

```bash
# Build for development
npm run build

# For production builds, use EAS Build (Expo Application Services)
eas build --platform all
```