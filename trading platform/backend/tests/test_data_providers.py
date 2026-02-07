"""
Unit tests for data provider implementations.

Tests the DataProvider protocol and YahooFinanceProvider implementation,
including successful data fetching, error handling, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.services.data_providers import (
    DataProvider,
    YahooFinanceProvider,
    Candle,
    FetchResult,
    Timeframe
)


class TestCandle:
    """Tests for Candle data class"""
    
    def test_candle_creation(self):
        """Test creating a candle with valid data"""
        timestamp = datetime(2024, 1, 15, 10, 0, 0)
        candle = Candle(
            timestamp=timestamp,
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        assert candle.timestamp == timestamp
        assert candle.open == Decimal('150.00')
        assert candle.high == Decimal('155.00')
        assert candle.low == Decimal('149.00')
        assert candle.close == Decimal('154.00')
        assert candle.volume == 1000000
    
    def test_candle_to_dict(self):
        """Test converting candle to dictionary"""
        timestamp = datetime(2024, 1, 15, 10, 0, 0)
        candle = Candle(
            timestamp=timestamp,
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        candle_dict = candle.to_dict()
        
        assert candle_dict['timestamp'] == timestamp
        assert candle_dict['open'] == Decimal('150.00')
        assert candle_dict['high'] == Decimal('155.00')
        assert candle_dict['low'] == Decimal('149.00')
        assert candle_dict['close'] == Decimal('154.00')
        assert candle_dict['volume'] == 1000000


class TestFetchResult:
    """Tests for FetchResult data class"""
    
    def test_success_result(self):
        """Test creating a successful fetch result"""
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 15),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            )
        ]
        
        result = FetchResult.success_result(candles, "TestProvider")
        
        assert result.success is True
        assert len(result.candles) == 1
        assert result.error_message is None
        assert result.provider_name == "TestProvider"
    
    def test_failure_result(self):
        """Test creating a failed fetch result"""
        result = FetchResult.failure_result("Network error", "TestProvider")
        
        assert result.success is False
        assert len(result.candles) == 0
        assert result.error_message == "Network error"
        assert result.provider_name == "TestProvider"


class TestYahooFinanceProvider:
    """Tests for Yahoo Finance provider implementation"""
    
    @pytest.fixture
    def provider(self):
        """Create a Yahoo Finance provider instance"""
        return YahooFinanceProvider()
    
    @pytest.fixture
    def mock_eod_dataframe(self):
        """Create a mock DataFrame for EOD data"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
        data = {
            'Open': [150.0, 151.0, 152.0, 153.0, 154.0],
            'High': [155.0, 156.0, 157.0, 158.0, 159.0],
            'Low': [149.0, 150.0, 151.0, 152.0, 153.0],
            'Close': [154.0, 155.0, 156.0, 157.0, 158.0],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }
        return pd.DataFrame(data, index=dates)
    
    @pytest.fixture
    def mock_intraday_dataframe(self):
        """Create a mock DataFrame for intraday data"""
        times = pd.date_range(start='2024-01-15 09:30', end='2024-01-15 10:00', freq='5min')
        data = {
            'Open': [150.0, 150.5, 151.0, 151.5, 152.0, 152.5, 153.0],
            'High': [150.5, 151.0, 151.5, 152.0, 152.5, 153.0, 153.5],
            'Low': [149.5, 150.0, 150.5, 151.0, 151.5, 152.0, 152.5],
            'Close': [150.5, 151.0, 151.5, 152.0, 152.5, 153.0, 153.5],
            'Volume': [10000, 11000, 12000, 13000, 14000, 15000, 16000]
        }
        return pd.DataFrame(data, index=times)
    
    def test_provider_name(self, provider):
        """Test provider name property"""
        assert provider.name == "YahooFinance"
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_eod_data_success(self, mock_ticker_class, provider, mock_eod_dataframe):
        """Test successful EOD data fetch"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_eod_dataframe
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        result = provider.fetch_eod_data('AAPL', start_date, end_date)
        
        # Verify result
        assert result.success is True
        assert len(result.candles) == 5
        assert result.provider_name == "YahooFinance"
        assert result.error_message is None
        
        # Verify first candle
        first_candle = result.candles[0]
        assert first_candle.open == Decimal('150.0')
        assert first_candle.high == Decimal('155.0')
        assert first_candle.low == Decimal('149.0')
        assert first_candle.close == Decimal('154.0')
        assert first_candle.volume == 1000000
        
        # Verify ticker was called correctly
        mock_ticker.history.assert_called_once_with(
            start='2024-01-01',
            end='2024-01-05',
            interval='1d',
            auto_adjust=False,
            actions=False
        )
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_eod_data_empty_response(self, mock_ticker_class, provider):
        """Test EOD data fetch with empty response"""
        # Setup mock to return empty DataFrame
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        result = provider.fetch_eod_data('INVALID', start_date, end_date)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert result.provider_name == "YahooFinance"
        assert "No data returned" in result.error_message
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_eod_data_network_error(self, mock_ticker_class, provider):
        """Test EOD data fetch with network error"""
        # Setup mock to raise network error
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ConnectionError("Network unreachable")
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        result = provider.fetch_eod_data('AAPL', start_date, end_date)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert result.provider_name == "YahooFinance"
        assert "Network error" in result.error_message
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_eod_data_unexpected_error(self, mock_ticker_class, provider):
        """Test EOD data fetch with unexpected error"""
        # Setup mock to raise unexpected error
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ValueError("Unexpected error")
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        result = provider.fetch_eod_data('AAPL', start_date, end_date)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert result.provider_name == "YahooFinance"
        assert "Unexpected error" in result.error_message
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_eod_data_with_invalid_candles(self, mock_ticker_class, provider):
        """Test EOD data fetch with some invalid candles (missing data)"""
        # Create DataFrame with some invalid data
        dates = pd.date_range(start='2024-01-01', end='2024-01-03', freq='D')
        data = {
            'Open': [150.0, None, 152.0],  # Missing open price
            'High': [155.0, 156.0, 157.0],
            'Low': [149.0, 150.0, 151.0],
            'Close': [154.0, 155.0, 156.0],
            'Volume': [1000000, 1100000, 1200000]
        }
        df = pd.DataFrame(data, index=dates)
        
        mock_ticker = Mock()
        mock_ticker.history.return_value = df
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        result = provider.fetch_eod_data('AAPL', start_date, end_date)
        
        # Verify result - should skip invalid candle but succeed with valid ones
        assert result.success is True
        assert len(result.candles) == 2  # Only 2 valid candles
        assert result.provider_name == "YahooFinance"
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_intraday_data_success(self, mock_ticker_class, provider, mock_intraday_dataframe):
        """Test successful intraday data fetch"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_intraday_dataframe
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_time = datetime(2024, 1, 15, 9, 30)
        end_time = datetime(2024, 1, 15, 10, 0)
        result = provider.fetch_intraday_data('AAPL', Timeframe.FIVE_MINUTE, start_time, end_time)
        
        # Verify result
        assert result.success is True
        assert len(result.candles) == 7
        assert result.provider_name == "YahooFinance"
        assert result.error_message is None
        
        # Verify first candle
        first_candle = result.candles[0]
        assert first_candle.open == Decimal('150.0')
        assert first_candle.high == Decimal('150.5')
        assert first_candle.low == Decimal('149.5')
        assert first_candle.close == Decimal('150.5')
        assert first_candle.volume == 10000
        
        # Verify ticker was called correctly
        mock_ticker.history.assert_called_once_with(
            start='2024-01-15',
            end='2024-01-15',
            interval='5m',
            auto_adjust=False,
            actions=False
        )
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_intraday_data_one_minute(self, mock_ticker_class, provider, mock_intraday_dataframe):
        """Test intraday data fetch with 1-minute timeframe"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_intraday_dataframe
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_time = datetime(2024, 1, 15, 9, 30)
        end_time = datetime(2024, 1, 15, 10, 0)
        result = provider.fetch_intraday_data('AAPL', Timeframe.ONE_MINUTE, start_time, end_time)
        
        # Verify result
        assert result.success is True
        
        # Verify correct interval was used
        mock_ticker.history.assert_called_once()
        call_kwargs = mock_ticker.history.call_args[1]
        assert call_kwargs['interval'] == '1m'
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_intraday_data_unsupported_timeframe(self, mock_ticker_class, provider):
        """Test intraday data fetch with unsupported timeframe"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data with daily timeframe (not supported for intraday)
        start_time = datetime(2024, 1, 15, 9, 30)
        end_time = datetime(2024, 1, 15, 10, 0)
        result = provider.fetch_intraday_data('AAPL', Timeframe.ONE_DAY, start_time, end_time)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert "Unsupported timeframe" in result.error_message
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_intraday_data_empty_response(self, mock_ticker_class, provider):
        """Test intraday data fetch with empty response"""
        # Setup mock to return empty DataFrame
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_time = datetime(2024, 1, 15, 9, 30)
        end_time = datetime(2024, 1, 15, 10, 0)
        result = provider.fetch_intraday_data('INVALID', Timeframe.FIVE_MINUTE, start_time, end_time)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert "No intraday data returned" in result.error_message
    
    @patch('app.services.data_providers.yf.Ticker')
    def test_fetch_intraday_data_network_error(self, mock_ticker_class, provider):
        """Test intraday data fetch with network error"""
        # Setup mock to raise network error
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ConnectionError("Network unreachable")
        mock_ticker_class.return_value = mock_ticker
        
        # Fetch data
        start_time = datetime(2024, 1, 15, 9, 30)
        end_time = datetime(2024, 1, 15, 10, 0)
        result = provider.fetch_intraday_data('AAPL', Timeframe.FIVE_MINUTE, start_time, end_time)
        
        # Verify result
        assert result.success is False
        assert len(result.candles) == 0
        assert "Network error" in result.error_message


class TestDataProviderProtocol:
    """Tests for DataProvider protocol compliance"""
    
    def test_yahoo_finance_implements_protocol(self):
        """Test that YahooFinanceProvider implements DataProvider protocol"""
        provider = YahooFinanceProvider()
        
        # Check that provider has required methods
        assert hasattr(provider, 'name')
        assert hasattr(provider, 'fetch_eod_data')
        assert hasattr(provider, 'fetch_intraday_data')
        
        # Check that methods are callable
        assert callable(provider.fetch_eod_data)
        assert callable(provider.fetch_intraday_data)
        
        # Check name property
        assert isinstance(provider.name, str)
        assert provider.name == "YahooFinance"
