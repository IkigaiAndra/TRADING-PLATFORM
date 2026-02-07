"""
Unit tests for the IngestionService.

Tests cover:
- Provider fallback logic
- Validation integration
- Upsert logic for duplicates
- Exponential backoff for rate limiting
- Error handling and logging
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.ingestion import IngestionService, IngestionResult
from app.services.data_providers import (
    DataProvider, Candle, FetchResult, Timeframe
)
from app.models.price import Price


# Test fixtures

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock(spec=Session)
    db.execute = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def sample_candles():
    """Sample valid candles for testing"""
    return [
        Candle(
            timestamp=datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('154.00'),
            high=Decimal('158.00'),
            low=Decimal('153.00'),
            close=Decimal('157.00'),
            volume=1200000
        ),
        Candle(
            timestamp=datetime(2024, 1, 17, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('157.00'),
            high=Decimal('160.00'),
            low=Decimal('156.00'),
            close=Decimal('159.00'),
            volume=1100000
        )
    ]


@pytest.fixture
def invalid_candles():
    """Sample invalid candles for testing validation"""
    return [
        # Invalid OHLC: High < Low
        Candle(
            timestamp=datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('149.00'),  # Invalid: high < low
            low=Decimal('151.00'),
            close=Decimal('150.00'),
            volume=1000000
        ),
        # Invalid volume: negative
        Candle(
            timestamp=datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=-1000  # Invalid: negative volume
        )
    ]


@pytest.fixture
def mock_provider_success(sample_candles):
    """Mock provider that returns successful results"""
    provider = Mock(spec=DataProvider)
    provider.name = "MockProvider"
    provider.fetch_eod_data = Mock(
        return_value=FetchResult.success_result(sample_candles, "MockProvider")
    )
    provider.fetch_intraday_data = Mock(
        return_value=FetchResult.success_result(sample_candles, "MockProvider")
    )
    return provider


@pytest.fixture
def mock_provider_failure():
    """Mock provider that returns failure results"""
    provider = Mock(spec=DataProvider)
    provider.name = "FailProvider"
    provider.fetch_eod_data = Mock(
        return_value=FetchResult.failure_result("Provider unavailable", "FailProvider")
    )
    provider.fetch_intraday_data = Mock(
        return_value=FetchResult.failure_result("Provider unavailable", "FailProvider")
    )
    return provider


@pytest.fixture
def mock_provider_rate_limited():
    """Mock provider that returns rate limit errors"""
    provider = Mock(spec=DataProvider)
    provider.name = "RateLimitedProvider"
    provider.fetch_eod_data = Mock(
        return_value=FetchResult.failure_result(
            "Rate limit exceeded (429)", "RateLimitedProvider"
        )
    )
    provider.fetch_intraday_data = Mock(
        return_value=FetchResult.failure_result(
            "Too many requests", "RateLimitedProvider"
        )
    )
    return provider


# Test IngestionService initialization

def test_ingestion_service_init_success(mock_provider_success, mock_db):
    """Test successful initialization of IngestionService"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    assert service.providers == [mock_provider_success]
    assert service.db == mock_db
    assert service.max_retries == 3
    assert service.base_delay == 1.0
    assert service.max_delay == 60.0


def test_ingestion_service_init_no_providers(mock_db):
    """Test initialization fails with no providers"""
    with pytest.raises(ValueError, match="At least one data provider must be provided"):
        IngestionService(providers=[], db=mock_db)


def test_ingestion_service_init_custom_params(mock_provider_success, mock_db):
    """Test initialization with custom parameters"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db,
        max_retries=5,
        base_delay=2.0,
        max_delay=120.0
    )
    
    assert service.max_retries == 5
    assert service.base_delay == 2.0
    assert service.max_delay == 120.0


# Test exponential backoff

def test_exponential_backoff_delay(mock_provider_success, mock_db):
    """Test exponential backoff delay calculation"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db,
        base_delay=1.0,
        max_delay=60.0
    )
    
    # Test exponential growth: delay = base_delay * 2^attempt
    assert service._exponential_backoff_delay(0) == 1.0  # 1 * 2^0 = 1
    assert service._exponential_backoff_delay(1) == 2.0  # 1 * 2^1 = 2
    assert service._exponential_backoff_delay(2) == 4.0  # 1 * 2^2 = 4
    assert service._exponential_backoff_delay(3) == 8.0  # 1 * 2^3 = 8
    assert service._exponential_backoff_delay(4) == 16.0  # 1 * 2^4 = 16
    assert service._exponential_backoff_delay(5) == 32.0  # 1 * 2^5 = 32
    assert service._exponential_backoff_delay(6) == 60.0  # 1 * 2^6 = 64, capped at 60


def test_exponential_backoff_max_delay(mock_provider_success, mock_db):
    """Test exponential backoff respects max_delay"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db,
        base_delay=10.0,
        max_delay=30.0
    )
    
    assert service._exponential_backoff_delay(0) == 10.0  # 10 * 2^0 = 10
    assert service._exponential_backoff_delay(1) == 20.0  # 10 * 2^1 = 20
    assert service._exponential_backoff_delay(2) == 30.0  # 10 * 2^2 = 40, capped at 30
    assert service._exponential_backoff_delay(3) == 30.0  # Capped at 30


# Test provider fallback

def test_fetch_with_fallback_primary_success(
    mock_provider_success,
    mock_provider_failure,
    mock_db
):
    """Test fallback uses primary provider when it succeeds"""
    service = IngestionService(
        providers=[mock_provider_success, mock_provider_failure],
        db=mock_db
    )
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data(
            'AAPL',
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
    )
    
    assert result.success
    assert result.provider_name == "MockProvider"
    assert len(result.candles) == 3
    
    # Verify primary provider was called
    mock_provider_success.fetch_eod_data.assert_called_once()
    # Verify secondary provider was NOT called
    mock_provider_failure.fetch_eod_data.assert_not_called()


def test_fetch_with_fallback_secondary_success(
    mock_provider_failure,
    mock_provider_success,
    mock_db
):
    """Test fallback uses secondary provider when primary fails"""
    service = IngestionService(
        providers=[mock_provider_failure, mock_provider_success],
        db=mock_db
    )
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data(
            'AAPL',
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
    )
    
    assert result.success
    assert result.provider_name == "MockProvider"
    assert len(result.candles) == 3
    
    # Verify both providers were called
    mock_provider_failure.fetch_eod_data.assert_called_once()
    mock_provider_success.fetch_eod_data.assert_called_once()


def test_fetch_with_fallback_all_fail(
    mock_provider_failure,
    mock_db
):
    """Test fallback returns failure when all providers fail"""
    provider2 = Mock(spec=DataProvider)
    provider2.name = "FailProvider2"
    provider2.fetch_eod_data = Mock(
        return_value=FetchResult.failure_result("Also unavailable", "FailProvider2")
    )
    
    service = IngestionService(
        providers=[mock_provider_failure, provider2],
        db=mock_db
    )
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data(
            'AAPL',
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
    )
    
    assert not result.success
    assert "All providers failed" in result.error_message
    
    # Verify both providers were called
    mock_provider_failure.fetch_eod_data.assert_called_once()
    provider2.fetch_eod_data.assert_called_once()


@patch('time.sleep')  # Mock sleep to speed up tests
def test_fetch_with_fallback_rate_limit_retry(
    mock_sleep,
    mock_provider_rate_limited,
    mock_db
):
    """Test fallback retries with exponential backoff on rate limiting"""
    service = IngestionService(
        providers=[mock_provider_rate_limited],
        db=mock_db,
        max_retries=3,
        base_delay=1.0
    )
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data(
            'AAPL',
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
    )
    
    assert not result.success
    
    # Verify provider was called max_retries times
    assert mock_provider_rate_limited.fetch_eod_data.call_count == 3
    
    # Verify exponential backoff delays were used
    # First retry: 1.0s, Second retry: 2.0s
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)
    mock_sleep.assert_any_call(2.0)


# Test validation integration

def test_validate_candles_all_valid(mock_provider_success, mock_db, sample_candles):
    """Test validation passes all valid candles"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    valid_candles, error_count = service._validate_candles(sample_candles, '1D')
    
    assert len(valid_candles) == 3
    assert error_count == 0


def test_validate_candles_some_invalid(
    mock_provider_success,
    mock_db,
    sample_candles,
    invalid_candles
):
    """Test validation filters out invalid candles"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    all_candles = sample_candles + invalid_candles
    valid_candles, error_count = service._validate_candles(all_candles, '1D')
    
    assert len(valid_candles) == 3  # Only the valid ones
    assert error_count == 2  # Two invalid candles


def test_validate_candles_all_invalid(mock_provider_success, mock_db, invalid_candles):
    """Test validation rejects all invalid candles"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    valid_candles, error_count = service._validate_candles(invalid_candles, '1D')
    
    assert len(valid_candles) == 0
    assert error_count == 2


# Test upsert logic

def test_upsert_candles_success(mock_provider_success, mock_db, sample_candles):
    """Test successful upsert of candles"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    # Mock successful database execution
    mock_db.execute.return_value = Mock()
    
    inserted, updated = service._upsert_candles(1, sample_candles, '1D')
    
    assert inserted == 3
    assert updated == 0
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


def test_upsert_candles_empty_list(mock_provider_success, mock_db):
    """Test upsert with empty candle list"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    inserted, updated = service._upsert_candles(1, [], '1D')
    
    assert inserted == 0
    assert updated == 0
    mock_db.execute.assert_not_called()


def test_upsert_candles_database_error(mock_provider_success, mock_db, sample_candles):
    """Test upsert handles database errors"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    # Mock database error
    mock_db.execute.side_effect = Exception("Database connection failed")
    
    with pytest.raises(Exception, match="Database connection failed"):
        service._upsert_candles(1, sample_candles, '1D')
    
    mock_db.rollback.assert_called_once()


# Test ingest_eod

def test_ingest_eod_success(mock_provider_success, mock_db):
    """Test successful EOD data ingestion"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    # Mock successful database execution
    mock_db.execute.return_value = Mock()
    
    result = service.ingest_eod(
        instrument_id=1,
        symbol='AAPL',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    assert result.success
    assert result.candles_fetched == 3
    assert result.candles_validated == 3
    assert result.candles_stored == 3
    assert result.validation_errors == 0
    assert result.provider_used == "MockProvider"
    assert result.error_message is None


def test_ingest_eod_fetch_failure(mock_provider_failure, mock_db):
    """Test EOD ingestion handles fetch failures"""
    service = IngestionService(
        providers=[mock_provider_failure],
        db=mock_db
    )
    
    result = service.ingest_eod(
        instrument_id=1,
        symbol='AAPL',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    assert not result.success
    assert result.candles_fetched == 0
    assert "All providers failed" in result.error_message


def test_ingest_eod_validation_failure(mock_db, invalid_candles):
    """Test EOD ingestion handles validation failures"""
    # Create provider that returns invalid candles
    provider = Mock(spec=DataProvider)
    provider.name = "InvalidProvider"
    provider.fetch_eod_data = Mock(
        return_value=FetchResult.success_result(invalid_candles, "InvalidProvider")
    )
    
    service = IngestionService(providers=[provider], db=mock_db)
    
    result = service.ingest_eod(
        instrument_id=1,
        symbol='AAPL',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    assert not result.success
    assert result.candles_fetched == 2
    assert "No valid candles after validation" in result.error_message


# Test ingest_intraday

def test_ingest_intraday_success(mock_provider_success, mock_db):
    """Test successful intraday data ingestion"""
    service = IngestionService(
        providers=[mock_provider_success],
        db=mock_db
    )
    
    # Mock successful database execution
    mock_db.execute.return_value = Mock()
    
    result = service.ingest_intraday(
        instrument_id=1,
        symbol='AAPL',
        timeframe=Timeframe.FIVE_MINUTE,
        start_time=datetime(2024, 1, 15, 9, 30, 0),
        end_time=datetime(2024, 1, 15, 16, 0, 0)
    )
    
    assert result.success
    assert result.candles_fetched == 3
    assert result.candles_validated == 3
    assert result.candles_stored == 3
    assert result.validation_errors == 0
    assert result.provider_used == "MockProvider"


def test_ingest_intraday_fetch_failure(mock_provider_failure, mock_db):
    """Test intraday ingestion handles fetch failures"""
    service = IngestionService(
        providers=[mock_provider_failure],
        db=mock_db
    )
    
    result = service.ingest_intraday(
        instrument_id=1,
        symbol='AAPL',
        timeframe=Timeframe.FIVE_MINUTE,
        start_time=datetime(2024, 1, 15, 9, 30, 0),
        end_time=datetime(2024, 1, 15, 16, 0, 0)
    )
    
    assert not result.success
    assert "All providers failed" in result.error_message


# Test IngestionResult

def test_ingestion_result_success():
    """Test IngestionResult success creation"""
    result = IngestionResult.success_result(
        candles_fetched=10,
        candles_validated=9,
        candles_stored=9,
        candles_updated=2,
        candles_inserted=7,
        validation_errors=1,
        provider_used="TestProvider"
    )
    
    assert result.success
    assert result.candles_fetched == 10
    assert result.candles_validated == 9
    assert result.candles_stored == 9
    assert result.candles_updated == 2
    assert result.candles_inserted == 7
    assert result.validation_errors == 1
    assert result.provider_used == "TestProvider"
    assert result.error_message is None


def test_ingestion_result_failure():
    """Test IngestionResult failure creation"""
    result = IngestionResult.failure_result("Test error message")
    
    assert not result.success
    assert result.error_message == "Test error message"
    assert result.candles_fetched == 0
    assert result.provider_used is None
