# Research: Frontend Shared Logic Extraction

## Package Architecture

**Decision**: Monorepo architecture with workspace-based shared packages using existing project structure

**Rationale**:
- Current project already has frontend/backend separation
- Adding packages/ directory leverages monorepo benefits without full restructuring
- Enables efficient code sharing while maintaining platform-specific optimizations
- Supports unified build processes with proper dependency management

**Alternatives considered**:
- Full Turborepo migration (too disruptive for current project)
- Separate repositories (loses unified development benefits)
- Single shared package (reduces modularity and testing isolation)

## TypeScript Configuration

**Decision**: Extend existing TypeScript configs with shared path mappings

**Rationale**:
- NextJS already has optimized TypeScript configuration
- React Native will use @react-native/typescript-config
- Shared packages can use consistent path mappings across platforms
- Platform-specific JSX settings handle React vs React Native differences

**Alternatives considered**:
- Single shared tsconfig (incompatible with platform differences)
- Completely separate configs (loses shared type safety benefits)

## Build and Bundling Strategy

**Decision**: Rollup for shared package building, keep existing NextJS bundling

**Rationale**:
- Rollup excels at building packages for consumption by multiple platforms
- NextJS handles web bundling optimally with built-in system
- React Native will use Metro (standard and zero-config)
- Each tool optimized for its specific use case

**Alternatives considered**:
- Webpack for everything (complex setup for package building)
- Metro for web (experimental and limited ecosystem)

## UI Component Sharing

**Decision**: Design token-based system with platform-specific styling adapters

**Rationale**:
- Design tokens provide shared design language
- Platform adapters handle CSS vs ViewStyle differences
- Maintains visual consistency while respecting platform conventions
- Current Tailwind system can generate design tokens

**Alternatives considered**:
- react-native-web (limited styling capabilities)
- Custom universal components (high maintenance overhead)

## State Management

**Decision**: Zustand for shared state management

**Rationale**:
- Excellent cross-platform compatibility
- Works identically in NextJS and React Native
- Lightweight and simple API reduces complexity
- Compatible with existing React Query usage

**Alternatives considered**:
- Redux Toolkit (overkill for current needs)
- React Context (doesn't scale for complex shared state)

## API Client Pattern

**Decision**: Extract existing API calls into shared service files using fetch + React Query

**Rationale**:
- Leverage existing React Query infrastructure
- Native fetch API works consistently across platforms
- Current API patterns can be extracted without major changes
- Maintains existing error handling and caching benefits

**Alternatives considered**:
- Axios (additional dependency, current project uses fetch)
- Platform-specific solutions (defeats sharing purpose)

## Testing Strategy

**Decision**: Jest + React Testing Library for unit tests, maintain existing Playwright for E2E

**Rationale**:
- Jest provides consistent testing environment across platforms
- React Testing Library works with React Native Testing Library
- Existing Playwright tests can validate web functionality
- Layered approach covers unit, integration, and E2E scenarios

**Alternatives considered**:
- Detox for React Native E2E (premature until mobile app exists)
- Single testing tool (no tool covers all scenarios effectively)

## Package Structure

**Decision**: Four separate packages in packages/ directory

**Rationale**:
- Separation of concerns: logic, UI, API, mobile app
- Independent versioning and testing
- Clear boundaries for different types of code
- Supports gradual migration approach

**Alternatives considered**:
- Three packages only (mobile app will be needed for validation)
- Single shared package (reduces modularity)

## Migration Strategy

**Decision**: Gradual extraction starting with API layer, then business logic, then UI components

**Rationale**:
- API extraction has lowest risk and highest immediate value
- Business logic extraction provides reusable utilities
- UI component extraction requires most platform-specific work
- Allows testing and validation at each step

**Alternatives considered**:
- Big bang migration (too risky)
- UI-first approach (highest complexity first)