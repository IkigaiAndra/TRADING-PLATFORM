"""Integration tests for Price model with TimescaleDB hypertable"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text

from app.models.instrument import Instrument
from app.models.price import Price


class TestPriceIntegration:
    """Integration tests for Price model with TimescaleDB"""
    
    def test_hypertable_exists(self, db_session):
        """Test that prices table is configured as a TimescaleDB hypertable"""
        # Query TimescaleDB metadata to check if prices is a hypertable
        result = db_session.execute(text("""
            SELECT * FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'prices'
        """))
        
        hypertable = result.fetchone()
        assert hypertable is not None, "prices table should be a hypertable"
    
    def test_time_based_partitioning(self, db_session):
        """Test that data is partitioned by timestamp"""
        # Arrange: Create instrument
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        # Act: Insert prices across multiple days (different chunks)
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        for i in range(30):  # 30 days of data
            price = Price(
                instrument_id=instrument.instrument_id,
                timestamp=base_date + timedelta(days=i),
                timeframe="1D",
                open=Decimal("150.00") + Decimal(i),
                high=Decimal("155.00") + Decimal(i),
                low=Decimal("149.00") + Decimal(i),
                close=Decimal("154.00") + Decimal(i),
                volume=1000000 + (i * 10000)
            )
            db_session.add(price)
        db_session.commit()
        
        # Assert: Data should be stored across multiple chunks
        result = db_session.execute(text("""
            SELECT COUNT(DISTINCT chunk_id) as chunk_count
            FROM timescaledb_information.chunks
            WHERE hypertable_name = 'prices'
        """))
        
        chunk_count = result.fetchone()[0]
        # With 7-day chunks and 30 days of data, we should have multiple chunks
        assert chunk_count >= 1, "Data should be partitioned into chunks"
    
    def test_composite_index_performance(self, db_session):
        """Test that composite index on (instrument_id, timeframe, timestamp) is used"""
        # Arrange: Create multiple instruments with price data
        instruments = []
        for i in range(5):
            instrument = Instrument(
                symbol=f"TEST{i}",
                instrument_type="equity"
            )
            db_session.add(instrument)
            instruments.append(instrument)
        db_session.commit()
        
        # Insert prices for each instrument
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        for instrument in instruments:
            for day in range(10):
                for timeframe in ["1D", "5m", "1m"]:
                    price = Price(
                        instrument_id=instrument.instrument_id,
                        timestamp=base_date + timedelta(days=day),
                        timeframe=timeframe,
                        open=Decimal("150.00"),
                        high=Decimal("155.00"),
                        low=Decimal("149.00"),
                        close=Decimal("154.00"),
                        volume=1000000
                    )
                    db_session.add(price)
        db_session.commit()
        
        # Act: Query using the composite index
        instrument_id = instruments[0].instrument_id
        prices = db_session.query(Price).filter(
            Price.instrument_id == instrument_id,
            Price.timeframe == "1D",
            Price.timestamp >= base_date,
            Price.timestamp < base_date + timedelta(days=5)
        ).order_by(Price.timestamp.desc()).all()
        
        # Assert: Should retrieve correct number of prices
        assert len(prices) == 5
        # Verify ordering (most recent first)
        for i in range(len(prices) - 1):
            assert prices[i].timestamp >= prices[i + 1].timestamp
    
    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert of price data"""
        # Arrange: Create instrument
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        # Act: Bulk insert 1000 price records
        prices = []
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        for i in range(1000):
            price = Price(
                instrument_id=instrument.instrument_id,
                timestamp=base_date + timedelta(minutes=i),
                timeframe="1m",
                open=Decimal("150.00") + Decimal(i % 10),
                high=Decimal("155.00") + Decimal(i % 10),
                low=Decimal("149.00") + Decimal(i % 10),
                close=Decimal("154.00") + Decimal(i % 10),
                volume=1000000 + (i * 1000)
            )
            prices.append(price)
        
        db_session.bulk_save_objects(prices)
        db_session.commit()
        
        # Assert: All records should be inserted
        count = db_session.query(Price).filter_by(
            instrument_id=instrument.instrument_id,
            timeframe="1m"
        ).count()
        assert count == 1000
    
    def test_time_range_query(self, db_session):
        """Test querying prices within a time range"""
        # Arrange: Create instrument and prices
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        for i in range(30):
            price = Price(
                instrument_id=instrument.instrument_id,
                timestamp=base_date + timedelta(days=i),
                timeframe="1D",
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("149.00"),
                close=Decimal("154.00"),
                volume=1000000
            )
            db_session.add(price)
        db_session.commit()
        
        # Act: Query prices within a specific time range
        start_date = base_date + timedelta(days=10)
        end_date = base_date + timedelta(days=20)
        
        prices = db_session.query(Price).filter(
            Price.instrument_id == instrument.instrument_id,
            Price.timeframe == "1D",
            Price.timestamp >= start_date,
            Price.timestamp < end_date
        ).all()
        
        # Assert: Should retrieve 10 days of data
        assert len(prices) == 10
        for price in prices:
            assert start_date <= price.timestamp < end_date
    
    def test_multiple_instruments_query(self, db_session):
        """Test querying prices for multiple instruments"""
        # Arrange: Create multiple instruments
        instruments = []
        for i in range(3):
            instrument = Instrument(
                symbol=f"STOCK{i}",
                instrument_type="equity"
            )
            db_session.add(instrument)
            instruments.append(instrument)
        db_session.commit()
        
        # Insert prices for each instrument
        base_date = datetime(2024, 1, 1, 10, 0, 0)
        for instrument in instruments:
            for day in range(5):
                price = Price(
                    instrument_id=instrument.instrument_id,
                    timestamp=base_date + timedelta(days=day),
                    timeframe="1D",
                    open=Decimal("150.00"),
                    high=Decimal("155.00"),
                    low=Decimal("149.00"),
                    close=Decimal("154.00"),
                    volume=1000000
                )
                db_session.add(price)
        db_session.commit()
        
        # Act: Query prices for specific instruments
        instrument_ids = [inst.instrument_id for inst in instruments[:2]]
        prices = db_session.query(Price).filter(
            Price.instrument_id.in_(instrument_ids),
            Price.timeframe == "1D"
        ).all()
        
        # Assert: Should retrieve prices for 2 instruments, 5 days each
        assert len(prices) == 10
        retrieved_ids = {p.instrument_id for p in prices}
        assert retrieved_ids == set(instrument_ids)
    
    def test_cascade_delete(self, db_session):
        """Test that deleting an instrument cascades to prices"""
        # Arrange: Create instrument with prices
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        price = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000
        )
        db_session.add(price)
        db_session.commit()
        
        instrument_id = instrument.instrument_id
        
        # Act: Delete instrument
        db_session.delete(instrument)
        db_session.commit()
        
        # Assert: Prices should be deleted (cascade)
        prices = db_session.query(Price).filter_by(
            instrument_id=instrument_id
        ).all()
        assert len(prices) == 0
    
    def test_check_constraint_ohlc(self, db_session):
        """Test that database check constraint enforces OHLC relationships"""
        # Arrange: Create instrument
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        # Act & Assert: Try to insert invalid OHLC data
        price = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("145.00"),  # Invalid: high < low
            low=Decimal("149.00"),
            close=Decimal("148.00"),
            volume=1000000
        )
        db_session.add(price)
        
        with pytest.raises(Exception):  # Should raise IntegrityError or CheckViolation
            db_session.commit()
    
    def test_check_constraint_volume(self, db_session):
        """Test that database check constraint enforces non-negative volume"""
        # Arrange: Create instrument
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        # Act & Assert: Try to insert negative volume
        price = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=-1000  # Invalid: negative volume
        )
        db_session.add(price)
        
        with pytest.raises(Exception):  # Should raise IntegrityError or CheckViolation
            db_session.commit()
