[README.md](https://github.com/user-attachments/files/25154689/README.md)
# Trading Analytics Platform

Full-stack market analytics and portfolio management system designed for production deployment in quantitative trading environments.

## Overview

The Trading Analytics Platform ingests multi-frequency equity data (EOD and intraday), computes technical indicators and statistical patterns, generates trading signals, and provides professional-grade charting and portfolio analytics.

### Key Features

- 📊 **Professional Charting**: TradingView-style charts with indicators and patterns
- 📈 **Technical Analysis**: Advanced indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ALMA, VWAP)
- 🔍 **Pattern Recognition**: Trend detection, momentum regimes, volatility states, breakouts
- 🎯 **Signal Generation**: Configurable trading signals based on patterns and indicators
- 🔔 **Smart Alerts**: Real-time notifications via Email, Telegram, and Dashboard
- 💼 **Portfolio Tracking**: Track trades, positions, and performance metrics
- ⚡ **Real-time Updates**: WebSocket-based live data streaming
- 🔧 **Instrument Agnostic**: Supports equities, options, and futures

## Architecture

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- TimescaleDB (PostgreSQL + time-series extension)
- Hypothesis (property-based testing)

**Frontend:**
- React 18 + TypeScript
- TradingView Lightweight Charts
- React Query (data fetching)
- Vite (build tool)
- Fast-check (property-based testing)

**Infrastructure:**
- Docker Compose (local development)
- Alembic (database migrations)

### Project Structure

```
trading-analytics-platform/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   ├── tests/           # Test suite
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
├── docker-compose.yml   # Docker services
└── README.md           # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose

### 1. Start the Database

```bash
docker-compose up -d timescaledb
```

Wait for the database to be ready:
```bash
docker-compose logs -f timescaledb
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the dev server
npm run dev
```

Frontend will be available at http://localhost:3000

## Development

### Backend Development

```bash
cd backend

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run tests
npm test

# Run linter
npm run lint

# Build for production
npm run build
```

## Testing Strategy

The platform employs both unit testing and property-based testing:

- **Unit Tests**: Specific examples, edge cases, integration points
- **Property-Based Tests**: Universal properties across randomized inputs

### Property-Based Testing

- **Backend**: Uses Hypothesis (minimum 100 iterations per property)
- **Frontend**: Uses Fast-check (minimum 100 iterations per property)

All 40 correctness properties from the design document have corresponding tests.

## Configuration

### Backend Configuration

Environment variables (`.env`):
- `DATABASE_URL`: PostgreSQL connection string
- `POLYGON_API_KEY`: Polygon.io API key (for intraday data)
- `IBKR_API_KEY`: Interactive Brokers API key
- `SMTP_*`: Email notification settings
- `TELEGRAM_*`: Telegram notification settings

### Frontend Configuration

Environment variables (`.env`):
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL

## API Documentation

Interactive API documentation is available at `/api/docs` when the backend is running.

Key endpoints:
- `GET /api/v1/instruments` - List instruments
- `GET /api/v1/prices/{instrument_id}` - Get price data
- `GET /api/v1/indicators/{instrument_id}` - Get indicators
- `GET /api/v1/patterns/{instrument_id}` - Get patterns
- `GET /api/v1/signals/{instrument_id}` - Get signals
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/portfolio/positions` - Get positions
- `GET /api/v1/portfolio/metrics` - Get performance metrics

## Database Schema

The platform uses TimescaleDB for efficient time-series data storage:

- **instruments**: Instrument metadata (equities, options, futures)
- **prices**: OHLCV data (hypertable, partitioned by time)
- **indicators**: Computed indicator values (hypertable)
- **patterns**: Detected patterns
- **signals**: Generated trading signals
- **alerts**: User-defined alerts
- **trades**: Trade history
- **positions**: Current positions

## Deployment

### Production Deployment

1. Build frontend: `cd frontend && npm run build`
2. Serve frontend with Nginx or similar
3. Run backend with Gunicorn/Uvicorn (4-8 workers)
4. Use managed PostgreSQL with TimescaleDB extension
5. Set up SSL/TLS certificates
6. Configure monitoring and logging

### Docker Deployment

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Performance

Target performance metrics:
- API response time: p95 < 200ms, p99 < 500ms
- Indicator computation: < 100ms for 1000 candles
- Pattern detection: < 200ms for 1000 candles
- Database query time: p95 < 50ms

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- TLS/SSL for all communication
- API rate limiting
- Input validation and sanitization
- Secrets management (environment variables)

## License

Proprietary - All rights reserved

## Support

For questions or issues, please contact the development team.

## Roadmap

### Phase 1: Core Platform (EOD Equities) ✅
- Data ingestion for EOD equity data
- Basic indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
- Trend and momentum patterns
- Chart UI with candlesticks and indicator overlays
- REST API

### Phase 2: Intraday Expansion (In Progress)
- Intraday data ingestion (5m, 1m)
- Advanced indicators (ALMA, rolling volatility, VWAP)
- Breakout and mean reversion patterns
- WebSocket real-time updates

### Phase 3: Signals + Portfolio
- Signal generation engine
- Alert system with notifications
- Portfolio tracking
- Performance metrics

### Phase 4: Derivatives-Ready
- Options support
- Futures support
- Greeks calculation
- Multi-leg positions
