"""Instrument model for storing tradeable assets"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class Instrument(Base):
    """
    Instrument model representing tradeable financial assets.
    
    Supports equities, options, and futures with type-specific metadata
    stored in JSONB for flexibility.
    
    Attributes:
        instrument_id: Primary key
        symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
        instrument_type: Type of instrument ('equity', 'option', 'future')
        metadata: JSONB field for type-specific data:
            - Equity: {"exchange": "NASDAQ", "sector": "Technology"}
            - Option: {"underlying": "AAPL", "strike": 150.0, 
                      "expiration": "2024-12-20", "option_type": "call"}
            - Future: {"underlying": "ES", "contract_month": "2024-12", 
                      "multiplier": 50}
        created_at: Timestamp when instrument was created
        updated_at: Timestamp when instrument was last updated
    """
    
    __tablename__ = "instruments"
    
    instrument_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    instrument_type = Column(String(20), nullable=False)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        # Unique constraint on symbol and instrument_type combination
        # This allows same symbol for different instrument types
        # (e.g., AAPL equity and AAPL options)
        Index('uq_instruments_symbol_type', 'symbol', 'instrument_type', unique=True),
        # Index on symbol for fast lookups
        Index('idx_instruments_symbol', 'symbol'),
        # Index on instrument_type for filtering by type
        Index('idx_instruments_type', 'instrument_type'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Instrument(id={self.instrument_id}, "
            f"symbol='{self.symbol}', "
            f"type='{self.instrument_type}')>"
        )
