# Ultimate Fantasy Platform

Welcome to the Ultimate Fantasy Platform, a modern, multi-sport fantasy platform. This repository contains the entire codebase for a comprehensive cross-platform fantasy sports experience.

## What's Inside?

This monorepo is organized into applications, shared packages, and supporting services:

### 🎯 Applications

-   **`./apps/web`**: Feature-rich web application built with Next.js, React, and Tailwind CSS. Provides the main user interface for managing leagues, teams, and players.
    -   [**Web App README**](./apps/web/README.md)

-   **`./apps/mobile`**: React Native mobile application consuming shared packages for a native mobile experience.
    -   [**Mobile App README**](./apps/mobile/README.md)

-   **`./apps/landing`**: Static landing page designed to attract new users and capture emails for a waitlist. Built with HTML, CSS, and JavaScript.
    -   [**Landing Page README**](./apps/landing/README.md)

### 🧱 Shared Packages

-   **`./packages/`**: Cross-platform shared packages enabling code reuse between web and mobile applications.
    -   [**Packages Overview**](./packages/README.md)
    -   [`@ultimate-fantasy/shared-logic`](./packages/shared-logic/) - Business logic, state management, utilities
    -   [`@ultimate-fantasy/api-client`](./packages/api-client/) - HTTP client and API services
    -   [`@ultimate-fantasy/ui-components`](./packages/ui-components/) - Cross-platform UI component library

### ⚙️ Backend Services

-   **`./apps/api`**: Robust backend API built with Python, FastAPI, and SQLAlchemy. Handles all business logic, data persistence, and user authentication.
    -   [**API README**](./apps/api/README.md)

## Getting Started

The fastest and most reliable way to get the entire platform running on your local machine is with Docker.

### Prerequisites

-   [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd ultimate-fantasy
    ```

2.  **Build and start the services:**

    This command will build the Docker images for the frontend and backend, and start them along with a PostgreSQL database.

    ```bash
    docker-compose up --build
    ```

3.  **Access the applications:**

    -   **Web App**: [http://localhost:3000](http://localhost:3000)
    -   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

To run the services in the background, use `docker-compose up -d --build`.

### Local Development without Docker

If you prefer to run the services directly on your machine, you can use the provided shell script which will set up and start both the backend and frontend.

-   **Prerequisites**: Python 3.11+, Node.js 20+, and a running PostgreSQL instance.
-   **Run**: `./start-local.sh`

For detailed manual setup instructions, please refer to the README files in the `apps/api` and `apps/web` directories.

## Development

### Architecture

This platform uses a modern monorepo architecture with shared packages:

```
ultimate-fantasy/
├── apps/
│   ├── web/                 # Next.js web application
│   ├── mobile/              # React Native mobile app
│   ├── api/                 # FastAPI backend services
│   └── landing/             # Static marketing site
├── packages/                # Shared cross-platform packages
│   ├── shared-logic/        # Business logic, hooks, utilities
│   ├── api-client/          # HTTP services and API types
│   └── ui-components/       # Cross-platform UI components
└── docs/                    # Documentation
```

### Development Scripts

| Command | Description |
|---------|-------------|
| `npm run dev:web` | Start Next.js web app development server |
| `npm run dev:mobile` | Start React Native mobile app development |
| `npm run dev:api` | Start FastAPI backend development server |
| `npm run dev:landing` | Start landing page development server |
| `npm run build:packages` | Build all shared packages |
| `npm run test:packages` | Test all shared packages |
| `npm run build` | Build all applications |
| `npm run test` | Run all tests |
| `npm run lint` | Lint all projects |

### Detailed Documentation

For comprehensive information on each component:

#### Applications
-   [**Web Development**](./apps/web/README.md) - Next.js web application
-   [**Mobile Development**](./apps/mobile/README.md) - React Native mobile app
-   [**Landing Page Development**](./apps/landing/README.md) - Static marketing site

#### Backend & Infrastructure
-   [**API Development**](./apps/api/README.md) - FastAPI backend services

#### Shared Packages
-   [**Packages Overview**](./packages/README.md) - Cross-platform shared packages
-   [**Deployment Guide**](./DEPLOYMENT.md) - Production deployment instructions
-   [**Contributing Guide**](./CONTRIBUTING.md) - Development guidelines

## Testing

The platform includes a comprehensive suite of tests to ensure quality and stability.

-   **API**: The backend includes unit, integration, contract, and performance tests that can be run with `pytest`. See the [API README](./apps/api/README.md#testing-and-quality) for more details.

-   **Web**: The frontend has unit tests (Vitest), end-to-end tests (Playwright), and visual regression tests. See the [web README](./apps/web/README.md#testing) for instructions.

-   **Validation Script**: A validation script is provided to check that all parts of the system are correctly configured and running.

    ```bash
    ./validate-setup.sh
    ```

## API Documentation

When the backend service is running, interactive API documentation is available through Swagger UI and ReDoc:

-   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)