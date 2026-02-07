"""Unit tests for Price model"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models.instrument import Instrument
from app.models.price import Price


class TestPriceModel:
    """Test suite for Price model"""
    
    def test_create_valid_price(self, db_session):
        """Test creating a valid price record"""
        # Arrange: Create an instrument first
        instrument = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ", "sector": "Technology"}
        )
        db_session.add(instrument)
        db_session.commit()
        
        # Act: Create a valid price record
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
        
        # Assert: Price should be stored correctly
        stored_price = db_session.query(Price).filter_by(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D"
        ).first()
        
        assert stored_price is not None
        assert stored_price.open == Decimal("150.00")
        assert stored_price.high == Decimal("155.00")
        assert stored_price.low == Decimal("149.00")
        assert stored_price.close == Decimal("154.00")
        assert stored_price.volume == 1000000
    
    def test_validate_ohlc_valid(self, db_session):
        """Test OHLC validation with valid data"""
        # Arrange
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
        
        # Act & Assert
        assert price.validate_ohlc() is True
        assert price.is_valid() is True
    
    def test_validate_ohlc_invalid_high_less_than_low(self, db_session):
        """Test OHLC validation fails when high < low"""
        # Arrange
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
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
        
        # Act & Assert
        assert price.validate_ohlc() is False
        assert price.is_valid() is False
    
    def test_validate_ohlc_invalid_open_outside_range(self, db_session):
        """Test OHLC validation fails when open is outside [low, high]"""
        # Arrange
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        price = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("160.00"),  # Invalid: open > high
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000
        )
        
        # Act & Assert
        assert price.validate_ohlc() is False
        assert price.is_valid() is False
    
    def test_validate_ohlc_invalid_close_outside_range(self, db_session):
        """Test OHLC validation fails when close is outside [low, high]"""
        # Arrange
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
            close=Decimal("148.00"),  # Invalid: close < low
            volume=1000000
        )
        
        # Act & Assert
        assert price.validate_ohlc() is False
        assert price.is_valid() is False
    
    def test_validate_volume_valid(self, db_session):
        """Test volume validation with valid non-negative volume"""
        # Arrange
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
        
        # Act & Assert
        assert price.validate_volume() is True
    
    def test_validate_volume_zero(self, db_session):
        """Test volume validation with zero volume (valid)"""
        # Arrange
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
            volume=0
        )
        
        # Act & Assert
        assert price.validate_volume() is True
    
    def test_validate_volume_negative(self, db_session):
        """Test volume validation fails with negative volume"""
        # Arrange
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
            volume=-1000
        )
        
        # Act & Assert
        assert price.validate_volume() is False
        assert price.is_valid() is False
    
    def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraint to instruments table"""
        # Act & Assert: Creating price with non-existent instrument should fail
        price = Price(
            instrument_id=99999,  # Non-existent instrument
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000
        )
        db_session.add(price)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_composite_primary_key(self, db_session):
        """Test composite primary key (instrument_id, timestamp, timeframe)"""
        # Arrange: Create instrument and first price
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        price1 = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000
        )
        db_session.add(price1)
        db_session.commit()
        
        # Act & Assert: Creating duplicate price should fail
        price2 = Price(
            instrument_id=instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe="1D",
            open=Decimal("151.00"),
            high=Decimal("156.00"),
            low=Decimal("150.00"),
            close=Decimal("155.00"),
            volume=2000000
        )
        db_session.add(price2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_multiple_timeframes_same_instrument(self, db_session):
        """Test storing multiple timeframes for same instrument and timestamp"""
        # Arrange: Create instrument
        instrument = Instrument(symbol="AAPL", instrument_type="equity")
        db_session.add(instrument)
        db_session.commit()
        
        timestamp = datetime(2024, 1, 15, 10, 0, 0)
        
        # Act: Create prices for different timeframes
        price_1d = Price(
            instrument_id=instrument.instrument_id,
            timestamp=timestamp,
            timeframe="1D",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000
        )
        
        price_5m = Price(
            instrument_id=instrument.instrument_id,
            timestamp=timestamp,
            timeframe="5m",
            open=Decimal("150.00"),
            high=Decimal("151.00"),
            low=Decimal("149.50"),
            close=Decimal("150.50"),
            volume=50000
        )
        
        price_1m = Price(
            instrument_id=instrument.instrument_id,
            timestamp=timestamp,
            timeframe="1m",
            open=Decimal("150.00"),
            high=Decimal("150.20"),
            low=Decimal("149.90"),
            close=Decimal("150.10"),
            volume=10000
        )
        
        db_session.add_all([price_1d, price_5m, price_1m])
        db_session.commit()
        
        # Assert: All three prices should be stored
        prices = db_session.query(Price).filter_by(
            instrument_id=instrument.instrument_id,
            timestamp=timestamp
        ).all()
        
        assert len(prices) == 3
        timeframes = {p.timeframe for p in prices}
        assert timeframes == {"1D", "5m", "1m"}
    
    def test_instrument_relationship(self, db_session):
        """Test relationship between Price and Instrument"""
        # Arrange: Create instrument and price
        instrument = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ"}
        )
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
        
        # Act: Access instrument through relationship
        stored_price = db_session.query(Price).first()
        
        # Assert: Relationship should work
        assert stored_price.instrument is not None
        assert stored_price.instrument.symbol == "AAPL"
        assert stored_price.instrument.instrument_type == "equity"
    
    def test_repr(self, db_session):
        """Test string representation of Price"""
        # Arrange
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
        
        # Act
        repr_str = repr(price)
        
        # Assert
        assert "Price" in repr_str
        assert str(instrument.instrument_id) in repr_str
        assert "2024-01-15 10:00:00" in repr_str
        assert "1D" in repr_str
        assert "154.00" in repr_str
