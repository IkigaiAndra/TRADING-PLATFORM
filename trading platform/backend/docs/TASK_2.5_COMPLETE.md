# Task 2.5: Create Indicators and Patterns Tables - COMPLETE ✅

## Overview

This task implements the database schema and SQLAlchemy models for storing technical indicators and detected market patterns. The indicators table is configured as a TimescaleDB hypertable for efficient time-series queries, while the patterns table stores detected patterns with timestamps and confidence scores.

## Requirements Validated

- **Requirement 4.7**: THE Indicator_Layer SHALL store computed indicator values with timestamps and instrument references
- **Requirement 6.3**: WHEN a trend pattern is identified, THE System SHALL store the pattern with start timestamp, end timestamp, pattern type, and confidence score

## Implementation Details

### 1. Indicator Model (`backend/app/models/indicator.py`)

The `Indicator` model stores computed technical indicator values as time-series data.

**Key Features:**
- **TimescaleDB Hypertable**: Partitioned by timestamp for efficient time-series queries
- **Flexible Metadata**: JSONB field for indicator-specific data (e.g., Bollinger Bands upper/lower, MACD signal line)
- **Multi-timeframe Support**: Stores indicators for different timeframes (1D, 5m, 1m)
- **Composite Primary Key**: (instrument_id, timestamp, timeframe, indicator_name)

**Schema:**
```sql
CREATE TABLE indicators (
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value NUMERIC(20, 6) NOT NULL,
    metadata JSONB,
    PRIMARY KEY (instrument_id, timestamp, timeframe, indicator_name)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('indicators', 'timestamp', chunk_time_interval => INTERVAL '7 days');

-- Create composite index for efficient queries
CREATE INDEX idx_indicators_lookup ON indicators(instrument_id, timeframe, indicator_name, timestamp);
```

**Supported Indicators:**
- SMA (Simple Moving Average): `{"period": 20}`
- EMA (Exponential Moving Average): `{"period": 50, "smoothing_factor": 0.04}`
- RSI (Relative Strength Index): `{"period": 14}`
- MACD: `{"signal_line": 1.5, "histogram": 0.3}`
- Bollinger Bands: `{"upper_band": 155.0, "lower_band": 145.0, "std_dev": 2.5}`
- ATR (Average True Range): `{"true_range": 2.5}`
- ALMA (Arnaud Legoux MA): `{"window": 20, "offset": 0.85, "sigma": 6}`
- Rolling Volatility: `{"window": 20}`
- VWAP: `{"anchor": "day"}`

### 2. Pattern Model (`backend/app/models/pattern.py`)

The `Pattern` model stores detected market patterns with confidence scores and metadata.

**Key Features:**
- **Ongoing Patterns**: `end_timestamp` is NULL for patterns still in progress
- **Confidence Scores**: Range [0.00, 100.00] indicating pattern strength
- **Pattern-specific Metadata**: JSONB field for pattern details
- **Validation Methods**: Built-in validation for confidence and timestamps

**Schema:**
```sql
CREATE TABLE patterns (
    pattern_id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    timeframe VARCHAR(10) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP,
    confidence NUMERIC(5, 2) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_patterns_confidence_range CHECK (confidence >= 0.00 AND confidence <= 100.00),
    CONSTRAINT ck_patterns_timestamp_order CHECK (end_timestamp IS NULL OR end_timestamp >= start_timestamp)
);

-- Create indexes for efficient queries
CREATE INDEX idx_patterns_instrument ON patterns(instrument_id, timeframe, start_timestamp);
CREATE INDEX idx_patterns_type ON patterns(pattern_type, start_timestamp);
```

**Supported Pattern Types:**
- **Trend Patterns**: `uptrend`, `downtrend`
  - Metadata: `{"highs": [150.0, 152.0, 155.0], "lows": [148.0, 150.0, 153.0]}`
- **Momentum Regimes**: `momentum_oversold`, `momentum_neutral`, `momentum_overbought`
  - Metadata: `{"rsi_value": 25.5}`
- **Volatility States**: `volatility_compression`, `volatility_expansion`
  - Metadata: `{"volatility_value": 0.025, "percentile": 15.0}`
- **Breakout Patterns**: `breakout`, `breakdown`
  - Metadata: `{"breakout_level": 155.0, "volume_ratio": 1.8}`
- **Mean Reversion**: `mean_reversion`
  - Metadata: `{"deviation": 2.5, "ma_value": 150.0}`

**Validation Methods:**
```python
pattern.validate_confidence()  # Returns True if confidence in [0.00, 100.00]
pattern.validate_timestamps()  # Returns True if end_timestamp >= start_timestamp or NULL
pattern.is_ongoing()           # Returns True if end_timestamp is NULL
pattern.is_valid()             # Returns True if all validations pass
```

### 3. Database Migration (`backend/alembic/versions/2024_01_15_1530-003_create_indicators_patterns_tables.py`)

**Migration Details:**
- **Revision**: 003
- **Revises**: 002 (prices hypertable)
- **Creates**: indicators and patterns tables with all indexes and constraints

**Key Operations:**
1. Create indicators table with composite primary key
2. Convert indicators to TimescaleDB hypertable (7-day chunks)
3. Create idx_indicators_lookup index
4. Create patterns table with auto-incrementing primary key
5. Create idx_patterns_instrument and idx_patterns_type indexes
6. Add check constraints for confidence range and timestamp ordering

**Running the Migration:**
```bash
# Upgrade to latest
cd backend
alembic upgrade head

# Verify migration
alembic current

# Rollback if needed
alembic downgrade -1
```

### 4. Model Exports (`backend/app/models/__init__.py`)

Updated to export the new models:
```python
from app.models.indicator import Indicator
from app.models.pattern import Pattern

__all__ = ["Base", "Instrument", "Price", "Indicator", "Pattern"]
```

## Testing

### Unit Tests

**Indicator Model Tests** (`backend/tests/test_indicator_model.py`):
- ✓ Basic indicator creation
- ✓ Indicator with metadata (Bollinger Bands, MACD)
- ✓ Multiple timeframes for same indicator
- ✓ Relationship to instrument
- ✓ Time series storage
- ✓ String representation

**Pattern Model Tests** (`backend/tests/test_pattern_model.py`):
- ✓ Basic pattern creation
- ✓ Ongoing patterns (end_timestamp = NULL)
- ✓ Completed patterns
- ✓ Confidence validation (0.00 to 100.00)
- ✓ Timestamp validation (end >= start)
- ✓ Overall validation (is_valid method)
- ✓ Relationship to instrument
- ✓ Multiple pattern types
- ✓ String representation

**Running Tests:**
```bash
# Run all tests
cd backend
pytest tests/test_indicator_model.py tests/test_pattern_model.py -v

# Run with coverage
pytest tests/test_indicator_model.py tests/test_pattern_model.py --cov=app.models --cov-report=html
```

### Integration Verification

**Verification Script** (`backend/scripts/verify_indicators_patterns_tables.py`):

Comprehensive verification that checks:
1. ✓ Table structure (all columns present)
2. ✓ Indexes created correctly
3. ✓ Constraints enforced
4. ✓ TimescaleDB hypertable for indicators
5. ✓ Data operations (insert, query, validate)

**Running Verification:**
```bash
cd backend
python scripts/verify_indicators_patterns_tables.py
```

**Expected Output:**
```
============================================================
INDICATORS AND PATTERNS TABLES VERIFICATION
Task 2.5: Create indicators and patterns tables
============================================================

✓ Connected to database

============================================================
VERIFYING TABLE STRUCTURE
============================================================
✓ All columns present in indicators table
✓ All columns present in patterns table
✅ Table structure verification passed

============================================================
VERIFYING INDEXES
============================================================
✓ idx_indicators_lookup exists
✓ idx_patterns_instrument exists
✓ idx_patterns_type exists
✅ Index verification passed

============================================================
VERIFYING CONSTRAINTS
============================================================
✓ ck_patterns_confidence_range exists
✓ ck_patterns_timestamp_order exists
✅ Constraint verification passed

============================================================
VERIFYING TIMESCALEDB HYPERTABLE
============================================================
✓ indicators table is a TimescaleDB hypertable
✅ Hypertable verification passed

============================================================
VERIFYING DATA OPERATIONS
============================================================
✓ Test data inserted and queried successfully
✓ Pattern validation methods work correctly
✅ Data operations verification passed

============================================================
🎉 ALL VERIFICATIONS PASSED!
============================================================
```

## Usage Examples

### Creating Indicators

```python
from datetime import datetime
from decimal import Decimal
from app.models import Indicator

# Simple indicator (SMA)
sma = Indicator(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe='1D',
    indicator_name='SMA_20',
    value=Decimal('150.50')
)

# Indicator with metadata (Bollinger Bands)
bb = Indicator(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe='1D',
    indicator_name='BB_20',
    value=Decimal('150.00'),  # Middle band
    metadata={
        'upper_band': 155.00,
        'lower_band': 145.00,
        'std_dev': 2.5
    }
)

# MACD with signal line
macd = Indicator(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe='1D',
    indicator_name='MACD_12_26_9',
    value=Decimal('2.35'),
    metadata={
        'signal_line': 1.85,
        'histogram': 0.50
    }
)
```

### Creating Patterns

```python
from datetime import datetime
from decimal import Decimal
from app.models import Pattern

# Uptrend pattern (completed)
uptrend = Pattern(
    instrument_id=1,
    timeframe='1D',
    pattern_type='uptrend',
    start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
    end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
    confidence=Decimal('85.50'),
    metadata={
        'highs': [150.0, 152.0, 155.0],
        'lows': [148.0, 150.0, 153.0]
    }
)

# Breakout pattern (ongoing)
breakout = Pattern(
    instrument_id=1,
    timeframe='5m',
    pattern_type='breakout',
    start_timestamp=datetime(2024, 1, 15, 10, 30, 0),
    end_timestamp=None,  # Still ongoing
    confidence=Decimal('78.00'),
    metadata={
        'breakout_level': 155.0,
        'volume_ratio': 1.8
    }
)

# Validate before saving
if breakout.is_valid():
    session.add(breakout)
    session.commit()
```

### Querying Indicators

```python
from app.models import Indicator

# Get all SMA values for an instrument
sma_values = session.query(Indicator).filter_by(
    instrument_id=1,
    timeframe='1D',
    indicator_name='SMA_20'
).order_by(Indicator.timestamp.desc()).all()

# Get latest indicator value
latest_rsi = session.query(Indicator).filter_by(
    instrument_id=1,
    timeframe='1D',
    indicator_name='RSI_14'
).order_by(Indicator.timestamp.desc()).first()

# Get indicators for a time range
from datetime import datetime
indicators = session.query(Indicator).filter(
    Indicator.instrument_id == 1,
    Indicator.timeframe == '1D',
    Indicator.timestamp >= datetime(2024, 1, 1),
    Indicator.timestamp <= datetime(2024, 1, 31)
).all()
```

### Querying Patterns

```python
from app.models import Pattern

# Get all ongoing patterns
ongoing = session.query(Pattern).filter(
    Pattern.end_timestamp.is_(None)
).all()

# Get patterns by type
uptrends = session.query(Pattern).filter_by(
    pattern_type='uptrend'
).order_by(Pattern.start_timestamp.desc()).all()

# Get high-confidence patterns
high_confidence = session.query(Pattern).filter(
    Pattern.confidence >= 80.0
).all()

# Get patterns for an instrument
instrument_patterns = session.query(Pattern).filter_by(
    instrument_id=1,
    timeframe='1D'
).order_by(Pattern.start_timestamp.desc()).all()
```

## Performance Considerations

### Indicators Table (Hypertable)

**Partitioning Strategy:**
- Partitioned by timestamp with 7-day chunks
- Efficient for time-range queries
- Automatic data retention policies can be added

**Index Usage:**
- `idx_indicators_lookup` optimized for queries filtering by:
  - instrument_id + timeframe + indicator_name + timestamp
- Use this index for typical queries: "Get RSI values for AAPL in 1D timeframe"

**Query Optimization:**
```sql
-- Efficient: Uses idx_indicators_lookup
SELECT * FROM indicators 
WHERE instrument_id = 1 
  AND timeframe = '1D' 
  AND indicator_name = 'RSI_14'
  AND timestamp >= '2024-01-01'
ORDER BY timestamp DESC;

-- Less efficient: Missing timeframe filter
SELECT * FROM indicators 
WHERE instrument_id = 1 
  AND indicator_name = 'RSI_14'
ORDER BY timestamp DESC;
```

### Patterns Table

**Index Usage:**
- `idx_patterns_instrument`: Queries by instrument and timeframe
- `idx_patterns_type`: Queries by pattern type

**Query Optimization:**
```sql
-- Efficient: Uses idx_patterns_instrument
SELECT * FROM patterns 
WHERE instrument_id = 1 
  AND timeframe = '1D'
ORDER BY start_timestamp DESC;

-- Efficient: Uses idx_patterns_type
SELECT * FROM patterns 
WHERE pattern_type = 'uptrend'
ORDER BY start_timestamp DESC;
```

## Next Steps

With indicators and patterns tables implemented, the following tasks can now proceed:

1. **Task 5.x**: Implement indicator computation (SMA, EMA, RSI, MACD, etc.)
   - Use the Indicator model to store computed values
   - Leverage TimescaleDB hypertable for efficient storage

2. **Task 7.x**: Implement pattern detection (trends, momentum, volatility)
   - Use the Pattern model to store detected patterns
   - Implement confidence scoring algorithms

3. **Task 9.x**: Integrate pattern detection into Analytics Engine
   - Query indicators from the indicators table
   - Store detected patterns in the patterns table

4. **Task 20.x**: Implement signal generation
   - Query patterns and indicators to generate trading signals
   - Use pattern confidence scores in signal logic

## Files Created/Modified

### Created:
- `backend/app/models/indicator.py` - Indicator model
- `backend/app/models/pattern.py` - Pattern model
- `backend/alembic/versions/2024_01_15_1530-003_create_indicators_patterns_tables.py` - Migration
- `backend/tests/test_indicator_model.py` - Indicator unit tests
- `backend/tests/test_pattern_model.py` - Pattern unit tests
- `backend/scripts/verify_indicators_patterns_tables.py` - Verification script
- `backend/docs/TASK_2.5_COMPLETE.md` - This documentation

### Modified:
- `backend/app/models/__init__.py` - Added Indicator and Pattern exports

## Conclusion

Task 2.5 is complete! The indicators and patterns tables are now implemented with:

✅ **Indicator Model**: TimescaleDB hypertable for efficient time-series storage  
✅ **Pattern Model**: Flexible schema with confidence scores and metadata  
✅ **Database Migration**: Creates tables, indexes, and constraints  
✅ **Unit Tests**: Comprehensive test coverage for both models  
✅ **Verification Script**: Validates implementation correctness  
✅ **Documentation**: Complete usage examples and performance guidelines  

The foundation is now in place for implementing the Analytics Engine that will compute indicators and detect patterns from price data.
