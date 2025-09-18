# Ultimate Fantasy Platform — Backend

This project provides the backend API for the Ultimate Fantasy Platform. It is built with Python 3.11, FastAPI, and SQLAlchemy.

## Overview

The backend exposes a RESTful API to manage fantasy leagues, teams, players, and all related game logic. It handles user authentication, data persistence, and business logic for the entire platform.

## Architecture

The backend follows a standard layered architecture:

-   **API Layer (`src/api`)**: Defines the FastAPI routers and endpoints. This layer is responsible for handling incoming HTTP requests, validating data using Pydantic models, and returning responses.
-   **Service Layer (`src/services`)**: Contains the core business logic of the application. Services are called by the API layer to perform operations.
-   **Data Access Layer (`src/models`)**: Defines the SQLAlchemy database models and schema. All database interactions are handled through these models.

Middleware for authentication and logging is applied in `src/main.py`.

## Getting Started

### Prerequisites

-   Python 3.11
-   PostgreSQL (recommended for development) or an in-memory SQLite database (default fallback).

### Quickstart

1.  **Create and activate a virtual environment:**

    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate  # For Windows: .venv\Scripts\activate
    ```

2.  **Install dependencies:**

    The project uses `uv` for dependency management. The `--all-extras` flag includes tools for testing, linting, and formatting.

    ```bash
    uv sync --all-extras
    ```

3.  **Configure the database:**

    Set the `DATABASE_URL` environment variable to point to your PostgreSQL instance. If this is not set, the application will default to an in-memory SQLite database, which is useful for quick tests but does not persist data.

    ```bash
    export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/ultimate_fantasy"
    ```

4.  **Run database migrations:**

    The project uses Alembic to manage database schema migrations. To upgrade your database to the latest version, run:

    ```bash
    alembic upgrade head
    ```

    To create a new migration after changing a model, use:

    ```bash
    alembic revision --autogenerate -m "A descriptive message for your migration"
    ```

5.  **Run the server:**

    Uvicorn is used to run the FastAPI application via uv. The `--reload` flag enables hot-reloading for development.

    ```bash
    uv run uvicorn main:app --reload --app-dir src
    ```

    The API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Testing and Quality

The project includes a comprehensive test suite and linting configuration to ensure code quality.

-   **Run tests:**

    Tests are organized into `contract`, `integration`, `unit`, and `perf` directories. You can run all tests with `pytest` via uv.

    ```bash
    uv run pytest -q
    ```

-   **Lint and format:**

    The project uses `ruff` for linting, `black` for formatting, `isort` for import sorting, and `mypy` for static type checking.

    ```bash
    uv run ruff check .
    uv run black .
    uv run isort .
    uv run mypy .
    ```

## Project Structure

```
apps/api/
├── alembic/              # Alembic migration scripts
├── alembic.ini           # Alembic configuration
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # This file
├── src/
│   ├── api/              # FastAPI routers and endpoints
│   ├── models/           # SQLAlchemy data models
│   └── services/         # Business logic
└── tests/
    ├── contract/         # API contract tests
    ├── integration/      # Integration tests
    ├── perf/             # Performance tests
    └── unit/             # Unit tests
```