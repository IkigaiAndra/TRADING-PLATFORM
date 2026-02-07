"""Unit tests for Instrument model"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.instrument import Instrument


class TestInstrumentModel:
    """Test suite for Instrument model"""
    
    def test_create_equity_instrument(self, db_session):
        """Test creating an equity instrument"""
        # Arrange
        instrument = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ", "sector": "Technology"}
        )
        
        # Act
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        
        # Assert
        assert instrument.instrument_id is not None
        assert instrument.symbol == "AAPL"
        assert instrument.instrument_type == "equity"
        assert instrument.metadata["exchange"] == "NASDAQ"
        assert instrument.metadata["sector"] == "Technology"
        assert instrument.created_at is not None
        assert instrument.updated_at is not None
    
    def test_create_option_instrument(self, db_session):
        """Test creating an option instrument with required metadata"""
        # Arrange
        instrument = Instrument(
            symbol="AAPL",
            instrument_type="option",
            metadata={
                "underlying": "AAPL",
                "strike": 150.0,
                "expiration": "2024-12-20",
                "option_type": "call"
            }
        )
        
        # Act
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        
        # Assert
        assert instrument.instrument_id is not None
        assert instrument.symbol == "AAPL"
        assert instrument.instrument_type == "option"
        assert instrument.metadata["underlying"] == "AAPL"
        assert instrument.metadata["strike"] == 150.0
        assert instrument.metadata["expiration"] == "2024-12-20"
        assert instrument.metadata["option_type"] == "call"
    
    def test_create_future_instrument(self, db_session):
        """Test creating a future instrument with required metadata"""
        # Arrange
        instrument = Instrument(
            symbol="ES",
            instrument_type="future",
            metadata={
                "underlying": "ES",
                "contract_month": "2024-12",
                "multiplier": 50
            }
        )
        
        # Act
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        
        # Assert
        assert instrument.instrument_id is not None
        assert instrument.symbol == "ES"
        assert instrument.instrument_type == "future"
        assert instrument.metadata["underlying"] == "ES"
        assert instrument.metadata["contract_month"] == "2024-12"
        assert instrument.metadata["multiplier"] == 50
    
    def test_instrument_without_metadata(self, db_session):
        """Test creating an instrument without metadata (should be allowed)"""
        # Arrange
        instrument = Instrument(
            symbol="SPY",
            instrument_type="equity",
            metadata=None
        )
        
        # Act
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        
        # Assert
        assert instrument.instrument_id is not None
        assert instrument.metadata is None
    
    def test_unique_constraint_symbol_and_type(self, db_session):
        """Test that symbol + instrument_type combination must be unique"""
        # Arrange
        instrument1 = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ"}
        )
        db_session.add(instrument1)
        db_session.commit()
        
        # Act & Assert - Try to create duplicate
        instrument2 = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NYSE"}
        )
        db_session.add(instrument2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_same_symbol_different_types_allowed(self, db_session):
        """Test that same symbol can exist for different instrument types"""
        # Arrange
        equity = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ"}
        )
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
        
        # Act
        db_session.add(equity)
        db_session.add(option)
        db_session.commit()
        
        # Assert
        db_session.refresh(equity)
        db_session.refresh(option)
        assert equity.instrument_id != option.instrument_id
        assert equity.symbol == option.symbol
        assert equity.instrument_type != option.instrument_type
    
    def test_timestamps_auto_populated(self, db_session):
        """Test that created_at and updated_at are automatically set"""
        # Arrange
        before_create = datetime.utcnow()
        instrument = Instrument(
            symbol="TSLA",
            instrument_type="equity"
        )
        
        # Act
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        after_create = datetime.utcnow()
        
        # Assert
        assert instrument.created_at is not None
        assert instrument.updated_at is not None
        assert before_create <= instrument.created_at <= after_create
        assert before_create <= instrument.updated_at <= after_create
    
    def test_instrument_repr(self, db_session):
        """Test string representation of instrument"""
        # Arrange
        instrument = Instrument(
            symbol="MSFT",
            instrument_type="equity"
        )
        db_session.add(instrument)
        db_session.commit()
        db_session.refresh(instrument)
        
        # Act
        repr_str = repr(instrument)
        
        # Assert
        assert "MSFT" in repr_str
        assert "equity" in repr_str
        assert str(instrument.instrument_id) in repr_str
    
    def test_query_by_symbol(self, db_session):
        """Test querying instruments by symbol"""
        # Arrange
        instruments = [
            Instrument(symbol="AAPL", instrument_type="equity"),
            Instrument(symbol="GOOGL", instrument_type="equity"),
            Instrument(symbol="AAPL", instrument_type="option", 
                      metadata={"strike": 150.0, "option_type": "call"})
        ]
        for inst in instruments:
            db_session.add(inst)
        db_session.commit()
        
        # Act
        aapl_instruments = db_session.query(Instrument).filter(
            Instrument.symbol == "AAPL"
        ).all()
        
        # Assert
        assert len(aapl_instruments) == 2
        assert all(inst.symbol == "AAPL" for inst in aapl_instruments)
    
    def test_query_by_instrument_type(self, db_session):
        """Test querying instruments by type"""
        # Arrange
        instruments = [
            Instrument(symbol="AAPL", instrument_type="equity"),
            Instrument(symbol="GOOGL", instrument_type="equity"),
            Instrument(symbol="AAPL", instrument_type="option",
                      metadata={"strike": 150.0, "option_type": "call"})
        ]
        for inst in instruments:
            db_session.add(inst)
        db_session.commit()
        
        # Act
        equities = db_session.query(Instrument).filter(
            Instrument.instrument_type == "equity"
        ).all()
        
        # Assert
        assert len(equities) == 2
        assert all(inst.instrument_type == "equity" for inst in equities)
    
    def test_jsonb_metadata_query(self, db_session):
        """Test querying instruments by JSONB metadata fields"""
        # Arrange
        instruments = [
            Instrument(
                symbol="AAPL",
                instrument_type="option",
                metadata={"strike": 150.0, "option_type": "call"}
            ),
            Instrument(
                symbol="AAPL",
                instrument_type="option",
                metadata={"strike": 150.0, "option_type": "put"}
            ),
            Instrument(
                symbol="AAPL",
                instrument_type="option",
                metadata={"strike": 160.0, "option_type": "call"}
            )
        ]
        for inst in instruments:
            db_session.add(inst)
        db_session.commit()
        
        # Act - Query for call options
        call_options = db_session.query(Instrument).filter(
            Instrument.metadata["option_type"].astext == "call"
        ).all()
        
        # Assert
        assert len(call_options) == 2
        assert all(
            inst.metadata["option_type"] == "call" 
            for inst in call_options
        )
    
    def test_update_instrument_metadata(self, db_session):
        """Test updating instrument metadata"""
        # Arrange
        instrument = Instrument(
            symbol="AAPL",
            instrument_type="equity",
            metadata={"exchange": "NASDAQ"}
        )
        db_session.add(instrument)
        db_session.commit()
        original_updated_at = instrument.updated_at
        
        # Act - Update metadata
        instrument.metadata = {
            "exchange": "NASDAQ",
            "sector": "Technology"
        }
        db_session.commit()
        db_session.refresh(instrument)
        
        # Assert
        assert instrument.metadata["sector"] == "Technology"
        # Note: updated_at auto-update depends on database trigger or application logic
    
    def test_delete_instrument(self, db_session):
        """Test deleting an instrument"""
        # Arrange
        instrument = Instrument(
            symbol="TEMP",
            instrument_type="equity"
        )
        db_session.add(instrument)
        db_session.commit()
        instrument_id = instrument.instrument_id
        
        # Act
        db_session.delete(instrument)
        db_session.commit()
        
        # Assert
        deleted = db_session.query(Instrument).filter(
            Instrument.instrument_id == instrument_id
        ).first()
        assert deleted is None
