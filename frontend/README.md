# Ultimate Fantasy Platform — Frontend

This project contains the frontend for the Ultimate Fantasy Platform, built with Next.js (App Router), React, and Tailwind CSS.

## Overview

The frontend provides the user interface for interacting with the Ultimate Fantasy world. It communicates with the backend API to fetch and manipulate data, offering a reactive and modern user experience.

## Key Technologies

-   **Framework**: [Next.js](https://nextjs.org/) (with App Router)
-   **UI Library**: [React](https://react.dev/)
-   **Styling**: [Tailwind CSS](https://tailwindcss.com/)
-   **Data Fetching**: [React Query](https://tanstack.com/query/latest) for server state management.
-   **Forms**: [React Hook Form](https://react-hook-form.com/) with [Zod](https://zod.dev/) for validation.
-   **Component Library**: A custom set of accessible UI primitives built with [Radix UI](https://www.radix-ui.com/) and styled with CVA (Class Variance Authority).
-   **Component Playground**: [Ladle](https://ladle.dev/) for interactive component development and documentation.

## Getting Started

### Prerequisites

-   Node.js >= 20
-   An instance of the backend API running and accessible.

### Environment Variables

Create a `.env.local` file in the `frontend` directory and add the following environment variable to point to your running backend API:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Quickstart

1.  **Install dependencies:**

    ```bash
    npm install
    ```

2.  **Run the development server:**

    ```bash
    npm run dev
    ```

    The application will be available at [http://localhost:3000](http://localhost:3000).

3.  **Authentication:**

    The UI reads the authentication token from the `uf_token` key in `localStorage`. For development, you can use the `DevAuthToken` component on any page to easily set or read a token.

## Scripts

-   `npm run dev`: Starts the development server.
-   `npm run build`: Creates a production build of the application.
-   `npm run start`: Starts the production server.
-   `npm run lint`: Lints the codebase using ESLint.
-   `npm run format`: Formats the code with Prettier.
-   `npm run typecheck`: Runs the TypeScript compiler to check for type errors.

## Architecture

-   **App Router**: Routes are defined in the `src/app/` directory using Next.js file-system routing.
-   **Data Layer**: Located in `src/services/`. `client.ts` configures the base API fetcher (including authentication headers), and `api.ts` contains typed functions for each API endpoint.
-   **UI Components**: Reusable UI primitives are in `src/components/ui/`. These are built to be accessible and composable.
-   **Theming**: A flexible theming system is implemented using CSS variables. The base theme is in `src/styles/theme.css`, and runtime theme switching is handled by `src/app/theme.tsx`.
-   **Providers**: `src/app/providers.tsx` wraps the application with essential context providers like React Query, ThemeProvider, and ToastProvider.

## Component Development

This project uses [Ladle](https://ladle.dev/) for developing and documenting components in isolation.

-   **Run the component playground:**

    ```bash
    npm run play:ui
    ```

-   **Stories**: Component stories are located alongside the components themselves (e.g., `src/components/ui/button.stories.tsx`).

## Testing

The project has both unit and end-to-end tests.

-   **Unit Tests**: Written with Vitest and React Testing Library. Run them with:

    ```bash
    npm run test:unit
    ```

-   **End-to-End Tests**: Written with Playwright. Run them with:

    ```bash
    npm run test:e2e
    ```

-   **Visual Regression Tests**: Playwright is also used for visual snapshot testing.

    ```bash
    npm run test:visual         # Run visual tests
    npm run test:visual:update  # Update snapshots
    ```

## Deployment

The application is configured for deployment on platforms like Vercel or any Node.js hosting environment. The `npm run build` command generates an optimized production-ready build in the `.next` directory.