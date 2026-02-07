# Instruments Table Implementation

## Overview

The instruments table is the foundation of the Trading Analytics Platform's instrument-agnostic architecture. It stores information about tradeable financial assets including equities, options, and futures.

## Schema Design

### Table Structure

```sql
CREATE TABLE instruments (
    instrument_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    instrument_type VARCHAR(20) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Columns

- **instrument_id**: Auto-incrementing primary key
- **symbol**: Ticker symbol (e.g., 'AAPL', 'SPY', 'ES')
- **instrument_type**: Type of instrument ('equity', 'option', 'future')
- **metadata**: JSONB field for type-specific data (flexible schema)
- **created_at**: Timestamp when the instrument was created
- **updated_at**: Timestamp when the instrument was last updated

### Indexes

1. **uq_instruments_symbol_type** (UNIQUE)
   - Columns: (symbol, instrument_type)
   - Purpose: Ensures unique combination of symbol and type
   - Allows same symbol for different instrument types (e.g., AAPL equity and AAPL options)

2. **idx_instruments_symbol**
   - Column: symbol
   - Purpose: Fast lookups by symbol

3. **idx_instruments_type**
   - Column: instrument_type
   - Purpose: Fast filtering by instrument type

## Metadata Schema

The `metadata` JSONB field stores type-specific information:

### Equity Metadata

```json
{
  "exchange": "NASDAQ",
  "sector": "Technology",
  "industry": "Consumer Electronics"
}
```

### Option Metadata

```json
{
  "underlying": "AAPL",
  "strike": 150.0,
  "expiration": "2024-12-20",
  "option_type": "call"
}
```

**Required fields for options:**
- `underlying`: Symbol of the underlying asset
- `strike`: Strike price
- `expiration`: Expiration date (ISO format)
- `option_type`: "call" or "put"

### Future Metadata

```json
{
  "underlying": "ES",
  "contract_month": "2024-12",
  "multiplier": 50
}
```

**Required fields for futures:**
- `underlying`: Symbol of the underlying asset
- `contract_month`: Contract expiration month (YYYY-MM format)
- `multiplier`: Contract multiplier

## SQLAlchemy Model

The `Instrument` model is defined in `app/models/instrument.py`:

```python
from app.models.instrument import Instrument

# Create an equity
equity = Instrument(
    symbol="AAPL",
    instrument_type="equity",
    metadata={"exchange": "NASDAQ", "sector": "Technology"}
)

# Create an option
option = Instrument(
    symbol="AAPL",
    instrument_type="option",
    metadata={
        "underlying": "AAPL",
        "strike": 150.0,
        "expiration": "2024-12-20",
        "option_type": "call"
    }
)

# Create a future
future = Instrument(
    symbol="ES",
    instrument_type="future",
    metadata={
        "underlying": "ES",
        "contract_month": "2024-12",
        "multiplier": 50
    }
)
```

## Database Migration

The migration is located at:
```
backend/alembic/versions/2024_01_15_1430-001_create_instruments_table.py
```

### Running the Migration

```bash
# Activate virtual environment
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run migration
alembic upgrade head
```

### Verifying the Migration

```bash
# Run verification script
python scripts/verify_migration.py
```

## Querying Examples

### Query by Symbol

```python
from app.models.instrument import Instrument

# Get all instruments with symbol AAPL
instruments = session.query(Instrument).filter(
    Instrument.symbol == "AAPL"
).all()
```

### Query by Instrument Type

```python
# Get all equity instruments
equities = session.query(Instrument).filter(
    Instrument.instrument_type == "equity"
).all()
```

### Query by Metadata Field

```python
# Get all call options
call_options = session.query(Instrument).filter(
    Instrument.instrument_type == "option",
    Instrument.metadata["option_type"].astext == "call"
).all()

# Get options with specific strike price
options_150 = session.query(Instrument).filter(
    Instrument.instrument_type == "option",
    Instrument.metadata["strike"].astext == "150.0"
).all()
```

### Query by Symbol and Type

```python
# Get AAPL equity (unique combination)
aapl_equity = session.query(Instrument).filter(
    Instrument.symbol == "AAPL",
    Instrument.instrument_type == "equity"
).first()
```

## Design Principles

### Instrument Agnosticism

The schema is designed to support any instrument type without schema changes:
- Core fields (symbol, type) are common to all instruments
- Type-specific data goes in JSONB metadata
- No need to create new tables for new instrument types

### Extensibility

Adding a new instrument type (e.g., "crypto", "forex"):
1. No schema changes required
2. Define metadata structure in documentation
3. Add validation logic in application layer
4. Create instruments with new type

### Performance

- Indexes on symbol and instrument_type enable fast lookups
- JSONB allows flexible queries on metadata fields
- Unique constraint prevents duplicate instruments

## Requirements Validated

This implementation validates the following requirements:

- **3.1**: Instruments stored in dedicated table with instrument_type, symbol, and metadata
- **3.2**: Price data references instruments by instrument_id (foreign key support)
- **3.3**: Supports instrument_type values: 'equity', 'option', 'future'
- **3.4**: Option metadata includes strike, expiration, option_type
- **3.5**: Future metadata includes contract_month, underlying

## Testing

Unit tests are located in `backend/tests/test_instrument_model.py`:

```bash
# Run instrument model tests
pytest tests/test_instrument_model.py -v
```

Test coverage includes:
- Creating instruments of all types
- Unique constraint validation
- Metadata storage and retrieval
- Querying by various fields
- JSONB metadata queries
- Timestamp auto-population

## Next Steps

After implementing the instruments table:

1. **Task 2.2**: Write property tests for instrument metadata completeness
2. **Task 2.3**: Create prices hypertable with foreign key to instruments
3. **Task 3.x**: Implement data ingestion service that uses instruments table

## References

- Design Document: `.kiro/specs/trading-analytics-platform/design.md`
- Requirements: `.kiro/specs/trading-analytics-platform/requirements.md`
- Tasks: `.kiro/specs/trading-analytics-platform/tasks.md`
