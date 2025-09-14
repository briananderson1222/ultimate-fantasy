# Data Model: Frontend Shared Logic Extraction

## Core Entities

### SharedPackage
**Purpose**: Represents a shared package in the monorepo
**Fields**:
- name: string (package identifier)
- version: string (semantic version)
- platform: 'shared' | 'web' | 'mobile' | 'universal'
- dependencies: string[] (package dependencies)
- exports: Export[] (public API surface)

**Validation Rules**:
- Name must follow npm package naming conventions
- Version must follow semantic versioning (MAJOR.MINOR.PATCH)
- Dependencies must be resolvable packages

### Export
**Purpose**: Represents a public API export from a shared package
**Fields**:
- name: string (export identifier)
- type: 'function' | 'component' | 'hook' | 'constant' | 'type'
- signature: string (TypeScript signature)
- platform: 'shared' | 'web' | 'mobile' | 'universal'
- deprecated: boolean (deprecation status)

**Validation Rules**:
- Name must be valid JavaScript identifier
- Signature must be valid TypeScript
- Platform compatibility must be documented

### ApiService
**Purpose**: Represents a shared API service module
**Fields**:
- name: string (service identifier)
- endpoints: Endpoint[] (API endpoints served)
- baseUrl: string (API base URL)
- authentication: boolean (requires auth)
- platform: 'universal' (works on both platforms)

**Relationships**:
- Used by both NextJS and React Native applications
- Depends on shared HTTP client configuration

### Endpoint
**Purpose**: Represents an API endpoint contract
**Fields**:
- path: string (URL path)
- method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
- requestSchema: object (request validation schema)
- responseSchema: object (response validation schema)
- authenticated: boolean (requires authentication)

**Validation Rules**:
- Path must be valid URL path
- Schemas must be valid JSON schema or Zod schema
- Method must be valid HTTP method

### UIComponent
**Purpose**: Represents a shared UI component
**Fields**:
- name: string (component name)
- props: ComponentProp[] (component properties)
- platforms: Platform[] (supported platforms)
- variants: string[] (available variants)
- dependencies: string[] (required peer dependencies)

**Relationships**:
- Has platform-specific implementations
- Uses shared design tokens

### ComponentProp
**Purpose**: Represents a component property definition
**Fields**:
- name: string (property name)
- type: string (TypeScript type)
- required: boolean (is required)
- defaultValue: any (default value if optional)
- description: string (property description)

### Platform
**Purpose**: Represents a target platform for components
**Fields**:
- name: 'web' | 'mobile'
- styling: 'tailwind' | 'stylesheet' (styling approach)
- imports: string[] (platform-specific imports)
- adapters: string[] (required style adapters)

### DesignToken
**Purpose**: Represents a design system token
**Fields**:
- name: string (token name)
- category: 'color' | 'spacing' | 'typography' | 'shadow'
- value: any (token value)
- webValue: any (web-specific value)
- mobileValue: any (mobile-specific value)

**Validation Rules**:
- Name must follow design token naming conventions
- Values must be valid for their category
- Platform values must be compatible with target platforms

### SharedHook
**Purpose**: Represents a custom React hook
**Fields**:
- name: string (hook name)
- parameters: HookParam[] (hook parameters)
- returnType: string (TypeScript return type)
- dependencies: string[] (other hooks or services used)
- platform: 'universal' (works on both platforms)

### HookParam
**Purpose**: Represents a parameter for a shared hook
**Fields**:
- name: string (parameter name)
- type: string (TypeScript type)
- optional: boolean (is optional)
- description: string (parameter description)

## State Transitions

### Package Lifecycle
1. **Development** → **Testing** → **Published** → **Deprecated**
2. **Development**: Active development, frequent changes
3. **Testing**: Feature complete, undergoing validation
4. **Published**: Stable, consumed by applications
5. **Deprecated**: Marked for removal, migration path provided

### Component Migration
1. **Web-Only** → **Extracted** → **Adapted** → **Universal**
2. **Web-Only**: Component exists only in NextJS app
3. **Extracted**: Component moved to shared package
4. **Adapted**: Platform-specific styling added
5. **Universal**: Component usable on both platforms

### API Service Migration
1. **Embedded** → **Extracted** → **Shared** → **Optimized**
2. **Embedded**: API calls in component files
3. **Extracted**: API calls in service files
4. **Shared**: Service files in shared package
5. **Optimized**: Cross-platform optimizations applied

## Relationships

- SharedPackage contains multiple Exports
- ApiService contains multiple Endpoints
- UIComponent has multiple ComponentProps
- UIComponent supports multiple Platforms
- Platform uses multiple DesignTokens
- SharedHook has multiple HookParams
- Export depends on other Exports (dependency graph)
- UIComponent depends on DesignTokens
- ApiService uses shared authentication patterns