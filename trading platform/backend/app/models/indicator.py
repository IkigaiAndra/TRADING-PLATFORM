"""Indicator model for storing computed technical indicator values"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, TIMESTAMP, NUMERIC, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Indicator(Base):
    """
    Indicator model representing computed technical indicator values.
    
    This table is configured as a TimescaleDB hypertable partitioned by timestamp
    for efficient time-series queries. Stores values for various indicators
    (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ALMA, VWAP, etc.) with support
    for indicator-specific metadata.
    
    Attributes:
        instrument_id: Foreign key to instruments table
        timestamp: Indicator value timestamp (partition key for hypertable)
        timeframe: Candle frequency ('1D' for daily, '5m' for 5-minute, '1m' for 1-minute)
        indicator_name: Name of the indicator (e.g., 'SMA_20', 'RSI_14', 'MACD_12_26_9')
        value: Computed indicator value
        metadata: JSONB field for indicator-specific data:
            - Bollinger Bands: {"upper_band": 155.0, "lower_band": 145.0}
            - MACD: {"signal_line": 1.5, "histogram": 0.3}
            - ATR: {"true_range": 2.5}
            
    Constraints:
        - Primary key: (instrument_id, timestamp, timeframe, indicator_name)
    """
    
    __tablename__ = "indicators"
    
    instrument_id = Column(
        Integer, 
        ForeignKey('instruments.instrument_id', ondelete='CASCADE'),
        nullable=False
    )
    timestamp = Column(TIMESTAMP, nullable=False)
    timeframe = Column(String(10), nullable=False)
    indicator_name = Column(String(50), nullable=False)
    value = Column(NUMERIC(20, 6), nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relationship to instrument
    instrument = relationship("Instrument", backref="indicators")
    
    __table_args__ = (
        # Composite primary key
        PrimaryKeyConstraint('instrument_id', 'timestamp', 'timeframe', 'indicator_name'),
        # Composite index for efficient queries on (instrument_id, timeframe, indicator_name, timestamp)
        # This index is optimized for queries filtering by instrument, timeframe, and indicator
        # and ordering by timestamp (most recent first)
        Index('idx_indicators_lookup', 'instrument_id', 'timeframe', 'indicator_name', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Indicator(instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp}, "
            f"timeframe='{self.timeframe}', "
            f"indicator='{self.indicator_name}', "
            f"value={self.value})>"
        )
