"""Unit tests for Indicator model"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Instrument, Indicator


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


def test_indicator_creation(db_session, sample_instrument):
    """Test creating an indicator record"""
    indicator = Indicator(
        instrument_id=sample_instrument.instrument_id,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        timeframe='1D',
        indicator_name='SMA_20',
        value=Decimal('150.50'),
        metadata=None
    )
    
    db_session.add(indicator)
    db_session.commit()
    
    # Verify indicator was created
    retrieved = db_session.query(Indicator).filter_by(
        instrument_id=sample_instrument.instrument_id,
        indicator_name='SMA_20'
    ).first()
    
    assert retrieved is not None
    assert retrieved.instrument_id == sample_instrument.instrument_id
    assert retrieved.timeframe == '1D'
    assert retrieved.indicator_name == 'SMA_20'
    assert retrieved.value == Decimal('150.50')
    assert retrieved.metadata is None


def test_indicator_with_metadata(db_session, sample_instrument):
    """Test creating an indicator with metadata (e.g., Bollinger Bands)"""
    indicator = Indicator(
        instrument_id=sample_instrument.instrument_id,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        timeframe='1D',
        indicator_name='BB_20',
        value=Decimal('150.00'),  # Middle band
        metadata={
            'upper_band': 155.00,
            'lower_band': 145.00,
            'std_dev': 2.5
        }
    )
    
    db_session.add(indicator)
    db_session.commit()
    
    # Verify indicator with metadata was created
    retrieved = db_session.query(Indicator).filter_by(
        instrument_id=sample_instrument.instrument_id,
        indicator_name='BB_20'
    ).first()
    
    assert retrieved is not None
    assert retrieved.metadata is not None
    assert retrieved.metadata['upper_band'] == 155.00
    assert retrieved.metadata['lower_band'] == 145.00
    assert retrieved.metadata['std_dev'] == 2.5


def test_indicator_multiple_timeframes(db_session, sample_instrument):
    """Test storing indicators for multiple timeframes"""
    indicators = [
        Indicator(
            instrument_id=sample_instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe='1D',
            indicator_name='RSI_14',
            value=Decimal('65.50')
        ),
        Indicator(
            instrument_id=sample_instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe='5m',
            indicator_name='RSI_14',
            value=Decimal('72.30')
        ),
        Indicator(
            instrument_id=sample_instrument.instrument_id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            timeframe='1m',
            indicator_name='RSI_14',
            value=Decimal('68.90')
        )
    ]
    
    for indicator in indicators:
        db_session.add(indicator)
    db_session.commit()
    
    # Verify all timeframes were stored
    retrieved = db_session.query(Indicator).filter_by(
        instrument_id=sample_instrument.instrument_id,
        indicator_name='RSI_14'
    ).all()
    
    assert len(retrieved) == 3
    timeframes = {ind.timeframe for ind in retrieved}
    assert timeframes == {'1D', '5m', '1m'}


def test_indicator_relationship_to_instrument(db_session, sample_instrument):
    """Test the relationship between Indicator and Instrument"""
    indicator = Indicator(
        instrument_id=sample_instrument.instrument_id,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        timeframe='1D',
        indicator_name='EMA_50',
        value=Decimal('148.75')
    )
    
    db_session.add(indicator)
    db_session.commit()
    
    # Access instrument through relationship
    retrieved = db_session.query(Indicator).filter_by(
        indicator_name='EMA_50'
    ).first()
    
    assert retrieved.instrument is not None
    assert retrieved.instrument.symbol == 'AAPL'
    assert retrieved.instrument.instrument_type == 'equity'


def test_indicator_repr(db_session, sample_instrument):
    """Test the string representation of Indicator"""
    indicator = Indicator(
        instrument_id=sample_instrument.instrument_id,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        timeframe='1D',
        indicator_name='MACD_12_26_9',
        value=Decimal('2.35')
    )
    
    repr_str = repr(indicator)
    assert 'Indicator' in repr_str
    assert str(sample_instrument.instrument_id) in repr_str
    assert '1D' in repr_str
    assert 'MACD_12_26_9' in repr_str
    assert '2.35' in repr_str


def test_indicator_time_series(db_session, sample_instrument):
    """Test storing a time series of indicator values"""
    timestamps = [
        datetime(2024, 1, 15, 10, 0, 0),
        datetime(2024, 1, 15, 11, 0, 0),
        datetime(2024, 1, 15, 12, 0, 0),
    ]
    
    values = [Decimal('150.00'), Decimal('151.50'), Decimal('149.75')]
    
    for ts, val in zip(timestamps, values):
        indicator = Indicator(
            instrument_id=sample_instrument.instrument_id,
            timestamp=ts,
            timeframe='1D',
            indicator_name='SMA_20',
            value=val
        )
        db_session.add(indicator)
    
    db_session.commit()
    
    # Verify time series was stored
    retrieved = db_session.query(Indicator).filter_by(
        instrument_id=sample_instrument.instrument_id,
        indicator_name='SMA_20'
    ).order_by(Indicator.timestamp).all()
    
    assert len(retrieved) == 3
    assert [ind.value for ind in retrieved] == values
    assert [ind.timestamp for ind in retrieved] == timestamps
