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
-   **For backend development:** See the [backend/README.md](./backend/README.md).
-   **For frontend development:** See the [frontend/README.md](./frontend/README.md).

## Coding Style

We enforce a consistent coding style across the project using automated tools. Please ensure your contributions adhere to these styles.

-   **Backend (Python):**
    -   **Formatting:** We use `black` for code formatting and `isort` for import sorting.
    -   **Linting:** We use `ruff` for linting and `mypy` for static type checking.
    -   You can run all checks with:
        ```bash
        cd backend
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
        cd frontend
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

▌I want to plan out detailed action plan for three big initiatives for my applications in this repo. 1. Related to modularizing the backend with the idea that we can split out the backend into microservices in the
▌future when it makes sense financially to do so. Treat each domain as a module  such that each domain could be owned by different teams if needed 2. I want to split out all shared logic in our 'frontend'
▌application that is currently nextjs. I am planning to introduce mobile applications via react native and want as much shared logic as possible  3. UI Overhaul with the attached images as inspiration for an easy to
▌use user interface that can be pretty consistent across both the nextjs AND react native frontends C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\179eb8c4-61e0-4fe0-b6b2-d50d2080dc19.JPEG
▌C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\314bbc92-300c-4282-be2c-c235f31ae276.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\815bf813-f1df-4036-bfd8-
▌327cea1476d0.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\926a0012-4973-424d-95ce-8aa0091a3512.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\8770d59c-
▌5dcf-493a-ab1d-d4934e2cf181.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\2791709a-77a1-4d33-8329-29c661465eba.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-
▌examples\e26eba5d-60e6-47c5-96e0-afcbd8ed751b.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\06f09582-3af8-4f42-aa1c-b25b20b237c7.JPEG C:\Users\ander\Downloads\UX-examples-
▌20250914T202843Z-1-001\UX-examples\6e44e462-74f4-4683-80dd-4c94fc16bfb5.JPEG C:\Users\ander\Downloads\UX-examples-20250914T202843Z-1-001\UX-examples\08f9e695-4a63-4264-8fb2-b55593f4a645.JPEG