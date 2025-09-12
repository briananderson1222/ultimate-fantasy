# Ultimate Fantasy Platform — Backend

FastAPI + SQLAlchemy backend for the Ultimate Fantasy Platform.

## Requirements
- Python 3.11
- PostgreSQL (for development/testing via `DATABASE_URL`)

## Quickstart

1) Create and activate a virtual environment
```
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

2) Install dependencies (dev extras include linters and test tools)
```
pip install -U pip
pip install -e .[dev]
```

3) Set environment
```
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/ultimate_fantasy"
```

4) Run tests (contract, integration, unit, perf)
```
pytest -q
```

5) Lint and format
```
ruff check .
black .
isort .
mypy .
```

6) Run the server
```
uvicorn main:app --reload --app-dir src
```

## Project Structure
```
backend/
├── pyproject.toml
├── README.md
├── src/
│   ├── api/
│   ├── models/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    ├── perf/
    └── unit/
```

## Notes
- For local dev without DATABASE_URL, the app falls back to in-memory SQLite and auto-creates tables at startup.
- Alembic configuration/migrations are included (T035).
- Endpoints follow the contract in specs/001-ultimate-fantasy-platform/contracts/openapi.yml.
