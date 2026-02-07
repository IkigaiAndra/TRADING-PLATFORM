# Trading Analytics Platform - Backend

FastAPI-based backend for the Trading Analytics Platform.

## Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL client (optional, for manual database access)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and configure your settings (database URL, API keys, etc.)

### Database Setup

1. Start TimescaleDB with Docker Compose:
```bash
docker-compose up -d timescaledb
```

2. Wait for the database to be ready:
```bash
docker-compose logs -f timescaledb
```

3. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run property-based tests only:
```bash
pytest -m property
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic environment
├── app/
│   ├── api/             # API routes
│   ├── models/          # SQLAlchemy models
│   ├── services/        # Business logic
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection
│   ├── logging_config.py # Structured logging
│   └── main.py          # FastAPI application
├── tests/               # Test suite
│   ├── conftest.py      # Pytest fixtures
│   └── ...
├── .env.example         # Example environment variables
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Project configuration
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

Key configuration areas:
- **Database**: Connection URL, pool size
- **API**: Host, port, log level
- **Data Providers**: API keys for Polygon, IBKR
- **Notifications**: SMTP and Telegram configuration

## Logging

The application uses structured JSON logging. All logs include:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `component`: Logger name (module/class)
- `message`: Log message
- `context`: Additional contextual information
- `stack_trace`: Stack trace for errors

## API Documentation

Interactive API documentation is available at `/api/docs` when the server is running.

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes

### Testing

- Write unit tests for all business logic
- Write property-based tests for correctness properties
- Maintain >90% code coverage for critical components

### Database

- Use Alembic for all schema changes
- Never modify the database schema directly
- Test migrations in both upgrade and downgrade directions
