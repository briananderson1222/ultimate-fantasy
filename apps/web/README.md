# Frontend (Next.js + React + Tailwind)

This app uses Next.js (App Router) with React Query for data, Tailwind utilities, and a small, accessible UI primitive set.

## Architecture

- App Router: `src/app/**` route segments; client components where interactivity is needed.
- Data layer: `src/services/`
  - `client.ts` defines `apiFetch` (base URL + auth header from localStorage).
  - `api.ts` hosts typed fetchers used by pages/components.
- UI primitives: `src/components/ui/` → `Button`, `Input`, `Card`, `Modal`, `Toast`, `Skeleton`, `EmptyState`, `Tabs`, `Badge`, `PageHeader`.
- Theming: CSS variables in `src/styles/theme.css`; runtime theming in `src/app/theme.tsx`.
- Providers: `src/app/providers.tsx` wraps React Query, ThemeProvider, ToastProvider.

## Component Library

Lightweight headless components with sensible a11y defaults.

- `Button`
  - Props: `variant = 'primary' | 'secondary' | 'ghost'`, `size = 'sm' | 'md' | 'lg'`, `loading`, `leftIcon`, `rightIcon`.
  - Usage:
    ```tsx
    import { Button } from '@/components/ui/button';
    <Button leftIcon={<Icon />} loading>Save</Button>
    <Button variant="secondary">Cancel</Button>
    ```
- `Input`
  - Props: native `<input>` plus `label`, `error`.
  - Usage:
    ```tsx
    import { Input } from "@/components/ui/input";
    <Input name="name" label="Name" error={errors.name} />;
    ```
- `Modal` (Radix Dialog)
  - Controlled via `open`/`onClose`. Optional `title`.
    ```tsx
    import { Modal } from "@/components/ui/modal";
    <Modal open={open} onClose={() => setOpen(false)} title="Settings">
      ...
    </Modal>;
    ```
- `Toast`
  - Wrap a subtree with `ToastProvider` and use `useToast()` to show toasts.
    ```tsx
    import { ToastProvider, useToast } from "@/components/ui/toast";
    // in component
    const { show } = useToast();
    show({ title: "Saved", description: "It worked" });
    ```
- `Tabs`
  - Roving tabindex + keyboard arrows supported.
    ```tsx
    import { Tabs } from "@/components/ui/tabs";
    <Tabs tabs={[{ value: "a", label: "A" }]} value={value} onChange={setValue} />;
    ```
- `PageHeader`, `Card`, `Skeleton`, `EmptyState`, `Badge` provide simple layout and states.

## Forms

Use `react-hook-form` + `zod` for schema‑driven validation.

- Pattern:
  - Define a Zod schema.
  - `useForm({ resolver: zodResolver(schema) })` from `@hookform/resolvers/zod`.
  - Bind fields via `register('field')`; read messages from `formState.errors`.
  - Submit with `<form onSubmit={handleSubmit(onSubmit)}>...<Button type="submit" />`.
- Example: see `src/app/leagues/create/page.tsx`.

## Theme Tokens

Design tokens live as CSS variables and can be changed at runtime.

- Base tokens: `src/styles/theme.css`
  ```css
  :root {
    --color-bg: rgb(249, 250, 251);
    --color-text: rgb(17, 24, 39);
    --color-primary: rgb(37, 99, 235);
    --radius-md: 8px;
    --space-3: 12px;
    /* ... */
  }
  [data-theme="dark"] {
    /* dark overrides */
  }
  ```
- Runtime theming: `ThemeProvider` sets `[data-theme]` and can apply custom vars.
  ```tsx
  import { useTheme } from "@/app/theme";
  const { setTheme, setCustom } = useTheme();
  setTheme("dark");
  setCustom({ "--color-primary": "#7c3aed" }); // switches to custom theme
  ```
- Theme Studio: `/settings/theme` lets you edit and apply a JSON object of CSS vars. Values persist to localStorage keys `uf_theme` and `uf_theme_custom`.

## API usage

- Backend URL: set `NEXT_PUBLIC_API_URL` to point at the backend.

## Testing

- Unit: Vitest + React Testing Library
  - `npm run test:unit` (JSDOM env, files under `tests/unit/**`).
- E2E: Playwright
  - `npm run test:e2e`

## UI Playground (Ladle)

- Interactive component playground powered by Ladle.
  - Start locally: `npm run play:ui`
  - Build static preview: `npm run build:ui`
  - Stories live alongside components under `src/**/*.stories.tsx`.

## Accessibility

- `eslint-plugin-jsx-a11y` rules enabled.
- Components include labels, roles, focus-visible rings, and keyboard support where applicable.

## Conventions

- Prefer headless, composable components with explicit a11y attributes.
- Keep API types near `src/services/api.ts` and derived from backend contracts.

## Radix + CVA Patterns

This UI leans on Radix primitives for accessible behavior and class-variance-authority (CVA) for styling variants.

- Radix-backed wrappers
  - `Modal` wraps Radix Dialog and handles focus management, accessible titles, and escape/overlay dismissal.
    ```tsx
    import { Modal } from "@/components/ui/modal";
    const [open, setOpen] = useState(false);
    <Modal open={open} onClose={() => setOpen(false)} title="Review">
      <p>Dialog content here.</p>
    </Modal>;
    ```
  - `ToastProvider` wraps Radix Toast. Use `useToast()` to show messages. Swiping/dismiss animations are enabled and respect reduced-motion.
    ```tsx
    import { useToast } from "@/components/ui/toast";
    const { show } = useToast();
    show({ title: "Saved", description: "Your changes are live." });
    ```
- Styling with CVA
  - `Button` uses CVA + tailwind-merge to define and merge variants and sizes.
    ```tsx
    import { Button } from "@/components/ui/button";
    // Built-in variants: primary | secondary | ghost; sizes: sm | md | lg
    <Button variant="secondary" size="sm">
      Secondary
    </Button>;
    ```
  - Adding a new visual variant (example):
    1. Extend variants in `src/components/ui/button.tsx` (add a key under `variant` in the `cva(...)`).
    2. Use via `<Button variant="newVariant">...`.
  - When composing custom components, prefer a `cva()` at the top of the file for variants and pass `className` through `twMerge()` to preserve consumer overrides.

Tips

- Keep interaction and accessibility in Radix; keep visuals in Tailwind classes.
- Don’t break focus order. Use `focus-visible` rings for keyboard users.
- Respect `prefers-reduced-motion` (already applied globally in `globals.css`).
