# Indicators and Patterns Tables - Quick Reference

## Overview

This document provides a quick reference for the indicators and patterns tables implemented in Task 2.5.

## Indicators Table

**Purpose**: Store computed technical indicator values as time-series data

**Type**: TimescaleDB Hypertable (partitioned by timestamp, 7-day chunks)

**Primary Key**: (instrument_id, timestamp, timeframe, indicator_name)

### Schema

| Column | Type | Description |
|--------|------|-------------|
| instrument_id | INTEGER | Foreign key to instruments table |
| timestamp | TIMESTAMP | Indicator value timestamp (partition key) |
| timeframe | VARCHAR(10) | Candle frequency ('1D', '5m', '1m') |
| indicator_name | VARCHAR(50) | Indicator name (e.g., 'SMA_20', 'RSI_14') |
| value | NUMERIC(20,6) | Computed indicator value |
| metadata | JSONB | Indicator-specific data (optional) |

### Indexes

- **idx_indicators_lookup**: (instrument_id, timeframe, indicator_name, timestamp)
  - Optimized for queries filtering by instrument, timeframe, and indicator

### Example Usage

```python
# Create SMA indicator
sma = Indicator(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe='1D',
    indicator_name='SMA_20',
    value=Decimal('150.50')
)

# Create Bollinger Bands with metadata
bb = Indicator(
    instrument_id=1,
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    timeframe='1D',
    indicator_name='BB_20',
    value=Decimal('150.00'),
    metadata={
        'upper_band': 155.00,
        'lower_band': 145.00
    }
)

# Query latest RSI
latest_rsi = session.query(Indicator).filter_by(
    instrument_id=1,
    timeframe='1D',
    indicator_name='RSI_14'
).order_by(Indicator.timestamp.desc()).first()
```

### Supported Indicators

| Indicator | Name Format | Metadata Example |
|-----------|-------------|------------------|
| SMA | SMA_20 | `{"period": 20}` |
| EMA | EMA_50 | `{"period": 50}` |
| RSI | RSI_14 | `{"period": 14}` |
| MACD | MACD_12_26_9 | `{"signal_line": 1.5, "histogram": 0.3}` |
| Bollinger Bands | BB_20 | `{"upper_band": 155.0, "lower_band": 145.0}` |
| ATR | ATR_14 | `{"true_range": 2.5}` |
| ALMA | ALMA_20 | `{"window": 20, "offset": 0.85}` |
| Volatility | VOL_20 | `{"window": 20}` |
| VWAP | VWAP | `{"anchor": "day"}` |

## Patterns Table

**Purpose**: Store detected market patterns with confidence scores

**Type**: Regular table with indexes

**Primary Key**: pattern_id (auto-increment)

### Schema

| Column | Type | Description |
|--------|------|-------------|
| pattern_id | SERIAL | Primary key (auto-increment) |
| instrument_id | INTEGER | Foreign key to instruments table |
| timeframe | VARCHAR(10) | Candle frequency ('1D', '5m', '1m') |
| pattern_type | VARCHAR(50) | Pattern type (e.g., 'uptrend', 'breakout') |
| start_timestamp | TIMESTAMP | When pattern started |
| end_timestamp | TIMESTAMP | When pattern ended (NULL if ongoing) |
| confidence | NUMERIC(5,2) | Confidence score (0.00 to 100.00) |
| metadata | JSONB | Pattern-specific data (optional) |
| created_at | TIMESTAMP | When pattern was detected |

### Constraints

- **ck_patterns_confidence_range**: confidence >= 0.00 AND confidence <= 100.00
- **ck_patterns_timestamp_order**: end_timestamp IS NULL OR end_timestamp >= start_timestamp

### Indexes

- **idx_patterns_instrument**: (instrument_id, timeframe, start_timestamp)
  - Optimized for queries by instrument and timeframe
- **idx_patterns_type**: (pattern_type, start_timestamp)
  - Optimized for queries by pattern type

### Example Usage

```python
# Create uptrend pattern (completed)
uptrend = Pattern(
    instrument_id=1,
    timeframe='1D',
    pattern_type='uptrend',
    start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
    end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
    confidence=Decimal('85.50'),
    metadata={'highs': [150.0, 152.0, 155.0]}
)

# Create breakout pattern (ongoing)
breakout = Pattern(
    instrument_id=1,
    timeframe='5m',
    pattern_type='breakout',
    start_timestamp=datetime(2024, 1, 15, 10, 30, 0),
    end_timestamp=None,  # Still ongoing
    confidence=Decimal('78.00')
)

# Validate before saving
if breakout.is_valid():
    session.add(breakout)
    session.commit()

# Query ongoing patterns
ongoing = session.query(Pattern).filter(
    Pattern.end_timestamp.is_(None)
).all()
```

### Supported Pattern Types

| Pattern Type | Description | Metadata Example |
|--------------|-------------|------------------|
| uptrend | Higher-Highs and Higher-Lows | `{"highs": [150, 152, 155], "lows": [148, 150, 153]}` |
| downtrend | Lower-Lows and Lower-Highs | `{"highs": [155, 152, 150], "lows": [153, 150, 148]}` |
| momentum_oversold | RSI < 30 | `{"rsi_value": 25.5}` |
| momentum_neutral | 30 ≤ RSI ≤ 70 | `{"rsi_value": 55.0}` |
| momentum_overbought | RSI > 70 | `{"rsi_value": 78.5}` |
| volatility_compression | Below 20th percentile | `{"volatility": 0.015, "percentile": 12.0}` |
| volatility_expansion | Above 80th percentile | `{"volatility": 0.045, "percentile": 88.0}` |
| breakout | Price breaks above high | `{"breakout_level": 155.0, "volume_ratio": 1.8}` |
| breakdown | Price breaks below low | `{"breakdown_level": 145.0, "volume_ratio": 1.6}` |
| mean_reversion | Deviation from MA | `{"deviation": 2.5, "ma_value": 150.0}` |

## Validation Methods

### Pattern Validation

```python
# Check if confidence is in valid range [0.00, 100.00]
pattern.validate_confidence()  # Returns bool

# Check if end_timestamp >= start_timestamp (or NULL)
pattern.validate_timestamps()  # Returns bool

# Check if pattern is still ongoing
pattern.is_ongoing()  # Returns True if end_timestamp is NULL

# Check all validations
pattern.is_valid()  # Returns True if all validations pass
```

## Database Migration

**Migration File**: `backend/alembic/versions/2024_01_15_1530-003_create_indicators_patterns_tables.py`

**Revision**: 003  
**Revises**: 002 (prices hypertable)

### Running Migration

```bash
# Upgrade to latest
cd backend
alembic upgrade head

# Check current revision
alembic current

# Rollback if needed
alembic downgrade -1
```

## Testing

### Unit Tests

```bash
# Run indicator tests
pytest tests/test_indicator_model.py -v

# Run pattern tests
pytest tests/test_pattern_model.py -v

# Run both with coverage
pytest tests/test_indicator_model.py tests/test_pattern_model.py --cov=app.models
```

### Verification Script

```bash
# Run comprehensive verification
python scripts/verify_indicators_patterns_tables.py
```

Verifies:
- ✓ Table structure
- ✓ Indexes
- ✓ Constraints
- ✓ TimescaleDB hypertable
- ✓ Data operations

## Performance Tips

### Indicators Table

**Efficient Query** (uses idx_indicators_lookup):
```sql
SELECT * FROM indicators 
WHERE instrument_id = 1 
  AND timeframe = '1D' 
  AND indicator_name = 'RSI_14'
  AND timestamp >= '2024-01-01'
ORDER BY timestamp DESC;
```

**Less Efficient** (missing timeframe filter):
```sql
SELECT * FROM indicators 
WHERE instrument_id = 1 
  AND indicator_name = 'RSI_14'
ORDER BY timestamp DESC;
```

### Patterns Table

**Efficient Query** (uses idx_patterns_instrument):
```sql
SELECT * FROM patterns 
WHERE instrument_id = 1 
  AND timeframe = '1D'
ORDER BY start_timestamp DESC;
```

**Efficient Query** (uses idx_patterns_type):
```sql
SELECT * FROM patterns 
WHERE pattern_type = 'uptrend'
ORDER BY start_timestamp DESC;
```

## Related Documentation

- **Full Documentation**: `backend/docs/TASK_2.5_COMPLETE.md`
- **Indicator Model**: `backend/app/models/indicator.py`
- **Pattern Model**: `backend/app/models/pattern.py`
- **Migration**: `backend/alembic/versions/2024_01_15_1530-003_create_indicators_patterns_tables.py`

## Requirements Validated

- ✅ **Requirement 4.7**: Indicator values stored with timestamps and instrument references
- ✅ **Requirement 6.3**: Patterns stored with start/end timestamps, type, and confidence
