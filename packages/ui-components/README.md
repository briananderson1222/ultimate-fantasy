# @ultimate-fantasy/ui-components

Cross-platform UI component library for the Ultimate Fantasy platform. Provides a consistent design system that works seamlessly between NextJS web applications and React Native mobile apps.

## Features

- 🎨 **Design System** - Consistent visual language across platforms
- 📱 **Cross-Platform** - Works on web (React) and mobile (React Native)
- 🔧 **Platform Adapters** - Automatic styling adaptation
- 🎯 **TypeScript** - Full type safety and IntelliSense
- 📚 **Storybook** - Interactive component documentation
- ♿ **Accessibility** - WCAG compliant components
- 🎭 **Theming** - Dark/light mode support
- 🔄 **Animation** - Smooth transitions and micro-interactions

## Installation

```bash
npm install @ultimate-fantasy/ui-components
```

## Quick Start

### Web (NextJS/React)

```typescript
import { Button, Card, Input } from '@ultimate-fantasy/ui-components';

function MyComponent() {
  return (
    <Card>
      <Input placeholder="Enter your name" />
      <Button variant="primary" onPress={() => console.log('Clicked!')}>
        Submit
      </Button>
    </Card>
  );
}
```

### Mobile (React Native)

```typescript
import { Button, Card, Input } from '@ultimate-fantasy/ui-components';
import { View } from 'react-native';

function MyScreen() {
  return (
    <View>
      <Card>
        <Input placeholder="Enter your name" />
        <Button variant="primary" onPress={() => console.log('Pressed!')}>
          Submit
        </Button>
      </Card>
    </View>
  );
}
```

## Components

### Primitives

#### Button

Versatile button component with multiple variants and states.

```typescript
import { Button } from '@ultimate-fantasy/ui-components';

<Button variant="primary" size="lg" onPress={handlePress}>
  Primary Button
</Button>

<Button variant="secondary" disabled>
  Disabled Button
</Button>

<Button variant="outline" loading>
  Loading Button
</Button>
```

**Props:**
- `variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'`
- `size?: 'sm' | 'md' | 'lg'`
- `disabled?: boolean`
- `loading?: boolean`
- `onPress?: () => void`

#### Card

Container component for grouping related content.

```typescript
import { Card } from '@ultimate-fantasy/ui-components';

<Card variant="elevated" padding="lg">
  <Card.Header>
    <Card.Title>League Settings</Card.Title>
    <Card.Description>Configure your league preferences</Card.Description>
  </Card.Header>

  <Card.Content>
    <p>Card content goes here...</p>
  </Card.Content>

  <Card.Footer>
    <Button variant="primary">Save Changes</Button>
  </Card.Footer>
</Card>
```

**Props:**
- `variant?: 'flat' | 'elevated' | 'outlined'`
- `padding?: 'none' | 'sm' | 'md' | 'lg'`
- `interactive?: boolean`

#### Input

Text input component with validation and multiple types.

```typescript
import { Input } from '@ultimate-fantasy/ui-components';

<Input
  type="text"
  placeholder="Enter league name"
  value={value}
  onChangeText={setValue}
  error={error}
  required
/>

<Input
  type="email"
  label="Email Address"
  placeholder="you@example.com"
  leftIcon="mail"
/>

<Input
  type="password"
  label="Password"
  rightIcon="eye"
  secureTextEntry
/>
```

**Props:**
- `type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'`
- `label?: string`
- `placeholder?: string`
- `value?: string`
- `onChangeText?: (text: string) => void`
- `error?: string`
- `required?: boolean`
- `disabled?: boolean`
- `leftIcon?: string`
- `rightIcon?: string`

#### Modal

Dialog component for overlays and modals.

```typescript
import { Modal } from '@ultimate-fantasy/ui-components';

<Modal isOpen={isOpen} onClose={onClose} size="md">
  <Modal.Header>
    <Modal.Title>Confirm Action</Modal.Title>
  </Modal.Header>

  <Modal.Content>
    <p>Are you sure you want to delete this league?</p>
  </Modal.Content>

  <Modal.Footer>
    <Button variant="ghost" onPress={onClose}>
      Cancel
    </Button>
    <Button variant="danger" onPress={onConfirm}>
      Delete
    </Button>
  </Modal.Footer>
</Modal>
```

**Props:**
- `isOpen: boolean`
- `onClose: () => void`
- `size?: 'sm' | 'md' | 'lg' | 'xl'`
- `closeOnOverlayClick?: boolean`
- `showCloseButton?: boolean`

### Design Tokens

#### Colors

```typescript
import { colors } from '@ultimate-fantasy/ui-components';

const theme = {
  primary: colors.blue[600],
  secondary: colors.gray[500],
  success: colors.green[500],
  warning: colors.yellow[500],
  danger: colors.red[500],
};
```

#### Typography

```typescript
import { typography } from '@ultimate-fantasy/ui-components';

const textStyles = {
  heading1: typography.headings.h1,
  heading2: typography.headings.h2,
  body: typography.body.md,
  caption: typography.body.sm,
};
```

#### Spacing

```typescript
import { spacing } from '@ultimate-fantasy/ui-components';

const layout = {
  padding: spacing.md,
  margin: spacing.lg,
  gap: spacing.sm,
};
```

### Platform Adapters

The library automatically adapts to the target platform:

#### Web Implementation
```typescript
// Automatically uses CSS-in-JS or Tailwind classes
const buttonStyles = {
  backgroundColor: '#3b82f6',
  padding: '12px 24px',
  borderRadius: '6px',
  fontSize: '16px',
  fontWeight: '600',
  color: '#ffffff',
  border: 'none',
  cursor: 'pointer',
  transition: 'all 0.2s ease-in-out',
};
```

#### React Native Implementation
```typescript
// Automatically uses StyleSheet
const buttonStyles = StyleSheet.create({
  button: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
});
```

## Theming

### Theme Provider

Wrap your app with the theme provider:

```typescript
import { ThemeProvider, defaultTheme } from '@ultimate-fantasy/ui-components';

function App() {
  return (
    <ThemeProvider theme={defaultTheme}>
      <YourAppContent />
    </ThemeProvider>
  );
}
```

### Custom Theme

```typescript
import { createTheme } from '@ultimate-fantasy/ui-components';

const customTheme = createTheme({
  colors: {
    primary: '#6366f1',
    secondary: '#64748b',
    background: '#f8fafc',
    surface: '#ffffff',
    text: '#1e293b',
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    headings: {
      h1: { fontSize: 32, fontWeight: '700' },
      h2: { fontSize: 24, fontWeight: '600' },
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
  },
});
```

### Dark Mode

```typescript
import { useTheme } from '@ultimate-fantasy/ui-components';

function ThemeToggle() {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <Button
      variant="ghost"
      onPress={toggleTheme}
      leftIcon={isDark ? 'sun' : 'moon'}
    >
      {isDark ? 'Light Mode' : 'Dark Mode'}
    </Button>
  );
}
```

## Accessibility

All components are built with accessibility in mind:

- **Keyboard Navigation** - Full keyboard support
- **Screen Readers** - Proper ARIA labels and roles
- **Focus Management** - Logical focus order
- **Color Contrast** - WCAG AA compliant colors
- **Reduced Motion** - Respects user preferences

```typescript
import { Button } from '@ultimate-fantasy/ui-components';

<Button
  accessibilityLabel="Save league settings"
  accessibilityHint="Saves your current league configuration"
  accessibilityRole="button"
>
  Save
</Button>
```

## Animation

Smooth animations and transitions built-in:

```typescript
import { AnimatedCard } from '@ultimate-fantasy/ui-components';

<AnimatedCard
  animationType="fadeIn"
  duration={300}
  delay={100}
>
  <p>This card will fade in smoothly</p>
</AnimatedCard>
```

## Storybook

Interactive component documentation is available via Storybook:

```bash
npm run storybook
```

Visit `http://localhost:6006` to explore all components with live examples.

## Development

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

### Visual Testing

```bash
npm run test:visual
```

### Storybook Development

```bash
npm run storybook:dev
```

## Platform-Specific Features

### Web-Only Features
- CSS custom properties for theming
- CSS transitions and animations
- Focus management with Tab navigation
- Hover states and cursor styles

### Mobile-Only Features
- Touch gestures and haptic feedback
- Native platform styling
- Safe area handling
- Keyboard avoidance

### Automatic Feature Detection

```typescript
import { platformUtils } from '@ultimate-fantasy/ui-components';

// Automatically adapts based on platform
const isNative = platformUtils.isNative();
const hasTouch = platformUtils.hasTouch();
const supportsCSSCustomProperties = platformUtils.supportsCSSVars();
```

## Contributing

1. Follow the design system guidelines
2. Ensure cross-platform compatibility
3. Add comprehensive tests
4. Update Storybook documentation
5. Maintain accessibility standards

## Dependencies

### Core Dependencies
- `react` ^18.0.0
- `react-native-reanimated` (for animations)

### Web Dependencies
- `framer-motion` - Web animations
- `@radix-ui/react-*` - Accessible primitives

### Mobile Dependencies
- `react-native-gesture-handler` - Touch gestures
- `react-native-svg` - Vector graphics

## File Structure

```
packages/ui-components/
├── src/
│   ├── primitives/          # Base components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Modal.tsx
│   ├── adapters/            # Platform adapters
│   │   └── platform.ts
│   ├── tokens/              # Design tokens
│   │   └── design-tokens.ts
│   ├── themes/              # Theme definitions
│   │   └── default.ts
│   └── utils/               # Utility functions
├── .storybook/              # Storybook configuration
└── stories/                 # Component stories
```

## License

MIT