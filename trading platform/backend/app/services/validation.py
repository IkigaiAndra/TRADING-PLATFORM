"""
Candle validation module for OHLCV data.

This module provides comprehensive validation for candle data before storage,
ensuring data quality and integrity. Validates OHLC relationships, volume,
timestamps, and timeframe alignment.

Validates Requirements: 1.5, 16.1, 16.2, 16.3, 16.4, 2.5
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass


class ValidationErrorType(Enum):
    """Types of validation errors"""
    OHLC_INVALID = "ohlc_invalid"
    VOLUME_NEGATIVE = "volume_negative"
    TIMESTAMP_FUTURE = "timestamp_future"
    TIMEFRAME_MISALIGNMENT = "timeframe_misalignment"


@dataclass
class ValidationError:
    """Represents a validation error"""
    error_type: ValidationErrorType
    message: str
    field: Optional[str] = None
    value: Optional[any] = None


@dataclass
class ValidationResult:
    """Result of candle validation"""
    is_valid: bool
    errors: List[ValidationError]
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context"""
        return self.is_valid
    
    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create a successful validation result"""
        return cls(is_valid=True, errors=[])
    
    @classmethod
    def failure(cls, errors: List[ValidationError]) -> 'ValidationResult':
        """Create a failed validation result"""
        return cls(is_valid=False, errors=errors)


class CandleValidator:
    """
    Validator for OHLCV candle data.
    
    Provides comprehensive validation including:
    - OHLC relationship validation (Low <= Open <= High, Low <= Close <= High)
    - Volume non-negativity check
    - Timestamp validation (no future dates)
    - Timeframe alignment validation for intraday data
    """
    
    # Timeframe alignment rules: timeframe -> minutes divisor
    TIMEFRAME_RULES = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1D': None,  # Daily data doesn't require minute alignment
        '1W': None,  # Weekly data doesn't require minute alignment
        '1M': None,  # Monthly data doesn't require minute alignment
    }
    
    @staticmethod
    def validate_ohlc(
        open_price: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal
    ) -> ValidationResult:
        """
        Validate OHLC relationships.
        
        Requirements:
        - Low <= High
        - Low <= Open <= High
        - Low <= Close <= High
        
        Args:
            open_price: Opening price
            high: Highest price
            low: Lowest price
            close: Closing price
            
        Returns:
            ValidationResult indicating success or failure with error details
            
        Validates: Requirements 1.5, 16.1, 16.2
        """
        errors = []
        
        # Check Low <= High
        if low > high:
            errors.append(ValidationError(
                error_type=ValidationErrorType.OHLC_INVALID,
                message=f"Low ({low}) must be less than or equal to High ({high})",
                field="low,high",
                value={"low": float(low), "high": float(high)}
            ))
        
        # Check Low <= Open <= High
        if open_price < low or open_price > high:
            errors.append(ValidationError(
                error_type=ValidationErrorType.OHLC_INVALID,
                message=f"Open ({open_price}) must be between Low ({low}) and High ({high})",
                field="open",
                value=float(open_price)
            ))
        
        # Check Low <= Close <= High
        if close < low or close > high:
            errors.append(ValidationError(
                error_type=ValidationErrorType.OHLC_INVALID,
                message=f"Close ({close}) must be between Low ({low}) and High ({high})",
                field="close",
                value=float(close)
            ))
        
        if errors:
            return ValidationResult.failure(errors)
        return ValidationResult.success()
    
    @staticmethod
    def validate_volume(volume: int) -> ValidationResult:
        """
        Validate volume is non-negative.
        
        Args:
            volume: Trading volume
            
        Returns:
            ValidationResult indicating success or failure with error details
            
        Validates: Requirements 16.3
        """
        if volume < 0:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.VOLUME_NEGATIVE,
                    message=f"Volume ({volume}) must be non-negative",
                    field="volume",
                    value=volume
                )
            ])
        return ValidationResult.success()
    
    @staticmethod
    def validate_timestamp(timestamp: datetime, allow_future: bool = False) -> ValidationResult:
        """
        Validate timestamp is not in the future.
        
        Args:
            timestamp: Candle timestamp
            allow_future: If True, allow future timestamps (default: False)
            
        Returns:
            ValidationResult indicating success or failure with error details
            
        Validates: Requirements 16.4
        """
        if allow_future:
            return ValidationResult.success()
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        
        # Make timestamp timezone-aware if it's naive
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        if timestamp > now:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.TIMESTAMP_FUTURE,
                    message=f"Timestamp ({timestamp}) cannot be in the future (now: {now})",
                    field="timestamp",
                    value=timestamp.isoformat()
                )
            ])
        return ValidationResult.success()
    
    @staticmethod
    def validate_timeframe_alignment(
        timestamp: datetime,
        timeframe: str
    ) -> ValidationResult:
        """
        Validate timestamp aligns with declared timeframe.
        
        For intraday data, timestamps must align with their frequency:
        - 1m: Every minute (:00, :01, :02, ...)
        - 5m: Every 5 minutes (:00, :05, :10, :15, ...)
        - 15m: Every 15 minutes (:00, :15, :30, :45)
        - 30m: Every 30 minutes (:00, :30)
        - 1h: Every hour (:00)
        - 4h: Every 4 hours (00:00, 04:00, 08:00, ...)
        
        Daily, weekly, and monthly data don't require minute alignment.
        
        Args:
            timestamp: Candle timestamp
            timeframe: Timeframe identifier (e.g., '5m', '1D')
            
        Returns:
            ValidationResult indicating success or failure with error details
            
        Validates: Requirements 2.5
        """
        # Check if timeframe is recognized
        if timeframe not in CandleValidator.TIMEFRAME_RULES:
            # Unknown timeframe - we'll be lenient and allow it
            return ValidationResult.success()
        
        minutes_divisor = CandleValidator.TIMEFRAME_RULES[timeframe]
        
        # Daily and higher timeframes don't require minute alignment
        if minutes_divisor is None:
            return ValidationResult.success()
        
        # Check minute alignment
        if timestamp.minute % minutes_divisor != 0:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.TIMEFRAME_MISALIGNMENT,
                    message=(
                        f"Timestamp minute ({timestamp.minute}) does not align with "
                        f"timeframe {timeframe} (must be divisible by {minutes_divisor})"
                    ),
                    field="timestamp",
                    value=timestamp.isoformat()
                )
            ])
        
        # For timeframes >= 1 hour, also check seconds are zero
        if minutes_divisor >= 60 and timestamp.second != 0:
            return ValidationResult.failure([
                ValidationError(
                    error_type=ValidationErrorType.TIMEFRAME_MISALIGNMENT,
                    message=(
                        f"Timestamp for {timeframe} timeframe must have zero seconds "
                        f"(got {timestamp.second})"
                    ),
                    field="timestamp",
                    value=timestamp.isoformat()
                )
            ])
        
        return ValidationResult.success()
    
    @classmethod
    def validate_candle(
        cls,
        open_price: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int,
        timestamp: datetime,
        timeframe: str,
        allow_future: bool = False
    ) -> ValidationResult:
        """
        Perform comprehensive validation on a candle.
        
        Validates:
        - OHLC relationships
        - Volume non-negativity
        - Timestamp (no future dates unless allowed)
        - Timeframe alignment
        
        Args:
            open_price: Opening price
            high: Highest price
            low: Lowest price
            close: Closing price
            volume: Trading volume
            timestamp: Candle timestamp
            timeframe: Timeframe identifier
            allow_future: If True, allow future timestamps (default: False)
            
        Returns:
            ValidationResult with all validation errors (if any)
            
        Validates: Requirements 1.5, 16.1, 16.2, 16.3, 16.4, 2.5
        """
        all_errors = []
        
        # Validate OHLC
        ohlc_result = cls.validate_ohlc(open_price, high, low, close)
        if not ohlc_result.is_valid:
            all_errors.extend(ohlc_result.errors)
        
        # Validate volume
        volume_result = cls.validate_volume(volume)
        if not volume_result.is_valid:
            all_errors.extend(volume_result.errors)
        
        # Validate timestamp
        timestamp_result = cls.validate_timestamp(timestamp, allow_future)
        if not timestamp_result.is_valid:
            all_errors.extend(timestamp_result.errors)
        
        # Validate timeframe alignment
        alignment_result = cls.validate_timeframe_alignment(timestamp, timeframe)
        if not alignment_result.is_valid:
            all_errors.extend(alignment_result.errors)
        
        if all_errors:
            return ValidationResult.failure(all_errors)
        return ValidationResult.success()


def validate_candle_dict(candle_data: dict, allow_future: bool = False) -> ValidationResult:
    """
    Convenience function to validate a candle from a dictionary.
    
    Args:
        candle_data: Dictionary with keys: open, high, low, close, volume, timestamp, timeframe
        allow_future: If True, allow future timestamps (default: False)
        
    Returns:
        ValidationResult with all validation errors (if any)
        
    Example:
        >>> candle = {
        ...     'open': Decimal('150.00'),
        ...     'high': Decimal('155.00'),
        ...     'low': Decimal('149.00'),
        ...     'close': Decimal('154.00'),
        ...     'volume': 1000000,
        ...     'timestamp': datetime(2024, 1, 15, 10, 0, 0),
        ...     'timeframe': '1D'
        ... }
        >>> result = validate_candle_dict(candle)
        >>> result.is_valid
        True
    """
    return CandleValidator.validate_candle(
        open_price=candle_data['open'],
        high=candle_data['high'],
        low=candle_data['low'],
        close=candle_data['close'],
        volume=candle_data['volume'],
        timestamp=candle_data['timestamp'],
        timeframe=candle_data['timeframe'],
        allow_future=allow_future
    )
