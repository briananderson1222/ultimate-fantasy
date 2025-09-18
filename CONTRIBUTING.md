# Contributing to Ultimate Fantasy

First off, thank you for considering contributing to the Ultimate Fantasy platform. It's people like you that make open source such a great community.

This document provides guidelines for contributing to the project. Please read it carefully to ensure a smooth and effective contribution process.

## How to Contribute

We welcome contributions in various forms, including:

-   Reporting bugs and issues.
-   Suggesting new features or enhancements.
-   Improving documentation.
-   Writing code to fix bugs or add new features.

### Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** to your local machine: `git clone https://github.com/your-username/ultimate-fantasy.git`
3.  **Create a new branch** for your changes: `git checkout -b feature/your-amazing-feature` or `fix/issue-number`.
4.  **Make your changes** and commit them with clear, descriptive messages.
5.  **Push your changes** to your fork: `git push origin feature/your-amazing-feature`.
6.  **Open a pull request** to the `main` branch of the original repository.

## Development Setup

To get your development environment set up, please follow the instructions in the `README.md` files of the respective projects:

-   **For the entire platform (recommended):** See the main [README.md](./README.md) for instructions on how to get the full stack running with Docker.
-   **For backend development:** See the [apps/api/README.md](./apps/api/README.md).
-   **For frontend development:** See the [apps/web/README.md](./apps/web/README.md).

## Coding Style

We enforce a consistent coding style across the project using automated tools. Please ensure your contributions adhere to these styles.

-   **Backend (Python):**
    -   **Formatting:** We use `black` for code formatting and `isort` for import sorting.
    -   **Linting:** We use `ruff` for linting and `mypy` for static type checking.
    -   You can run all checks with:
        ```bash
        cd apps/api
        ruff check .
        black --check .
        isort --check-only .
        mypy .
        ```

-   **Frontend (TypeScript/React):**
    -   **Formatting:** We use `prettier` for code formatting.
    -   **Linting:** We use `eslint` to catch common issues.
    -   You can run all checks with:
        ```bash
        cd apps/web
        npm run format:check
        npm run lint
        npm run typecheck
        ```

## Running Tests

All contributions must pass the existing tests. If you are adding a new feature, please include tests for it.

-   **Backend Tests:**
    ```bash
    cd backend
    pytest
    ```

-   **Frontend Tests:**
    ```bash
    cd frontend
    npm test
    ```

-   **End-to-End (E2E) Tests:**
    Please see the instructions in the main [README.md](./README.md#testing) for running the Playwright E2E tests.

## Submitting a Pull Request

When you are ready to submit a pull request, please ensure the following:

-   [ ] Your code builds and runs without errors.
-   [ ] All tests pass.
-   [ ] Your code adheres to the coding style guidelines.
-   [ ] You have written clear and concise commit messages.
-   [ ] You have updated the documentation if your changes require it.
-   [ ] Your pull request has a descriptive title and a clear summary of the changes.

Thank you for your contribution!

## Additional Development Guidelines

### Shared Packages

When working with the shared packages in `packages/`, ensure cross-platform compatibility:

```bash
# Test packages individually
cd packages/shared-logic
npm test

cd packages/ui-components
npm test

cd packages/api-client
npm test

# Test packages together
npm run test:packages
```

### Platform-Specific Testing

- **Web Application**: Tests use Vitest and Playwright
- **Mobile Application**: Tests use Jest and Detox
- **API**: Tests use pytest with multiple test types (unit, integration, contract, performance)

### Code Quality Standards

All code must pass:
- TypeScript compilation (`npm run typecheck`)
- ESLint rules (`npm run lint`)
- Prettier formatting (`npm run format:check`)
- All existing tests (`npm test`)

## Package Management

This project uses:
- **Node.js applications**: npm with workspaces
- **Python API**: uv for fast dependency management
- **Cross-platform packages**: Shared dependencies across web and mobile