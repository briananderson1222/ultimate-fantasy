# Animation System Documentation

## Overview

The Ultimate Fantasy platform includes a comprehensive animation system that provides subtle transitions, loading states, and microinteractions while respecting user accessibility preferences.

## Animation Tokens

All animations use CSS custom properties defined in `src/styles/theme.css`:

### Durations

- `--anim-duration-xs`: 120ms (quick interactions)
- `--anim-duration-sm`: 180ms (standard transitions)
- `--anim-duration-md`: 260ms (moderate animations)
- `--anim-duration-lg`: 380ms (longer animations)
- `--anim-duration-xl`: 500ms (extended animations)

### Easings

- `--anim-ease-standard`: cubic-bezier(0.2, 0, 0, 1) (standard material design)
- `--anim-ease-emphasized`: cubic-bezier(0.16, 1, 0.3, 1) (emphasized entrance)
- `--anim-ease-bounce`: cubic-bezier(0.68, -0.55, 0.265, 1.55) (playful bounce)
- `--anim-ease-elastic`: cubic-bezier(0.175, 0.885, 0.32, 1.275) (elastic effect)

### Scales & Transforms

- `--anim-scale-press`: 0.98 (button press feedback)
- `--anim-scale-hover`: 1.02 (hover lift effect)
- `--anim-translate-slide`: 8px (slide distance)

## Animation Classes

### Basic Animations

- `.animate-fade-in` - Fade in from transparent
- `.animate-fade-out` - Fade out to transparent
- `.animate-slide-up` - Slide up with fade
- `.animate-slide-down` - Slide down with fade
- `.animate-scale-in` - Scale in with fade
- `.animate-bounce-in` - Bouncy entrance

### Loading States

- `.animate-pulse` - Subtle opacity pulse
- `.animate-shimmer` - Shimmer effect for skeletons
- `.loading-spinner` - Rotating spinner
- `.loading-dots` - Animated dots

### Microinteractions

- `.hover-lift` - Lift on hover
- `.press-scale` - Scale down on press
- `.focus-ring` - Focus ring animation

### Toast Animations

- `.toast-enter` - Toast slide-in animation
- `.toast-exit` - Toast slide-out animation

## Components

### Skeleton

```tsx
import { Skeleton, SkeletonCard, SkeletonList } from '@/components/ui';

// Basic skeleton
<Skeleton variant="text" width="3/4" />

// Multi-line text
<Skeleton variant="text" lines={3} />

// Preset components
<SkeletonCard />
<SkeletonList items={5} />
```

### EmptyState

```tsx
import { EmptyState } from "@/components/ui";

<EmptyState
  icon={<SearchIcon />}
  title="No results found"
  description="Try adjusting your search criteria"
  action={<Button>Clear filters</Button>}
/>;
```

### Enhanced Components

All UI components include animation enhancements:

- **Button**: Press scaling, hover lift, loading spinner
- **Input**: Focus transitions, error slide-in
- **Toast**: Slide animations with swipe-to-dismiss

## Reduced Motion Support

The animation system respects `prefers-reduced-motion: reduce`:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Essential animations (like loading spinners) are replaced with static states when reduced motion is preferred.

## Usage Guidelines

### Do's

- Use subtle animations that enhance UX
- Respect animation tokens for consistency
- Test with reduced motion preferences
- Use appropriate durations (shorter for interactions, longer for state changes)

### Don'ts

- Avoid excessive or distracting animations
- Don't use animations that could trigger vestibular disorders
- Don't animate essential content that users need to read
- Avoid conflicting with user accessibility preferences

## Performance

- Animations use `transform` and `opacity` for GPU acceleration
- `will-change` is applied sparingly and removed after animations
- Reduced motion preferences disable most animations for better performance
- Skeleton animations use efficient CSS-only implementations

## Testing

Animation components include basic tests in `src/components/ui/__tests__/animations.test.tsx` that verify:

- Animation classes are applied correctly
- Components render with expected structure
- Reduced motion preferences are respected (via CSS)
