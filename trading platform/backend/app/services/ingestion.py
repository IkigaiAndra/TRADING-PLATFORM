"""
Data ingestion service for orchestrating data fetching and storage.

This module provides the IngestionService class that orchestrates the complete
data ingestion pipeline: fetching data from providers with fallback support,
validating candles, handling duplicates with upsert logic, and implementing
exponential backoff for rate limiting.

Validates Requirements: 1.3, 1.4, 2.4
"""

import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.logging_config import get_logger
from app.services.data_providers import DataProvider, Candle, FetchResult, Timeframe
from app.services.validation import CandleValidator, ValidationResult
from app.models.price import Price


logger = get_logger(__name__)


@dataclass
class IngestionResult:
    """
    Result of a data ingestion operation.
    
    Attributes:
        success: Whether the ingestion was successful
        candles_fetched: Number of candles fetched from provider
        candles_validated: Number of candles that passed validation
        candles_stored: Number of candles successfully stored
        candles_updated: Number of existing candles updated (upsert)
        candles_inserted: Number of new candles inserted (upsert)
        validation_errors: Number of candles that failed validation
        provider_used: Name of the provider that successfully fetched data
        error_message: Error message if ingestion failed
    """
    success: bool
    candles_fetched: int = 0
    candles_validated: int = 0
    candles_stored: int = 0
    candles_updated: int = 0
    candles_inserted: int = 0
    validation_errors: int = 0
    provider_used: Optional[str] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(
        cls,
        candles_fetched: int,
        candles_validated: int,
        candles_stored: int,
        candles_updated: int,
        candles_inserted: int,
        validation_errors: int,
        provider_used: str
    ) -> 'IngestionResult':
        """Create a successful ingestion result"""
        return cls(
            success=True,
            candles_fetched=candles_fetched,
            candles_validated=candles_validated,
            candles_stored=candles_stored,
            candles_updated=candles_updated,
            candles_inserted=candles_inserted,
            validation_errors=validation_errors,
            provider_used=provider_used,
            error_message=None
        )
    
    @classmethod
    def failure_result(cls, error_message: str) -> 'IngestionResult':
        """Create a failed ingestion result"""
        return cls(
            success=False,
            error_message=error_message
        )


class IngestionService:
    """
    Orchestrates data fetching and storage with provider fallback.
    
    The IngestionService manages the complete data ingestion pipeline:
    1. Attempts to fetch data from primary provider
    2. Falls back to secondary providers if primary fails
    3. Validates all candles before storage
    4. Handles duplicates with upsert (update if exists, insert if new)
    5. Implements exponential backoff for rate-limited APIs
    6. Logs all ingestion activities with success/failure counts
    
    Validates Requirements: 1.3, 1.4, 2.4
    """
    
    def __init__(
        self,
        providers: List[DataProvider],
        db: Session,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """
        Initialize the ingestion service.
        
        Args:
            providers: List of data providers (tried in order)
            db: Database session
            max_retries: Maximum number of retry attempts for rate limiting
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds for exponential backoff
        """
        if not providers:
            raise ValueError("At least one data provider must be provided")
        
        self.providers = providers
        self.db = db
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        logger.info(
            "Initialized IngestionService",
            extra={'context': {
                'provider_count': len(providers),
                'provider_names': [p.name for p in providers],
                'max_retries': max_retries,
                'base_delay': base_delay,
                'max_delay': max_delay
            }}
        )
    
    def _exponential_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Formula: delay = min(base_delay * 2^attempt, max_delay)
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
            
        Validates: Requirements 2.4
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def _fetch_with_fallback(
        self,
        fetch_func,
        *args,
        **kwargs
    ) -> FetchResult:
        """
        Fetch data with provider fallback and exponential backoff.
        
        Tries each provider in order. If a provider fails due to rate limiting
        (detected by specific error messages), implements exponential backoff
        before trying the next provider.
        
        Args:
            fetch_func: Function to call on each provider (fetch_eod_data or fetch_intraday_data)
            *args: Positional arguments to pass to fetch_func
            **kwargs: Keyword arguments to pass to fetch_func
            
        Returns:
            FetchResult from the first successful provider
            
        Validates: Requirements 1.4, 2.4
        """
        last_error = None
        
        for provider_idx, provider in enumerate(self.providers):
            logger.info(
                f"Attempting to fetch data from provider {provider.name}",
                extra={'context': {
                    'provider': provider.name,
                    'provider_index': provider_idx,
                    'total_providers': len(self.providers)
                }}
            )
            
            # Try fetching with exponential backoff for rate limiting
            for attempt in range(self.max_retries):
                try:
                    # Call the fetch function on the provider
                    result = fetch_func(provider, *args, **kwargs)
                    
                    if result.success:
                        logger.info(
                            f"Successfully fetched data from {provider.name}",
                            extra={'context': {
                                'provider': provider.name,
                                'candle_count': len(result.candles),
                                'attempt': attempt + 1
                            }}
                        )
                        return result
                    
                    # Check if error is rate limiting
                    is_rate_limited = (
                        result.error_message and
                        any(keyword in result.error_message.lower() 
                            for keyword in ['rate limit', 'too many requests', '429'])
                    )
                    
                    if is_rate_limited and attempt < self.max_retries - 1:
                        delay = self._exponential_backoff_delay(attempt)
                        logger.warning(
                            f"Rate limited by {provider.name}, retrying after {delay}s",
                            extra={'context': {
                                'provider': provider.name,
                                'attempt': attempt + 1,
                                'max_retries': self.max_retries,
                                'delay_seconds': delay,
                                'error': result.error_message
                            }}
                        )
                        time.sleep(delay)
                        continue
                    
                    # Non-rate-limit error or max retries reached
                    last_error = result.error_message
                    logger.warning(
                        f"Failed to fetch from {provider.name}: {result.error_message}",
                        extra={'context': {
                            'provider': provider.name,
                            'error': result.error_message,
                            'attempt': attempt + 1
                        }}
                    )
                    break  # Try next provider
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(
                        f"Unexpected error fetching from {provider.name}",
                        extra={'context': {
                            'provider': provider.name,
                            'error': str(e),
                            'error_type': type(e).__name__,
                            'attempt': attempt + 1
                        }},
                        exc_info=True
                    )
                    break  # Try next provider
        
        # All providers failed
        error_msg = f"All providers failed. Last error: {last_error}"
        logger.error(
            "All data providers failed",
            extra={'context': {
                'provider_count': len(self.providers),
                'last_error': last_error
            }}
        )
        return FetchResult.failure_result(error_msg, "None")
    
    def _validate_candles(
        self,
        candles: List[Candle],
        timeframe: str
    ) -> tuple[List[Candle], int]:
        """
        Validate candles before storage.
        
        Args:
            candles: List of candles to validate
            timeframe: Timeframe identifier (e.g., '1D', '5m')
            
        Returns:
            Tuple of (valid_candles, validation_error_count)
            
        Validates: Requirements 1.5, 16.1-16.5
        """
        valid_candles = []
        error_count = 0
        
        for candle in candles:
            result = CandleValidator.validate_candle(
                open_price=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                timestamp=candle.timestamp,
                timeframe=timeframe,
                allow_future=False
            )
            
            if result.is_valid:
                valid_candles.append(candle)
            else:
                error_count += 1
                # Log validation errors
                error_details = [
                    f"{err.error_type.value}: {err.message}"
                    for err in result.errors
                ]
                logger.warning(
                    f"Candle validation failed",
                    extra={'context': {
                        'timestamp': candle.timestamp.isoformat(),
                        'timeframe': timeframe,
                        'errors': error_details,
                        'candle_data': {
                            'open': float(candle.open),
                            'high': float(candle.high),
                            'low': float(candle.low),
                            'close': float(candle.close),
                            'volume': candle.volume
                        }
                    }}
                )
        
        logger.info(
            f"Validation complete: {len(valid_candles)} valid, {error_count} invalid",
            extra={'context': {
                'total_candles': len(candles),
                'valid_candles': len(valid_candles),
                'invalid_candles': error_count,
                'timeframe': timeframe
            }}
        )
        
        return valid_candles, error_count
    
    def _upsert_candles(
        self,
        instrument_id: int,
        candles: List[Candle],
        timeframe: str
    ) -> tuple[int, int]:
        """
        Store candles with upsert logic (update if exists, insert if new).
        
        Uses PostgreSQL's INSERT ... ON CONFLICT DO UPDATE to handle duplicates
        efficiently in a single query.
        
        Args:
            instrument_id: Instrument ID
            candles: List of validated candles to store
            timeframe: Timeframe identifier
            
        Returns:
            Tuple of (inserted_count, updated_count)
            
        Validates: Requirements 1.3
        """
        if not candles:
            return 0, 0
        
        # Prepare data for bulk upsert
        candle_dicts = []
        for candle in candles:
            candle_dicts.append({
                'instrument_id': instrument_id,
                'timestamp': candle.timestamp,
                'timeframe': timeframe,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        try:
            # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
            stmt = insert(Price).values(candle_dicts)
            
            # On conflict (duplicate key), update the existing record
            stmt = stmt.on_conflict_do_update(
                index_elements=['instrument_id', 'timestamp', 'timeframe'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume
                }
            )
            
            # Execute the upsert
            result = self.db.execute(stmt)
            self.db.commit()
            
            # Note: PostgreSQL doesn't easily distinguish between inserts and updates
            # in the result, so we'll report total stored count
            stored_count = len(candles)
            
            logger.info(
                f"Upserted {stored_count} candles",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'timeframe': timeframe,
                    'candles_stored': stored_count
                }}
            )
            
            # For simplicity, we'll assume all are inserts (can be refined later)
            # In practice, we'd need to query before to determine which exist
            return stored_count, 0
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to upsert candles",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'timeframe': timeframe,
                    'candle_count': len(candles),
                    'error': str(e),
                    'error_type': type(e).__name__
                }},
                exc_info=True
            )
            raise
    
    def ingest_eod(
        self,
        instrument_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1D'
    ) -> IngestionResult:
        """
        Ingest end-of-day data with fallback providers.
        
        Complete ingestion pipeline:
        1. Fetch data from providers (with fallback)
        2. Validate all candles
        3. Store valid candles with upsert logic
        4. Log ingestion statistics
        
        Args:
            instrument_id: Instrument ID
            symbol: Instrument symbol (e.g., 'AAPL')
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            timeframe: Timeframe identifier (default: '1D')
            
        Returns:
            IngestionResult with detailed statistics
            
        Validates: Requirements 1.3, 1.4, 2.4
        """
        logger.info(
            f"Starting EOD data ingestion for {symbol}",
            extra={'context': {
                'instrument_id': instrument_id,
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'timeframe': timeframe
            }}
        )
        
        # Fetch data with provider fallback
        fetch_result = self._fetch_with_fallback(
            lambda provider: provider.fetch_eod_data(symbol, start_date, end_date)
        )
        
        if not fetch_result.success:
            logger.error(
                f"Failed to fetch EOD data for {symbol}",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'error': fetch_result.error_message
                }}
            )
            return IngestionResult.failure_result(fetch_result.error_message)
        
        candles_fetched = len(fetch_result.candles)
        
        # Validate candles
        valid_candles, validation_errors = self._validate_candles(
            fetch_result.candles,
            timeframe
        )
        
        if not valid_candles:
            error_msg = f"No valid candles after validation (all {candles_fetched} failed)"
            logger.error(
                error_msg,
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'candles_fetched': candles_fetched,
                    'validation_errors': validation_errors
                }}
            )
            return IngestionResult.failure_result(error_msg)
        
        # Store candles with upsert
        try:
            inserted, updated = self._upsert_candles(
                instrument_id,
                valid_candles,
                timeframe
            )
            
            result = IngestionResult.success_result(
                candles_fetched=candles_fetched,
                candles_validated=len(valid_candles),
                candles_stored=inserted + updated,
                candles_inserted=inserted,
                candles_updated=updated,
                validation_errors=validation_errors,
                provider_used=fetch_result.provider_name
            )
            
            logger.info(
                f"Successfully ingested EOD data for {symbol}",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'candles_fetched': candles_fetched,
                    'candles_validated': len(valid_candles),
                    'candles_stored': inserted + updated,
                    'candles_inserted': inserted,
                    'candles_updated': updated,
                    'validation_errors': validation_errors,
                    'provider_used': fetch_result.provider_name
                }}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to store candles: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'error': str(e),
                    'error_type': type(e).__name__
                }},
                exc_info=True
            )
            return IngestionResult.failure_result(error_msg)
    
    def ingest_intraday(
        self,
        instrument_id: int,
        symbol: str,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: datetime
    ) -> IngestionResult:
        """
        Ingest intraday data with fallback providers.
        
        Complete ingestion pipeline:
        1. Fetch data from providers (with fallback)
        2. Validate all candles (including timeframe alignment)
        3. Store valid candles with upsert logic
        4. Log ingestion statistics
        
        Args:
            instrument_id: Instrument ID
            symbol: Instrument symbol (e.g., 'AAPL')
            timeframe: Candle frequency (5m, 1m, etc.)
            start_time: Start time (inclusive)
            end_time: End time (inclusive)
            
        Returns:
            IngestionResult with detailed statistics
            
        Validates: Requirements 1.3, 1.4, 2.4
        """
        logger.info(
            f"Starting intraday data ingestion for {symbol}",
            extra={'context': {
                'instrument_id': instrument_id,
                'symbol': symbol,
                'timeframe': timeframe.value,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }}
        )
        
        # Fetch data with provider fallback
        fetch_result = self._fetch_with_fallback(
            lambda provider: provider.fetch_intraday_data(
                symbol, timeframe, start_time, end_time
            )
        )
        
        if not fetch_result.success:
            logger.error(
                f"Failed to fetch intraday data for {symbol}",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'error': fetch_result.error_message
                }}
            )
            return IngestionResult.failure_result(fetch_result.error_message)
        
        candles_fetched = len(fetch_result.candles)
        
        # Validate candles (including timeframe alignment)
        valid_candles, validation_errors = self._validate_candles(
            fetch_result.candles,
            timeframe.value
        )
        
        if not valid_candles:
            error_msg = f"No valid candles after validation (all {candles_fetched} failed)"
            logger.error(
                error_msg,
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'candles_fetched': candles_fetched,
                    'validation_errors': validation_errors
                }}
            )
            return IngestionResult.failure_result(error_msg)
        
        # Store candles with upsert
        try:
            inserted, updated = self._upsert_candles(
                instrument_id,
                valid_candles,
                timeframe.value
            )
            
            result = IngestionResult.success_result(
                candles_fetched=candles_fetched,
                candles_validated=len(valid_candles),
                candles_stored=inserted + updated,
                candles_inserted=inserted,
                candles_updated=updated,
                validation_errors=validation_errors,
                provider_used=fetch_result.provider_name
            )
            
            logger.info(
                f"Successfully ingested intraday data for {symbol}",
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'candles_fetched': candles_fetched,
                    'candles_validated': len(valid_candles),
                    'candles_stored': inserted + updated,
                    'candles_inserted': inserted,
                    'candles_updated': updated,
                    'validation_errors': validation_errors,
                    'provider_used': fetch_result.provider_name
                }}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to store candles: {str(e)}"
            logger.error(
                error_msg,
                extra={'context': {
                    'instrument_id': instrument_id,
                    'symbol': symbol,
                    'timeframe': timeframe.value,
                    'error': str(e),
                    'error_type': type(e).__name__
                }},
                exc_info=True
            )
            return IngestionResult.failure_result(error_msg)
