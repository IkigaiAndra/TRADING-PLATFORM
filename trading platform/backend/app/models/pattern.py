"""Pattern model for storing detected market patterns"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, TIMESTAMP, NUMERIC, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Pattern(Base):
    """
    Pattern model representing detected market patterns.
    
    Stores identified patterns such as trends (HH-HL, LL-LH), momentum regimes
    (oversold, overbought), volatility states (compression, expansion), breakouts,
    and mean reversion setups.
    
    Attributes:
        pattern_id: Primary key
        instrument_id: Foreign key to instruments table
        timeframe: Candle frequency ('1D' for daily, '5m' for 5-minute, '1m' for 1-minute)
        pattern_type: Type of pattern (e.g., 'uptrend', 'downtrend', 'breakout', 
                     'momentum_oversold', 'volatility_compression')
        start_timestamp: When the pattern started
        end_timestamp: When the pattern ended (NULL if pattern is ongoing)
        confidence: Confidence score (0.00 to 100.00) indicating pattern strength
        metadata: JSONB field for pattern-specific data:
            - Trend: {"highs": [150.0, 152.0, 155.0], "lows": [148.0, 150.0, 153.0]}
            - Breakout: {"breakout_level": 155.0, "volume_ratio": 1.8}
            - Mean Reversion: {"deviation": 2.5, "ma_value": 150.0}
            - Volatility: {"volatility_value": 0.025, "percentile": 15.0}
        created_at: Timestamp when pattern was detected
        
    Constraints:
        - Confidence must be in range [0.00, 100.00]
        - If end_timestamp is not NULL, it must be >= start_timestamp
    """
    
    __tablename__ = "patterns"
    
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(
        Integer, 
        ForeignKey('instruments.instrument_id', ondelete='CASCADE'),
        nullable=False
    )
    timeframe = Column(String(10), nullable=False)
    pattern_type = Column(String(50), nullable=False)
    start_timestamp = Column(TIMESTAMP, nullable=False)
    end_timestamp = Column(TIMESTAMP, nullable=True)
    confidence = Column(NUMERIC(5, 2), nullable=False)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    # Relationship to instrument
    instrument = relationship("Instrument", backref="patterns")
    
    __table_args__ = (
        # Index on (instrument_id, timeframe, start_timestamp) for queries by instrument
        # DESC on start_timestamp for most recent patterns first
        Index('idx_patterns_instrument', 'instrument_id', 'timeframe', 'start_timestamp'),
        # Index on (pattern_type, start_timestamp) for queries by pattern type
        # DESC on start_timestamp for most recent patterns first
        Index('idx_patterns_type', 'pattern_type', 'start_timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Pattern(id={self.pattern_id}, "
            f"instrument_id={self.instrument_id}, "
            f"type='{self.pattern_type}', "
            f"confidence={self.confidence})>"
        )
    
    def is_ongoing(self) -> bool:
        """
        Check if the pattern is still ongoing.
        
        Returns:
            True if end_timestamp is NULL, False otherwise
        """
        return self.end_timestamp is None
    
    def validate_confidence(self) -> bool:
        """
        Validate confidence score is in valid range.
        
        Returns:
            True if confidence is in [0.00, 100.00], False otherwise
        """
        return Decimal('0.00') <= self.confidence <= Decimal('100.00')
    
    def validate_timestamps(self) -> bool:
        """
        Validate timestamp relationships.
        
        Returns:
            True if end_timestamp is NULL or >= start_timestamp, False otherwise
        """
        if self.end_timestamp is None:
            return True
        return self.end_timestamp >= self.start_timestamp
    
    def is_valid(self) -> bool:
        """
        Check if the pattern record is valid.
        
        Returns:
            True if all validations pass, False otherwise
        """
        return self.validate_confidence() and self.validate_timestamps()
