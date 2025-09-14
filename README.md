# Ultimate Fantasy Platform

Welcome to the Ultimate Fantasy Platform, a modern, multi-sport fantasy platform. This repository contains the entire codebase, including a backend API, a frontend web application, and a static landing page.

## What's Inside?

This monorepo is organized into three main projects:

-   **`./backend`**: A robust backend API built with Python, FastAPI, and SQLAlchemy. It handles all business logic, data persistence, and user authentication for the platform.
    -   [**Backend README**](./backend/README.md)

-   **`./frontend`**: A feature-rich frontend application built with Next.js, React, and Tailwind CSS. It provides the main user interface for managing leagues, teams, and players.
    -   [**Frontend README**](./frontend/README.md)

-   **`./landing`**: A simple, static landing page designed to attract new users and capture emails for a waitlist. It is built with plain HTML, CSS, and JavaScript.
    -   [**Landing Page README**](./landing/README.md)

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

    -   **Frontend**: [http://localhost:3000](http://localhost:3000)
    -   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

To run the services in the background, use `docker-compose up -d --build`.

### Local Development without Docker

If you prefer to run the services directly on your machine, you can use the provided shell script which will set up and start both the backend and frontend.

-   **Prerequisites**: Python 3.11+, Node.js 20+, and a running PostgreSQL instance.
-   **Run**: `./start-local.sh`

For detailed manual setup instructions, please refer to the README files in the `backend` and `frontend` directories.

## Development

For detailed information on the architecture, dependencies, and scripts for each project, please consult their respective README files:

-   [**Backend Development**](./backend/README.md)
-   [**Frontend Development**](./frontend/README.md)
-   [**Landing Page Development**](./landing/README.md)

## Testing

The platform includes a comprehensive suite of tests to ensure quality and stability.

-   **Backend**: The backend includes unit, integration, contract, and performance tests that can be run with `pytest`. See the [backend README](./backend/README.md#testing-and-quality) for more details.

-   **Frontend**: The frontend has unit tests (Vitest), end-to-end tests (Playwright), and visual regression tests. See the [frontend README](./frontend/README.md#testing) for instructions.

-   **Validation Script**: A validation script is provided to check that all parts of the system are correctly configured and running.

    ```bash
    ./validate-setup.sh
    ```

## API Documentation

When the backend service is running, interactive API documentation is available through Swagger UI and ReDoc:

-   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)