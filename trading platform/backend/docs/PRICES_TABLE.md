# Prices Table - TimescaleDB Hypertable

## Overview

The `prices` table stores OHLCV (Open, High, Low, Close, Volume) time-series data for all instruments. It is implemented as a TimescaleDB hypertable for optimal time-series query performance.

## Schema

```sql
CREATE TABLE prices (
    instrument_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 6) NOT NULL,
    high NUMERIC(20, 6) NOT NULL,
    low NUMERIC(20, 6) NOT NULL,
    close NUMERIC(20, 6) NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (instrument_id, timestamp, timeframe),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id) ON DELETE CASCADE
);
```

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `instrument_id` | INTEGER | Foreign key to instruments table |
| `timestamp` | TIMESTAMP | Candle timestamp (partition key) |
| `timeframe` | VARCHAR(10) | Candle frequency ('1D', '5m', '1m') |
| `open` | NUMERIC(20,6) | Opening price |
| `high` | NUMERIC(20,6) | Highest price during period |
| `low` | NUMERIC(20,6) | Lowest price during period |
| `close` | NUMERIC(20,6) | Closing price |
| `volume` | BIGINT | Trading volume |

## Constraints

### Primary Key
- Composite: `(instrument_id, timestamp, timeframe)`
- Allows multiple timeframes for the same instrument and timestamp

### Foreign Key
- `instrument_id` references `instruments(instrument_id)`
- `ON DELETE CASCADE`: Deleting an instrument deletes all its prices

### Check Constraints

#### OHLC Relationships
```sql
CHECK (
    low <= open AND open <= high AND 
    low <= close AND close <= high AND 
    low <= high
)
```

Ensures valid OHLC relationships:
- Low ≤ Open ≤ High
- Low ≤ Close ≤ High
- Low ≤ High

#### Non-Negative Volume
```sql
CHECK (volume >= 0)
```

Ensures volume is never negative.

## Indexes

### Composite Index
```sql
CREATE INDEX idx_prices_instrument_timeframe 
ON prices(instrument_id, timeframe, timestamp);
```

Optimized for queries that:
- Filter by instrument_id and timeframe
- Order by timestamp (most recent first)
- Use time range predicates

## TimescaleDB Hypertable

The prices table is configured as a TimescaleDB hypertable:

```sql
SELECT create_hypertable(
    'prices',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days'
);
```

### Benefits

1. **Automatic Partitioning**: Data is partitioned into 7-day chunks
2. **Query Optimization**: Time-based queries are automatically optimized
3. **Compression**: Older chunks can be compressed to save space
4. **Retention Policies**: Can automatically drop old data
5. **Parallel Queries**: Queries can be parallelized across chunks

### Chunk Management

- **Chunk Interval**: 7 days
- **Partition Key**: `timestamp`
- **Automatic**: Chunks are created automatically as data is inserted

## Supported Timeframes

| Timeframe | Description | Typical Use Case |
|-----------|-------------|------------------|
| `1D` | Daily (End-of-Day) | Long-term analysis, backtesting |
| `5m` | 5-minute intraday | Day trading, short-term patterns |
| `1m` | 1-minute intraday | Scalping, high-frequency analysis |

Additional timeframes can be added as needed (e.g., '1h', '15m', '4h').

## Usage Examples

### Insert Single Price

```python
from datetime import datetime
from decimal import Decimal
from app.models.price import Price

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

db.add(price)
db.commit()
```

### Bulk Insert

```python
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

### Query Latest Price

```python
latest_price = db.query(Price).filter(
    Price.instrument_id == 1,
    Price.timeframe == "1D"
).order_by(Price.timestamp.desc()).first()
```

### Query Time Range

```python
from datetime import datetime, timedelta

start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 2, 1)

prices = db.query(Price).filter(
    Price.instrument_id == 1,
    Price.timeframe == "1D",
    Price.timestamp >= start_date,
    Price.timestamp < end_date
).order_by(Price.timestamp.asc()).all()
```

### Query Multiple Instruments

```python
instrument_ids = [1, 2, 3]

prices = db.query(Price).filter(
    Price.instrument_id.in_(instrument_ids),
    Price.timeframe == "1D",
    Price.timestamp >= start_date
).order_by(
    Price.instrument_id,
    Price.timestamp.desc()
).all()
```

## Validation

The Price model includes validation methods:

```python
# Validate OHLC relationships
if price.validate_ohlc():
    print("OHLC is valid")

# Validate volume
if price.validate_volume():
    print("Volume is valid")

# Comprehensive validation
if price.is_valid():
    db.add(price)
    db.commit()
```

## Performance Considerations

### Query Optimization

1. **Always filter by instrument_id and timeframe** when possible
2. **Use time range predicates** to leverage hypertable partitioning
3. **Order by timestamp DESC** for most recent data first
4. **Use bulk inserts** for large datasets

### Index Usage

The composite index is used when queries:
- Filter by `instrument_id`
- Filter by `instrument_id` and `timeframe`
- Filter by `instrument_id`, `timeframe`, and `timestamp`

### Avoid

- Full table scans without time predicates
- Queries without instrument_id filter
- Individual inserts in loops (use bulk_save_objects)

## Maintenance

### Compression

Compress older chunks to save space:

```sql
-- Compress chunks older than 30 days
SELECT compress_chunk(i)
FROM show_chunks('prices', older_than => INTERVAL '30 days') i;
```

### Retention Policy

Automatically drop old data:

```sql
-- Drop chunks older than 2 years
SELECT add_retention_policy('prices', INTERVAL '2 years');
```

### Reindex

Reindex if query performance degrades:

```sql
REINDEX TABLE prices;
```

## Monitoring

### Check Hypertable Stats

```sql
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'prices';
```

### Check Chunks

```sql
SELECT * FROM timescaledb_information.chunks 
WHERE hypertable_name = 'prices'
ORDER BY range_start DESC;
```

### Check Table Size

```sql
SELECT 
    hypertable_size('prices') as total_size,
    pg_size_pretty(hypertable_size('prices')) as pretty_size;
```

## Related Tables

- **instruments**: Parent table containing instrument metadata
- **indicators**: Computed technical indicators derived from prices
- **patterns**: Detected patterns in price data

## Migration

The prices table is created by migration `002_create_prices_hypertable.py`.

To apply:
```bash
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```

## Testing

Tests are located in:
- `tests/test_price_model.py`: Unit tests for Price model
- `tests/test_price_integration.py`: Integration tests with TimescaleDB

Run tests:
```bash
pytest tests/test_price_model.py tests/test_price_integration.py -v
```
