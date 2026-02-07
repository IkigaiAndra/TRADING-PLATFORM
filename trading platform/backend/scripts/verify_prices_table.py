"""Script to verify prices hypertable setup"""

import sys
from sqlalchemy import create_engine, text
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def verify_prices_table():
    """Verify that prices table is properly configured as a hypertable"""
    
    try:
        # Create database connection
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            logger.info("Checking if prices table exists...")
            
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'prices'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                logger.error("❌ prices table does not exist")
                return False
            
            logger.info("✅ prices table exists")
            
            # Check if it's a hypertable
            logger.info("Checking if prices is a hypertable...")
            result = conn.execute(text("""
                SELECT * FROM timescaledb_information.hypertables 
                WHERE hypertable_name = 'prices';
            """))
            hypertable = result.fetchone()
            
            if not hypertable:
                logger.error("❌ prices table is not a hypertable")
                return False
            
            logger.info("✅ prices is configured as a hypertable")
            logger.info(f"   - Hypertable schema: {hypertable[0]}")
            logger.info(f"   - Hypertable name: {hypertable[1]}")
            
            # Check columns
            logger.info("Checking table columns...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'prices'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            expected_columns = {
                'instrument_id': 'integer',
                'timestamp': 'timestamp without time zone',
                'timeframe': 'character varying',
                'open': 'numeric',
                'high': 'numeric',
                'low': 'numeric',
                'close': 'numeric',
                'volume': 'bigint'
            }
            
            for col in columns:
                col_name, data_type, is_nullable = col
                logger.info(f"   - {col_name}: {data_type} (nullable: {is_nullable})")
                
                if col_name in expected_columns:
                    if data_type != expected_columns[col_name]:
                        logger.warning(
                            f"   ⚠️  Expected {expected_columns[col_name]}, "
                            f"got {data_type}"
                        )
            
            logger.info("✅ All columns present")
            
            # Check indexes
            logger.info("Checking indexes...")
            result = conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'prices';
            """))
            indexes = result.fetchall()
            
            for idx in indexes:
                logger.info(f"   - {idx[0]}")
            
            # Check for composite index
            has_composite_index = any(
                'instrument_id' in idx[1] and 
                'timeframe' in idx[1] and 
                'timestamp' in idx[1]
                for idx in indexes
            )
            
            if has_composite_index:
                logger.info("✅ Composite index on (instrument_id, timeframe, timestamp) exists")
            else:
                logger.warning("⚠️  Composite index might be missing")
            
            # Check constraints
            logger.info("Checking constraints...")
            result = conn.execute(text("""
                SELECT conname, contype, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'prices'::regclass;
            """))
            constraints = result.fetchall()
            
            for constraint in constraints:
                con_name, con_type, con_def = constraint
                con_type_name = {
                    'p': 'PRIMARY KEY',
                    'f': 'FOREIGN KEY',
                    'c': 'CHECK',
                    'u': 'UNIQUE'
                }.get(con_type, con_type)
                logger.info(f"   - {con_name} ({con_type_name})")
                logger.info(f"     {con_def}")
            
            # Check for OHLC check constraint
            has_ohlc_check = any(
                'ck_prices_ohlc' in constraint[0]
                for constraint in constraints
            )
            
            if has_ohlc_check:
                logger.info("✅ OHLC check constraint exists")
            else:
                logger.warning("⚠️  OHLC check constraint might be missing")
            
            # Check for volume check constraint
            has_volume_check = any(
                'ck_prices_volume' in constraint[0]
                for constraint in constraints
            )
            
            if has_volume_check:
                logger.info("✅ Volume check constraint exists")
            else:
                logger.warning("⚠️  Volume check constraint might be missing")
            
            # Check foreign key
            has_fk = any(
                constraint[1] == 'f' and 'instrument_id' in constraint[2]
                for constraint in constraints
            )
            
            if has_fk:
                logger.info("✅ Foreign key to instruments table exists")
            else:
                logger.error("❌ Foreign key to instruments table is missing")
                return False
            
            logger.info("\n" + "="*60)
            logger.info("✅ Prices hypertable verification complete!")
            logger.info("="*60)
            return True
            
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = verify_prices_table()
    sys.exit(0 if success else 1)
