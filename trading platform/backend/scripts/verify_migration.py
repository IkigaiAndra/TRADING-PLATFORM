"""
Script to verify the instruments table migration.

This script can be used to manually verify the migration structure
without running the full Alembic migration.

Usage:
    python scripts/verify_migration.py
"""

from sqlalchemy import inspect, MetaData
from app.database import engine
from app.models.instrument import Instrument


def verify_instruments_table():
    """Verify the instruments table structure"""
    
    inspector = inspect(engine)
    
    # Check if table exists
    if 'instruments' not in inspector.get_table_names():
        print("❌ Table 'instruments' does not exist")
        return False
    
    print("✅ Table 'instruments' exists")
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('instruments')}
    expected_columns = [
        'instrument_id',
        'symbol',
        'instrument_type',
        'metadata',
        'created_at',
        'updated_at'
    ]
    
    for col_name in expected_columns:
        if col_name in columns:
            print(f"✅ Column '{col_name}' exists - Type: {columns[col_name]['type']}")
        else:
            print(f"❌ Column '{col_name}' is missing")
            return False
    
    # Check indexes
    indexes = inspector.get_indexes('instruments')
    index_names = [idx['name'] for idx in indexes]
    
    expected_indexes = [
        'uq_instruments_symbol_type',
        'idx_instruments_symbol',
        'idx_instruments_type'
    ]
    
    for idx_name in expected_indexes:
        if idx_name in index_names:
            idx_info = next(idx for idx in indexes if idx['name'] == idx_name)
            print(f"✅ Index '{idx_name}' exists - Columns: {idx_info['column_names']}, Unique: {idx_info['unique']}")
        else:
            print(f"❌ Index '{idx_name}' is missing")
            return False
    
    # Check primary key
    pk = inspector.get_pk_constraint('instruments')
    if pk and 'instrument_id' in pk['constrained_columns']:
        print(f"✅ Primary key on 'instrument_id' exists")
    else:
        print(f"❌ Primary key on 'instrument_id' is missing")
        return False
    
    print("\n✅ All checks passed! Instruments table is correctly configured.")
    return True


if __name__ == "__main__":
    print("Verifying instruments table structure...\n")
    try:
        verify_instruments_table()
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
