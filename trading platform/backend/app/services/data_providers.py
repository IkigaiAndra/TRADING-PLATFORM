"""
Data provider interfaces and implementations for fetching market data.

This module defines the DataProvider protocol (interface) and concrete implementations
for various data sources (Yahoo Finance, Stooq, Polygon, IBKR). Each provider
implements methods to fetch EOD and intraday OHLCV data.

Validates Requirements: 1.1, 20.1, 20.3
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Protocol
import logging

import yfinance as yf
from requests.exceptions import RequestException, Timeout, ConnectionError

from app.logging_config import get_logger


logger = get_logger(__name__)


class Timeframe(Enum):
    """Supported timeframe identifiers"""
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    THIRTY_MINUTE = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"


@dataclass
class Candle:
    """
    Represents a single OHLCV candle.
    
    Attributes:
        timestamp: Candle timestamp
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
    """
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    
    def to_dict(self) -> dict:
        """Convert candle to dictionary"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


@dataclass
class FetchResult:
    """
    Result of a data fetch operation.
    
    Attributes:
        success: Whether the fetch was successful
        candles: List of fetched candles (empty if failed)
        error_message: Error message if fetch failed
        provider_name: Name of the provider that fetched the data
    """
    success: bool
    candles: List[Candle]
    error_message: Optional[str] = None
    provider_name: Optional[str] = None
    
    @classmethod
    def success_result(cls, candles: List[Candle], provider_name: str) -> 'FetchResult':
        """Create a successful fetch result"""
        return cls(
            success=True,
            candles=candles,
            error_message=None,
            provider_name=provider_name
        )
    
    @classmethod
    def failure_result(cls, error_message: str, provider_name: str) -> 'FetchResult':
        """Create a failed fetch result"""
        return cls(
            success=False,
            candles=[],
            error_message=error_message,
            provider_name=provider_name
        )


class DataProvider(Protocol):
    """
    Abstract interface for data providers.
    
    All data providers must implement this protocol to fetch EOD and intraday
    OHLCV data from external sources. Implementations should handle errors
    gracefully and return FetchResult objects.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and identification"""
        ...
    
    @abstractmethod
    def fetch_eod_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> FetchResult:
        """
        Fetch end-of-day OHLCV data.
        
        Args:
            symbol: Instrument symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for data fetch (inclusive)
            end_date: End date for data fetch (inclusive)
            
        Returns:
            FetchResult containing candles or error information
            
        Validates: Requirements 1.1
        """
        ...
    
    @abstractmethod
    def fetch_intraday_data(
        self,
        symbol: str,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: datetime
    ) -> FetchResult:
        """
        Fetch intraday OHLCV data.
        
        Args:
            symbol: Instrument symbol (e.g., 'AAPL', 'MSFT')
            timeframe: Candle frequency (5m, 1m, etc.)
            start_time: Start time for data fetch (inclusive)
            end_time: End time for data fetch (inclusive)
            
        Returns:
            FetchResult containing candles or error information
            
        Validates: Requirements 2.1
        """
        ...


class YahooFinanceProvider:
    """
    Yahoo Finance data provider implementation.
    
    Fetches EOD and intraday data from Yahoo Finance using the yfinance library.
    Handles errors gracefully and provides structured logging.
    
    Validates Requirements: 1.1, 20.1, 20.3
    """
    
    def __init__(self):
        """Initialize Yahoo Finance provider"""
        self._name = "YahooFinance"
        logger.info(
            "Initialized Yahoo Finance provider",
            extra={'context': {'provider': self._name}}
        )
    
    @property
    def name(self) -> str:
        """Provider name for logging and identification"""
        return self._name
    
    def fetch_eod_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> FetchResult:
        """
        Fetch end-of-day OHLCV data from Yahoo Finance.
        
        Args:
            symbol: Instrument symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for data fetch (inclusive)
            end_date: End date for data fetch (inclusive)
            
        Returns:
            FetchResult containing candles or error information
            
        Validates: Requirements 1.1, 20.1, 20.3
        """
        logger.info(
            f"Fetching EOD data for {symbol}",
            extra={'context': {
                'provider': self._name,
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }}
        )
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            # yfinance expects dates as strings in YYYY-MM-DD format
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d',
                auto_adjust=False,  # Don't adjust for splits/dividends
                actions=False  # Don't include dividends/splits
            )
            
            # Check if data was returned
            if df.empty:
                error_msg = f"No data returned for symbol {symbol}"
                logger.warning(
                    error_msg,
                    extra={'context': {
                        'provider': self._name,
                        'symbol': symbol,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    }}
                )
                return FetchResult.failure_result(error_msg, self._name)
            
            # Convert DataFrame to Candle objects
            candles = []
            for timestamp, row in df.iterrows():
                try:
                    candle = Candle(
                        timestamp=timestamp.to_pydatetime(),
                        open=Decimal(str(row['Open'])),
                        high=Decimal(str(row['High'])),
                        low=Decimal(str(row['Low'])),
                        close=Decimal(str(row['Close'])),
                        volume=int(row['Volume'])
                    )
                    candles.append(candle)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"Skipping invalid candle at {timestamp}: {str(e)}",
                        extra={'context': {
                            'provider': self._name,
                            'symbol': symbol,
                            'timestamp': str(timestamp),
                            'error': str(e)
                        }}
                    )
                    continue
            
            if not candles:
                error_msg = f"No valid candles extracted for symbol {symbol}"
                logger.error(
                    error_msg,
                    extra={'context': {
                        'provider': self._name,
                        'symbol': symbol,
                        'rows_processed': len(df)
                    }}
                )
                return FetchResult.failure_result(error_msg, self._name)
            
            logger.info(
                f"Successfully fetched {len(candles)} EOD candles for {symbol}",
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'candle_count': len(candles),
                    'start_date': candles[0].timestamp.isoformat() if candles else None,
                    'end_date': candles[-1].timestamp.isoformat() if candles else None
                }}
            )
            
            return FetchResult.success_result(candles, self._name)
            
        except (RequestException, Timeout, ConnectionError) as e:
            error_msg = f"Network error fetching data for {symbol}: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'error_type': type(e).__name__,
                    'error': str(e)
                }},
                exc_info=True
            )
            return FetchResult.failure_result(error_msg, self._name)
            
        except Exception as e:
            error_msg = f"Unexpected error fetching data for {symbol}: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'error_type': type(e).__name__,
                    'error': str(e)
                }},
                exc_info=True
            )
            return FetchResult.failure_result(error_msg, self._name)
    
    def fetch_intraday_data(
        self,
        symbol: str,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: datetime
    ) -> FetchResult:
        """
        Fetch intraday OHLCV data from Yahoo Finance.
        
        Yahoo Finance supports intraday data for recent periods (last 60 days for 1m,
        last 730 days for other intervals). Supported intervals: 1m, 5m, 15m, 30m, 1h.
        
        Args:
            symbol: Instrument symbol (e.g., 'AAPL', 'MSFT')
            timeframe: Candle frequency (5m, 1m, etc.)
            start_time: Start time for data fetch (inclusive)
            end_time: End time for data fetch (inclusive)
            
        Returns:
            FetchResult containing candles or error information
            
        Validates: Requirements 2.1, 20.1, 20.3
        """
        logger.info(
            f"Fetching intraday data for {symbol}",
            extra={'context': {
                'provider': self._name,
                'symbol': symbol,
                'timeframe': timeframe.value,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }}
        )
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Map our timeframe enum to yfinance interval strings
            interval_map = {
                Timeframe.ONE_MINUTE: '1m',
                Timeframe.FIVE_MINUTE: '5m',
                Timeframe.FIFTEEN_MINUTE: '15m',
                Timeframe.THIRTY_MINUTE: '30m',
                Timeframe.ONE_HOUR: '1h',
            }
            
            if timeframe not in interval_map:
                error_msg = f"Unsupported timeframe for intraday data: {timeframe.value}"
                logger.error(
                    error_msg,
                    extra={'context': {
                        'provider': self._name,
                        'symbol': symbol,
                        'timeframe': timeframe.value,
                        'supported_timeframes': list(interval_map.keys())
                    }}
                )
                return FetchResult.failure_result(error_msg, self._name)
            
            interval = interval_map[timeframe]
            
            # Fetch historical data
            df = ticker.history(
                start=start_time.strftime('%Y-%m-%d'),
                end=end_time.strftime('%Y-%m-%d'),
                interval=interval,
                auto_adjust=False,
                actions=False
            )
            
            # Check if data was returned
            if df.empty:
                error_msg = f"No intraday data returned for symbol {symbol}"
                logger.warning(
                    error_msg,
                    extra={'context': {
                        'provider': self._name,
                        'symbol': symbol,
                        'timeframe': timeframe.value,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat()
                    }}
                )
                return FetchResult.failure_result(error_msg, self._name)
            
            # Convert DataFrame to Candle objects
            candles = []
            for timestamp, row in df.iterrows():
                try:
                    candle = Candle(
                        timestamp=timestamp.to_pydatetime(),
                        open=Decimal(str(row['Open'])),
                        high=Decimal(str(row['High'])),
                        low=Decimal(str(row['Low'])),
                        close=Decimal(str(row['Close'])),
                        volume=int(row['Volume'])
                    )
                    candles.append(candle)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"Skipping invalid candle at {timestamp}: {str(e)}",
                        extra={'context': {
                            'provider': self._name,
                            'symbol': symbol,
                            'timestamp': str(timestamp),
                            'error': str(e)
                        }}
                    )
                    continue
            
            if not candles:
                error_msg = f"No valid intraday candles extracted for symbol {symbol}"
                logger.error(
                    error_msg,
                    extra={'context': {
                        'provider': self._name,
                        'symbol': symbol,
                        'timeframe': timeframe.value,
                        'rows_processed': len(df)
                    }}
                )
                return FetchResult.failure_result(error_msg, self._name)
            
            logger.info(
                f"Successfully fetched {len(candles)} intraday candles for {symbol}",
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'candle_count': len(candles),
                    'start_time': candles[0].timestamp.isoformat() if candles else None,
                    'end_time': candles[-1].timestamp.isoformat() if candles else None
                }}
            )
            
            return FetchResult.success_result(candles, self._name)
            
        except (RequestException, Timeout, ConnectionError) as e:
            error_msg = f"Network error fetching intraday data for {symbol}: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'error_type': type(e).__name__,
                    'error': str(e)
                }},
                exc_info=True
            )
            return FetchResult.failure_result(error_msg, self._name)
            
        except Exception as e:
            error_msg = f"Unexpected error fetching intraday data for {symbol}: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'provider': self._name,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'error_type': type(e).__name__,
                    'error': str(e)
                }},
                exc_info=True
            )
            return FetchResult.failure_result(error_msg, self._name)
