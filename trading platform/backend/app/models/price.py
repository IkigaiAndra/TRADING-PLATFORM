"""Price model for storing OHLCV time-series data"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, TIMESTAMP, NUMERIC, BIGINT, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class Price(Base):
    """
    Price model representing OHLCV (Open, High, Low, Close, Volume) candle data.
    
    This table is configured as a TimescaleDB hypertable partitioned by timestamp
    for efficient time-series queries. Supports multiple timeframes (1D, 5m, 1m)
    for the same instrument.
    
    Attributes:
        instrument_id: Foreign key to instruments table
        timestamp: Candle timestamp (partition key for hypertable)
        timeframe: Candle frequency ('1D' for daily, '5m' for 5-minute, '1m' for 1-minute)
        open: Opening price
        high: Highest price during period
        low: Lowest price during period
        close: Closing price
        volume: Trading volume
        
    Constraints:
        - Primary key: (instrument_id, timestamp, timeframe)
        - OHLC relationship: Low <= Open <= High AND Low <= Close <= High
        - Volume must be non-negative
    """
    
    __tablename__ = "prices"
    
    instrument_id = Column(
        Integer, 
        ForeignKey('instruments.instrument_id', ondelete='CASCADE'),
        nullable=False
    )
    timestamp = Column(TIMESTAMP, nullable=False)
    timeframe = Column(String(10), nullable=False)
    open = Column(NUMERIC(20, 6), nullable=False)
    high = Column(NUMERIC(20, 6), nullable=False)
    low = Column(NUMERIC(20, 6), nullable=False)
    close = Column(NUMERIC(20, 6), nullable=False)
    volume = Column(BIGINT, nullable=False)
    
    # Relationship to instrument
    instrument = relationship("Instrument", backref="prices")
    
    __table_args__ = (
        # Composite primary key
        PrimaryKeyConstraint('instrument_id', 'timestamp', 'timeframe'),
        # Composite index for efficient queries on (instrument_id, timeframe, timestamp)
        # DESC on timestamp for most recent data first
        Index('idx_prices_instrument_timeframe', 'instrument_id', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Price(instrument_id={self.instrument_id}, "
            f"timestamp={self.timestamp}, "
            f"timeframe='{self.timeframe}', "
            f"close={self.close})>"
        )
    
    def validate_ohlc(self) -> bool:
        """
        Validate OHLC relationships.
        
        Returns:
            True if valid, False otherwise
            
        Validates:
            - Low <= Open <= High
            - Low <= Close <= High
            - Low <= High
        """
        return (
            self.low <= self.open <= self.high and
            self.low <= self.close <= self.high and
            self.low <= self.high
        )
    
    def validate_volume(self) -> bool:
        """
        Validate volume is non-negative.
        
        Returns:
            True if valid, False otherwise
        """
        return self.volume >= 0
    
    def is_valid(self) -> bool:
        """
        Check if the price record is valid.
        
        Returns:
            True if all validations pass, False otherwise
        """
        return self.validate_ohlc() and self.validate_volume()
