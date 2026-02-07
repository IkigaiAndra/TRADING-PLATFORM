# Task 4: End-to-End Data Ingestion Testing Guide

## Overview

Task 4 is a checkpoint to ensure the complete data ingestion pipeline works end-to-end. This guide will help you set up the environment and run comprehensive tests.

## Prerequisites

Before running the end-to-end tests, you need:

1. **Docker Desktop** installed and running
2. **Python 3.10+** installed
3. **Git** (already have this if you're reading this!)

## Step-by-Step Setup

### Step 1: Start Docker Desktop

1. Open Docker Desktop application
2. Wait for Docker to fully start (the whale icon should be steady, not animated)
3. Verify Docker is running:
   ```powershell
   docker --version
   docker ps
   ```

### Step 2: Start TimescaleDB

From the project root directory:

```powershell
# Start the database
docker-compose up -d timescaledb

# Wait for database to be ready (about 10-15 seconds)
Start-Sleep -Seconds 15

# Check database is running
docker-compose ps
docker-compose logs timescaledb
```

You should see output indicating TimescaleDB is ready to accept connections.

### Step 3: Set Up Python Virtual Environment

From the `backend` directory:

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# The default values should work for local development
# No need to edit unless you changed Docker settings
```

### Step 5: Run Database Migrations

```powershell
# Make sure you're in the backend directory with venv activated
alembic upgrade head
```

You should see output showing migrations being applied:
- `001_create_instruments_table`
- `002_create_prices_hypertable`
- `003_create_indicators_patterns_tables`

### Step 6: Run End-to-End Tests

Now you're ready to run the comprehensive end-to-end test:

```powershell
# Run the end-to-end test script
python test_end_to_end_ingestion.py
```

## What the Tests Verify

The end-to-end test script (`test_end_to_end_ingestion.py`) performs the following checks:

### 1. Prerequisites Check
- ✅ All modules can be imported
- ✅ Database connection is working
- ✅ Database schema is up to date

### 2. Database Operations Test
- ✅ Create test instrument
- ✅ Insert price data
- ✅ Query price data
- ✅ Test upsert (update existing records)

### 3. Validation Module Test
- ✅ Valid OHLC accepted
- ✅ Invalid OHLC rejected (high < low)
- ✅ Positive volume accepted
- ✅ Negative volume rejected
- ✅ Past timestamp accepted
- ✅ Future timestamp rejected
- ✅ Aligned 5m timestamp accepted
- ✅ Misaligned 5m timestamp rejected

### 4. Data Provider Test
- ✅ Yahoo Finance provider created
- ✅ Fetch EOD data for AAPL (last 5 days)
- ✅ Verify candle data structure

### 5. Ingestion Service Test
- ✅ Create ingestion service
- ✅ Ingest EOD data for AAPL
- ✅ Verify data stored in database
- ✅ Test idempotence (re-ingest same data)

### 6. Data Quality Verification
- ✅ All candles satisfy OHLC invariants
- ✅ All volumes are non-negative
- ✅ No future timestamps
- ✅ All data fields are complete

## Expected Output

When all tests pass, you should see:

```
======================================================================
🎉 ALL TESTS PASSED! 🎉
======================================================================

✅ Task 4 Complete: Data ingestion works end-to-end!

The complete data ingestion pipeline is working correctly:
  ✓ Database connectivity and operations
  ✓ Validation module
  ✓ Data provider (Yahoo Finance)
  ✓ Ingestion service with fallback and upsert
  ✓ Data quality verification

You can now proceed to the next task!
```

## Running Unit Tests

In addition to the end-to-end test, you should also run the unit test suite:

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/test_validation.py -v
pytest tests/test_data_providers.py -v
pytest tests/test_ingestion.py -v
```

## Troubleshooting

### Docker Not Running

**Error**: `docker: The term 'docker' is not recognized...`

**Solution**: 
1. Install Docker Desktop from https://www.docker.com/products/docker-desktop
2. Start Docker Desktop
3. Wait for it to fully initialize

### Database Connection Failed

**Error**: `Database connection failed: could not connect to server`

**Solution**:
1. Make sure Docker is running: `docker ps`
2. Start TimescaleDB: `docker-compose up -d timescaledb`
3. Wait 15 seconds for database to initialize
4. Check logs: `docker-compose logs timescaledb`

### Missing Tables

**Error**: `Missing tables: ['instruments', 'prices']`

**Solution**:
1. Make sure you're in the backend directory
2. Activate virtual environment: `.\venv\Scripts\activate`
3. Run migrations: `alembic upgrade head`

### Import Errors

**Error**: `ImportError: No module named 'app'`

**Solution**:
1. Make sure virtual environment is activated: `.\venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Make sure you're running from the backend directory

### Yahoo Finance API Issues

**Warning**: `Fetch failed: Yahoo Finance API error`

**Note**: This is not a critical failure. Yahoo Finance has rate limits and may occasionally fail. The test script will continue with other tests. The important thing is that the ingestion service handles the error gracefully.

## Manual Testing

You can also manually test the ingestion pipeline:

```python
# Start Python REPL
python

# Import required modules
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app.models.instrument import Instrument
from app.services.ingestion import IngestionService
from app.services.data_providers import YahooFinanceProvider

# Create database session
db = SessionLocal()

# Create test instrument
instrument = Instrument(
    symbol="AAPL",
    instrument_type="equity",
    metadata={"exchange": "NASDAQ"}
)
db.add(instrument)
db.commit()
db.refresh(instrument)

# Create ingestion service
provider = YahooFinanceProvider()
service = IngestionService(providers=[provider], db=db)

# Ingest data
result = service.ingest_eod(
    instrument_id=instrument.instrument_id,
    symbol="AAPL",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    timeframe='1D'
)

# Check result
print(f"Success: {result.success}")
print(f"Candles fetched: {result.candles_fetched}")
print(f"Candles stored: {result.candles_stored}")
print(f"Provider: {result.provider_used}")

# Query stored data
from app.models.price import Price
prices = db.query(Price).filter(
    Price.instrument_id == instrument.instrument_id
).limit(5).all()

for price in prices:
    print(f"{price.timestamp}: O={price.open} H={price.high} L={price.low} C={price.close}")

# Cleanup
db.close()
```

## Verification Scripts

You can also run the individual verification scripts:

```powershell
# Verify validation module
python verify_validation.py

# Verify data providers
python verify_data_providers.py

# Verify ingestion service
python verify_ingestion.py
```

## Next Steps

Once all tests pass:

1. ✅ Mark Task 4 as complete
2. ✅ Commit your changes
3. ✅ Proceed to Task 5: Implement basic technical indicators

## Task 4 Completion Checklist

- [ ] Docker Desktop installed and running
- [ ] TimescaleDB container started
- [ ] Python virtual environment created and activated
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] End-to-end test script passes
- [ ] Unit tests pass
- [ ] Data quality verified in database

## Summary

Task 4 validates that:

1. **Database Infrastructure**: TimescaleDB is properly configured with hypertables
2. **Validation Module**: All OHLC, volume, and timestamp validations work correctly
3. **Data Provider**: Yahoo Finance integration fetches real market data
4. **Ingestion Service**: Complete pipeline with provider fallback, validation, and upsert
5. **Data Quality**: All stored data satisfies correctness invariants

This checkpoint ensures the foundation is solid before moving on to indicator computation and pattern detection.

## Questions?

If you encounter any issues not covered in this guide:

1. Check the error message carefully
2. Review the troubleshooting section
3. Check Docker and database logs: `docker-compose logs timescaledb`
4. Verify all prerequisites are met
5. Ask for help with specific error messages

Good luck! 🚀
