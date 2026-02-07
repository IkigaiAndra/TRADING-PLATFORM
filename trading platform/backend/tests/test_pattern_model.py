"""Unit tests for Pattern model"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Instrument, Pattern


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_instrument(db_session):
    """Create a sample instrument for testing"""
    instrument = Instrument(
        symbol='AAPL',
        instrument_type='equity',
        metadata={'exchange': 'NASDAQ', 'sector': 'Technology'}
    )
    db_session.add(instrument)
    db_session.commit()
    return instrument


def test_pattern_creation(db_session, sample_instrument):
    """Test creating a pattern record"""
    pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='uptrend',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('85.50'),
        metadata={'highs': [150.0, 152.0, 155.0], 'lows': [148.0, 150.0, 153.0]}
    )
    
    db_session.add(pattern)
    db_session.commit()
    
    # Verify pattern was created
    retrieved = db_session.query(Pattern).filter_by(
        instrument_id=sample_instrument.instrument_id,
        pattern_type='uptrend'
    ).first()
    
    assert retrieved is not None
    assert retrieved.instrument_id == sample_instrument.instrument_id
    assert retrieved.timeframe == '1D'
    assert retrieved.pattern_type == 'uptrend'
    assert retrieved.confidence == Decimal('85.50')
    assert retrieved.start_timestamp == datetime(2024, 1, 10, 0, 0, 0)
    assert retrieved.end_timestamp == datetime(2024, 1, 15, 0, 0, 0)


def test_pattern_ongoing(db_session, sample_instrument):
    """Test creating an ongoing pattern (end_timestamp is NULL)"""
    pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='breakout',
        start_timestamp=datetime(2024, 1, 15, 10, 0, 0),
        end_timestamp=None,
        confidence=Decimal('78.00'),
        metadata={'breakout_level': 155.0, 'volume_ratio': 1.8}
    )
    
    db_session.add(pattern)
    db_session.commit()
    
    # Verify ongoing pattern
    retrieved = db_session.query(Pattern).filter_by(
        pattern_type='breakout'
    ).first()
    
    assert retrieved is not None
    assert retrieved.end_timestamp is None
    assert retrieved.is_ongoing() is True


def test_pattern_completed(db_session, sample_instrument):
    """Test a completed pattern (end_timestamp is not NULL)"""
    pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='downtrend',
        start_timestamp=datetime(2024, 1, 5, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 12, 0, 0, 0),
        confidence=Decimal('72.30')
    )
    
    db_session.add(pattern)
    db_session.commit()
    
    # Verify completed pattern
    retrieved = db_session.query(Pattern).filter_by(
        pattern_type='downtrend'
    ).first()
    
    assert retrieved is not None
    assert retrieved.end_timestamp is not None
    assert retrieved.is_ongoing() is False


def test_pattern_validate_confidence(db_session, sample_instrument):
    """Test confidence validation"""
    # Valid confidence values
    valid_patterns = [
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='test1',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('0.00')
        ),
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='test2',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('50.00')
        ),
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='test3',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('100.00')
        ),
    ]
    
    for pattern in valid_patterns:
        assert pattern.validate_confidence() is True
    
    # Invalid confidence values
    invalid_patterns = [
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='test4',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('-1.00')
        ),
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='test5',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('100.01')
        ),
    ]
    
    for pattern in invalid_patterns:
        assert pattern.validate_confidence() is False


def test_pattern_validate_timestamps(db_session, sample_instrument):
    """Test timestamp validation"""
    # Valid timestamp relationships
    valid_pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='test',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('80.00')
    )
    assert valid_pattern.validate_timestamps() is True
    
    # Valid: end_timestamp is NULL
    ongoing_pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='test',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=None,
        confidence=Decimal('80.00')
    )
    assert ongoing_pattern.validate_timestamps() is True
    
    # Valid: end_timestamp equals start_timestamp
    same_time_pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='test',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        confidence=Decimal('80.00')
    )
    assert same_time_pattern.validate_timestamps() is True
    
    # Invalid: end_timestamp before start_timestamp
    invalid_pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='test',
        start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        confidence=Decimal('80.00')
    )
    assert invalid_pattern.validate_timestamps() is False


def test_pattern_is_valid(db_session, sample_instrument):
    """Test overall pattern validation"""
    # Valid pattern
    valid_pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='uptrend',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('85.00')
    )
    assert valid_pattern.is_valid() is True
    
    # Invalid: bad confidence
    invalid_confidence = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='uptrend',
        start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('150.00')
    )
    assert invalid_confidence.is_valid() is False
    
    # Invalid: bad timestamps
    invalid_timestamps = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='uptrend',
        start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        end_timestamp=datetime(2024, 1, 10, 0, 0, 0),
        confidence=Decimal('85.00')
    )
    assert invalid_timestamps.is_valid() is False


def test_pattern_relationship_to_instrument(db_session, sample_instrument):
    """Test the relationship between Pattern and Instrument"""
    pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='momentum_oversold',
        start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('65.00')
    )
    
    db_session.add(pattern)
    db_session.commit()
    
    # Access instrument through relationship
    retrieved = db_session.query(Pattern).filter_by(
        pattern_type='momentum_oversold'
    ).first()
    
    assert retrieved.instrument is not None
    assert retrieved.instrument.symbol == 'AAPL'
    assert retrieved.instrument.instrument_type == 'equity'


def test_pattern_repr(db_session, sample_instrument):
    """Test the string representation of Pattern"""
    pattern = Pattern(
        instrument_id=sample_instrument.instrument_id,
        timeframe='1D',
        pattern_type='volatility_compression',
        start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
        confidence=Decimal('92.50')
    )
    
    db_session.add(pattern)
    db_session.commit()
    
    repr_str = repr(pattern)
    assert 'Pattern' in repr_str
    assert str(sample_instrument.instrument_id) in repr_str
    assert 'volatility_compression' in repr_str
    assert '92.50' in repr_str


def test_pattern_multiple_types(db_session, sample_instrument):
    """Test storing multiple pattern types for the same instrument"""
    patterns = [
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='uptrend',
            start_timestamp=datetime(2024, 1, 10, 0, 0, 0),
            confidence=Decimal('85.00')
        ),
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='momentum_overbought',
            start_timestamp=datetime(2024, 1, 15, 0, 0, 0),
            confidence=Decimal('72.00')
        ),
        Pattern(
            instrument_id=sample_instrument.instrument_id,
            timeframe='1D',
            pattern_type='volatility_expansion',
            start_timestamp=datetime(2024, 1, 12, 0, 0, 0),
            confidence=Decimal('68.50')
        ),
    ]
    
    for pattern in patterns:
        db_session.add(pattern)
    db_session.commit()
    
    # Verify all patterns were stored
    retrieved = db_session.query(Pattern).filter_by(
        instrument_id=sample_instrument.instrument_id
    ).all()
    
    assert len(retrieved) == 3
    pattern_types = {p.pattern_type for p in retrieved}
    assert pattern_types == {'uptrend', 'momentum_overbought', 'volatility_expansion'}
