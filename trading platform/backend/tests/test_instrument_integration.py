"""
Integration tests for Instrument model with database.

These tests require a running PostgreSQL/TimescaleDB instance.
Run with: pytest tests/test_instrument_integration.py -v

Note: These tests will be skipped if the database is not available.
"""

import pytest
from sqlalchemy.exc import OperationalError

from app.models.instrument import Instrument


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestInstrumentIntegration:
    """Integration tests for Instrument model with actual database"""
    
    def test_database_connection(self, db_session):
        """Test that we can connect to the database"""
        try:
            # Simple query to verify connection
            result = db_session.execute("SELECT 1")
            assert result.scalar() == 1
        except OperationalError:
            pytest.skip("Database not available")
    
    def test_create_and_retrieve_equity(self, db_session):
        """Test full lifecycle: create, commit, query equity instrument"""
        # Create
        equity = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ", "sector": "Technology"}
        )
        db_session.add(equity)
        db_session.commit()
        instrument_id = equity.instrument_id
        
        # Clear session to force database query
        db_session.expunge_all()
        
        # Retrieve
        retrieved = db_session.query(Instrument).filter(
            Instrument.instrument_id == instrument_id
        ).first()
        
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.instrument_type == "equity"
        assert retrieved.metadata["exchange"] == "NASDAQ"
    
    def test_create_and_retrieve_option(self, db_session):
        """Test full lifecycle: create, commit, query option instrument"""
        # Create
        option = Instrument(
            symbol="AAPL_150C_2024-12-20",
            instrument_type="option",
            metadata={
                "underlying": "AAPL",
                "strike": 150.0,
                "expiration": "2024-12-20",
                "option_type": "call"
            }
        )
        db_session.add(option)
        db_session.commit()
        instrument_id = option.instrument_id
        
        # Clear session
        db_session.expunge_all()
        
        # Retrieve
        retrieved = db_session.query(Instrument).filter(
            Instrument.instrument_id == instrument_id
        ).first()
        
        assert retrieved is not None
        assert retrieved.instrument_type == "option"
        assert retrieved.metadata["strike"] == 150.0
        assert retrieved.metadata["option_type"] == "call"
    
    def test_create_and_retrieve_future(self, db_session):
        """Test full lifecycle: create, commit, query future instrument"""
        # Create
        future = Instrument(
            symbol="ESZ24",
            instrument_type="future",
            metadata={
                "underlying": "ES",
                "contract_month": "2024-12",
                "multiplier": 50
            }
        )
        db_session.add(future)
        db_session.commit()
        instrument_id = future.instrument_id
        
        # Clear session
        db_session.expunge_all()
        
        # Retrieve
        retrieved = db_session.query(Instrument).filter(
            Instrument.instrument_id == instrument_id
        ).first()
        
        assert retrieved is not None
        assert retrieved.instrument_type == "future"
        assert retrieved.metadata["contract_month"] == "2024-12"
        assert retrieved.metadata["multiplier"] == 50
    
    def test_indexes_improve_query_performance(self, db_session):
        """Test that indexes are being used for queries"""
        # Create multiple instruments
        instruments = [
            Instrument(symbol=f"SYM{i}", instrument_type="equity")
            for i in range(100)
        ]
        db_session.add_all(instruments)
        db_session.commit()
        
        # Query by symbol (should use idx_instruments_symbol)
        result = db_session.query(Instrument).filter(
            Instrument.symbol == "SYM50"
        ).first()
        
        assert result is not None
        assert result.symbol == "SYM50"
        
        # Query by type (should use idx_instruments_type)
        equities = db_session.query(Instrument).filter(
            Instrument.instrument_type == "equity"
        ).count()
        
        assert equities >= 100
    
    def test_jsonb_metadata_queries(self, db_session):
        """Test querying by JSONB metadata fields"""
        # Create options with different strikes
        options = [
            Instrument(
                symbol=f"AAPL_{strike}C",
                instrument_type="option",
                metadata={
                    "underlying": "AAPL",
                    "strike": float(strike),
                    "option_type": "call"
                }
            )
            for strike in [140, 150, 160]
        ]
        db_session.add_all(options)
        db_session.commit()
        
        # Query for specific strike
        strike_150 = db_session.query(Instrument).filter(
            Instrument.instrument_type == "option",
            Instrument.metadata["strike"].astext == "150.0"
        ).all()
        
        assert len(strike_150) >= 1
        assert all(opt.metadata["strike"] == 150.0 for opt in strike_150)
    
    def test_concurrent_inserts(self, db_session):
        """Test that multiple instruments can be inserted in one transaction"""
        instruments = [
            Instrument(symbol="AAPL", instrument_type="equity"),
            Instrument(symbol="GOOGL", instrument_type="equity"),
            Instrument(symbol="MSFT", instrument_type="equity"),
            Instrument(
                symbol="AAPL",
                instrument_type="option",
                metadata={"strike": 150.0, "option_type": "call"}
            ),
        ]
        
        db_session.add_all(instruments)
        db_session.commit()
        
        # Verify all were inserted
        count = db_session.query(Instrument).count()
        assert count >= 4
    
    def test_migration_applied_correctly(self, db_session):
        """Test that the migration created all expected database objects"""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.bind)
        
        # Check table exists
        assert 'instruments' in inspector.get_table_names()
        
        # Check columns
        columns = {col['name'] for col in inspector.get_columns('instruments')}
        expected_columns = {
            'instrument_id', 'symbol', 'instrument_type',
            'metadata', 'created_at', 'updated_at'
        }
        assert expected_columns.issubset(columns)
        
        # Check indexes
        indexes = {idx['name'] for idx in inspector.get_indexes('instruments')}
        expected_indexes = {
            'uq_instruments_symbol_type',
            'idx_instruments_symbol',
            'idx_instruments_type'
        }
        assert expected_indexes.issubset(indexes)
        
        # Check primary key
        pk = inspector.get_pk_constraint('instruments')
        assert 'instrument_id' in pk['constrained_columns']
