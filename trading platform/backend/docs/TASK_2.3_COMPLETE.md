# Task 2.3: Create Prices Hypertable with TimescaleDB - COMPLETE

## Overview

This task implements the prices table as a TimescaleDB hypertable for storing OHLCV (Open, High, Low, Close, Volume) time-series data. The implementation follows the design specifications and includes proper validation, indexing, and partitioning.

## Implementation Details

### 1. Price Model (`app/models/price.py`)

Created SQLAlchemy model with the following features:

**Columns:**
- `instrument_id` (Integer, Foreign Key): References instruments table
- `timestamp` (TIMESTAMP): Candle timestamp (partition key)
- `timeframe` (String): Candle frequency ('1D', '5m', '1m')
- `open` (NUMERIC(20,6)): Opening price
- `high` (NUMERIC(20,6)): Highest price
- `low` (NUMERIC(20,6)): Lowest price
- `close` (NUMERIC(20,6)): Closing price
- `volume` (BIGINT): Trading volume

**Constraints:**
- Composite primary key: (instrument_id, timestamp, timeframe)
- Foreign key to instruments table with CASCADE delete
- Check constraint: OHLC relationships (Low ≤ Open ≤ High AND Low ≤ Close ≤ High)
- Check constraint: Non-negative volume

**Indexes:**
- Composite index on (instrument_id, timeframe, timestamp) for efficient queries

**Validation Methods:**
- `validate_ohlc()`: Validates OHLC price relationships
- `validate_volume()`: Validates non-negative volume
- `is_valid()`: Comprehensive validation check

**Relationship:**
- `instrument`: Relationship to Instrument model

### 2. Database Migration (`alembic/versions/2024_01_15_1500-002_create_prices_hypertable.py`)

Created Alembic migration that:

1. **Creates prices table** with all columns and constraints
2. **Creates composite index** on (instrument_id, timeframe, timestamp)
3. **Converts to TimescaleDB hypertable**:
   - Partitioned by timestamp
   - 7-day chunk interval for optimal performance
4. **Adds check constraints**:
   - OHLC relationship validation
   - Non-negative volume validation
5. **Adds foreign key** to instruments table with CASCADE delete

### 3. Tests

#### Unit Tests (`tests/test_price_model.py`)

Comprehensive unit tests covering:
- ✅ Creating valid price records
- ✅ OHLC validation (valid and invalid cases)
- ✅ Volume validation (positive, zero, negative)
- ✅ Foreign key constraint enforcement
- ✅ Composite primary key uniqueness
- ✅ Multiple timeframes for same instrument
- ✅ Instrument relationship
- ✅ String representation

#### Integration Tests (`tests/test_price_integration.py`)

Integration tests covering:
- ✅ Hypertable configuration verification
- ✅ Time-based partitioning (chunks)
- ✅ Composite index performance
- ✅ Bulk insert performance (1000 records)
- ✅ Time range queries
- ✅ Multiple instruments queries
- ✅ Cascade delete behavior
- ✅ Database check constraints (OHLC and volume)

### 4. Verification Script (`scripts/verify_prices_table.py`)

Created verification script that checks:
- Table existence
- Hypertable configuration
- Column definitions
- Index presence
- Constraint definitions
- Foreign key relationships

## Database Schema

```sql
CREATE TABLE prices (
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 6) NOT NULL,
    high NUMERIC(20, 6) NOT NULL,
    low NUMERIC(20, 6) NOT NULL,
    close NUMERIC(20, 6) NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (instrument_id, timestamp, timeframe),
    CONSTRAINT ck_prices_ohlc_relationships CHECK (
        low <= open AND open <= high AND 
        low <= close AND close <= high AND 
        low <= high
    ),
    CONSTRAINT ck_prices_volume_non_negative CHECK (volume >= 0)
);

-- Composite index for efficient queries
CREATE INDEX idx_prices_instrument_timeframe 
ON prices(instrument_id, timeframe, timestamp);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('prices', 'timestamp', chunk_time_interval => INTERVAL '7 days');
```

## Usage Examples

### Creating a Price Record

```python
from datetime import datetime
from decimal import Decimal
from app.models.price import Price

# Create a daily price record
price = Price(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe="1D",
    open=Decimal("150.00"),
    high=Decimal("155.00"),
    low=Decimal("149.00"),
    close=Decimal("154.00"),
    volume=1000000
)

# Validate before saving
if price.is_valid():
    db.add(price)
    db.commit()
```

### Querying Prices

```python
from datetime import datetime, timedelta

# Query prices for a specific instrument and timeframe
prices = db.query(Price).filter(
    Price.instrument_id == 1,
    Price.timeframe == "1D",
    Price.timestamp >= datetime(2024, 1, 1),
    Price.timestamp < datetime(2024, 2, 1)
).order_by(Price.timestamp.desc()).all()

# Query latest price
latest_price = db.query(Price).filter(
    Price.instrument_id == 1,
    Price.timeframe == "1D"
).order_by(Price.timestamp.desc()).first()
```

### Bulk Insert

```python
# Efficient bulk insert for large datasets
prices = []
for i in range(1000):
    price = Price(
        instrument_id=1,
        timestamp=base_date + timedelta(minutes=i),
        timeframe="1m",
        open=Decimal("150.00"),
        high=Decimal("155.00"),
        low=Decimal("149.00"),
        close=Decimal("154.00"),
        volume=10000
    )
    prices.append(price)

db.bulk_save_objects(prices)
db.commit()
```

## Performance Characteristics

### TimescaleDB Hypertable Benefits

1. **Automatic Partitioning**: Data is automatically partitioned into 7-day chunks
2. **Efficient Time-Range Queries**: TimescaleDB optimizes queries with time predicates
3. **Compression**: Older chunks can be compressed to save space
4. **Retention Policies**: Can automatically drop old data
5. **Parallel Query Execution**: Queries can be parallelized across chunks

### Index Optimization

The composite index `(instrument_id, timeframe, timestamp)` is optimized for:
- Filtering by instrument and timeframe
- Ordering by timestamp (most recent first)
- Range queries on timestamp

### Query Performance

Expected performance with proper indexing:
- Single instrument, single timeframe query: < 10ms
- Time range query (1 month): < 50ms
- Bulk insert (1000 records): < 100ms

## Requirements Validated

This implementation validates the following requirements:

- **Requirement 1.2**: Store OHLCV data with timestamp and instrument identifier
- **Requirement 2.3**: Store timeframe identifier with each candle
- **Requirement 18.1**: Use TimescaleDB hypertables for time-series price data
- **Requirement 18.2**: Create indexes on instrument_id and timestamp columns

## Design Properties Supported

The implementation supports the following correctness properties:

- **Property 1**: OHLC Relationship Invariant (enforced by check constraint)
- **Property 5**: Instrument Reference Integrity (enforced by foreign key)

## Running the Migration

To apply the migration:

```bash
# Using Makefile
make db-migrate

# Or directly with alembic
cd backend
alembic upgrade head
```

To verify the migration:

```bash
cd backend
python scripts/verify_prices_table.py
```

## Running Tests

To run the tests:

```bash
# Run all tests
cd backend
pytest tests/test_price_model.py tests/test_price_integration.py -v

# Run specific test
pytest tests/test_price_model.py::TestPriceModel::test_create_valid_price -v

# Run with coverage
pytest tests/test_price_model.py tests/test_price_integration.py --cov=app.models.price -v
```

## Next Steps

With the prices hypertable implemented, the next tasks are:

1. **Task 2.4**: Write property tests for OHLC invariants
2. **Task 2.5**: Create indicators and patterns tables
3. **Task 3.1**: Create candle validation module

## Notes

- The prices table uses NUMERIC(20,6) for price fields to ensure precision
- Volume uses BIGINT to support high-volume instruments
- The composite primary key allows multiple timeframes for the same instrument and timestamp
- Foreign key CASCADE delete ensures data integrity when instruments are deleted
- Check constraints provide database-level validation in addition to application-level validation
