"""Unit tests for candle validation module"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.services.validation import (
    CandleValidator,
    ValidationResult,
    ValidationError,
    ValidationErrorType,
    validate_candle_dict
)


class TestOHLCValidation:
    """Test suite for OHLC relationship validation"""
    
    def test_valid_ohlc(self):
        """Test validation passes for valid OHLC data"""
        # Arrange
        open_price = Decimal("150.00")
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("154.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_valid_ohlc_equal_values(self):
        """Test validation passes when all OHLC values are equal"""
        # Arrange
        price = Decimal("150.00")
        
        # Act
        result = CandleValidator.validate_ohlc(price, price, price, price)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_valid_ohlc_open_equals_low(self):
        """Test validation passes when open equals low"""
        # Arrange
        open_price = Decimal("149.00")
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("154.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is True
    
    def test_valid_ohlc_close_equals_high(self):
        """Test validation passes when close equals high"""
        # Arrange
        open_price = Decimal("150.00")
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("155.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is True
    
    def test_invalid_high_less_than_low(self):
        """Test validation fails when high < low"""
        # Arrange
        open_price = Decimal("150.00")
        high = Decimal("145.00")  # Invalid: high < low
        low = Decimal("149.00")
        close = Decimal("148.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any(e.error_type == ValidationErrorType.OHLC_INVALID for e in result.errors)
        assert any("Low" in e.message and "High" in e.message for e in result.errors)
    
    def test_invalid_open_above_high(self):
        """Test validation fails when open > high"""
        # Arrange
        open_price = Decimal("160.00")  # Invalid: open > high
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("154.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any(e.error_type == ValidationErrorType.OHLC_INVALID for e in result.errors)
        assert any("Open" in e.message for e in result.errors)
    
    def test_invalid_open_below_low(self):
        """Test validation fails when open < low"""
        # Arrange
        open_price = Decimal("145.00")  # Invalid: open < low
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("154.00")
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any(e.error_type == ValidationErrorType.OHLC_INVALID for e in result.errors)
        assert any("Open" in e.message for e in result.errors)
    
    def test_invalid_close_above_high(self):
        """Test validation fails when close > high"""
        # Arrange
        open_price = Decimal("150.00")
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("160.00")  # Invalid: close > high
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any(e.error_type == ValidationErrorType.OHLC_INVALID for e in result.errors)
        assert any("Close" in e.message for e in result.errors)
    
    def test_invalid_close_below_low(self):
        """Test validation fails when close < low"""
        # Arrange
        open_price = Decimal("150.00")
        high = Decimal("155.00")
        low = Decimal("149.00")
        close = Decimal("145.00")  # Invalid: close < low
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any(e.error_type == ValidationErrorType.OHLC_INVALID for e in result.errors)
        assert any("Close" in e.message for e in result.errors)
    
    def test_multiple_ohlc_violations(self):
        """Test validation reports multiple errors when multiple constraints violated"""
        # Arrange
        open_price = Decimal("160.00")  # Invalid: open > high
        high = Decimal("145.00")  # Invalid: high < low
        low = Decimal("149.00")
        close = Decimal("140.00")  # Invalid: close < low
        
        # Act
        result = CandleValidator.validate_ohlc(open_price, high, low, close)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Should have multiple errors


class TestVolumeValidation:
    """Test suite for volume validation"""
    
    def test_valid_positive_volume(self):
        """Test validation passes for positive volume"""
        # Arrange
        volume = 1000000
        
        # Act
        result = CandleValidator.validate_volume(volume)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_valid_zero_volume(self):
        """Test validation passes for zero volume"""
        # Arrange
        volume = 0
        
        # Act
        result = CandleValidator.validate_volume(volume)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_negative_volume(self):
        """Test validation fails for negative volume"""
        # Arrange
        volume = -1000
        
        # Act
        result = CandleValidator.validate_volume(volume)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.VOLUME_NEGATIVE
        assert "non-negative" in result.errors[0].message.lower()


class TestTimestampValidation:
    """Test suite for timestamp validation"""
    
    def test_valid_past_timestamp(self):
        """Test validation passes for past timestamp"""
        # Arrange
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_timestamp(past_time)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_valid_current_timestamp(self):
        """Test validation passes for current timestamp"""
        # Arrange
        current_time = datetime.now(timezone.utc)
        
        # Act
        result = CandleValidator.validate_timestamp(current_time)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_future_timestamp(self):
        """Test validation fails for future timestamp"""
        # Arrange
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_timestamp(future_time)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.TIMESTAMP_FUTURE
        assert "future" in result.errors[0].message.lower()
    
    def test_future_timestamp_allowed_when_flag_set(self):
        """Test validation passes for future timestamp when allow_future=True"""
        # Arrange
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_timestamp(future_time, allow_future=True)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_naive_timestamp_converted_to_utc(self):
        """Test naive timestamp is treated as UTC"""
        # Arrange
        naive_past = datetime.now() - timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_timestamp(naive_past)
        
        # Assert
        assert result.is_valid is True


class TestTimeframeAlignment:
    """Test suite for timeframe alignment validation"""
    
    def test_valid_1m_alignment(self):
        """Test 1m timeframe accepts any minute"""
        # Arrange
        timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 1, 0),
            datetime(2024, 1, 15, 10, 59, 0),
        ]
        
        # Act & Assert
        for ts in timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '1m')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_valid_5m_alignment(self):
        """Test 5m timeframe accepts minutes divisible by 5"""
        # Arrange
        valid_timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 5, 0),
            datetime(2024, 1, 15, 10, 10, 0),
            datetime(2024, 1, 15, 10, 55, 0),
        ]
        
        # Act & Assert
        for ts in valid_timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '5m')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_invalid_5m_alignment(self):
        """Test 5m timeframe rejects minutes not divisible by 5"""
        # Arrange
        invalid_timestamps = [
            datetime(2024, 1, 15, 10, 1, 0),
            datetime(2024, 1, 15, 10, 7, 0),
            datetime(2024, 1, 15, 10, 13, 0),
        ]
        
        # Act & Assert
        for ts in invalid_timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '5m')
            assert result.is_valid is False, f"Should fail for {ts}"
            assert result.errors[0].error_type == ValidationErrorType.TIMEFRAME_MISALIGNMENT
    
    def test_valid_15m_alignment(self):
        """Test 15m timeframe accepts minutes divisible by 15"""
        # Arrange
        valid_timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 15, 0),
            datetime(2024, 1, 15, 10, 30, 0),
            datetime(2024, 1, 15, 10, 45, 0),
        ]
        
        # Act & Assert
        for ts in valid_timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '15m')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_valid_30m_alignment(self):
        """Test 30m timeframe accepts minutes 0 and 30"""
        # Arrange
        valid_timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 30, 0),
        ]
        
        # Act & Assert
        for ts in valid_timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '30m')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_valid_1h_alignment(self):
        """Test 1h timeframe requires minute 0 and second 0"""
        # Arrange
        valid_timestamp = datetime(2024, 1, 15, 10, 0, 0)
        
        # Act
        result = CandleValidator.validate_timeframe_alignment(valid_timestamp, '1h')
        
        # Assert
        assert result.is_valid is True
    
    def test_invalid_1h_alignment_nonzero_minute(self):
        """Test 1h timeframe rejects non-zero minutes"""
        # Arrange
        invalid_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        # Act
        result = CandleValidator.validate_timeframe_alignment(invalid_timestamp, '1h')
        
        # Assert
        assert result.is_valid is False
        assert result.errors[0].error_type == ValidationErrorType.TIMEFRAME_MISALIGNMENT
    
    def test_invalid_1h_alignment_nonzero_second(self):
        """Test 1h timeframe rejects non-zero seconds"""
        # Arrange
        invalid_timestamp = datetime(2024, 1, 15, 10, 0, 30)
        
        # Act
        result = CandleValidator.validate_timeframe_alignment(invalid_timestamp, '1h')
        
        # Assert
        assert result.is_valid is False
        assert result.errors[0].error_type == ValidationErrorType.TIMEFRAME_MISALIGNMENT
    
    def test_valid_4h_alignment(self):
        """Test 4h timeframe requires hours divisible by 4"""
        # Arrange
        valid_timestamps = [
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 1, 15, 4, 0, 0),
            datetime(2024, 1, 15, 8, 0, 0),
            datetime(2024, 1, 15, 12, 0, 0),
            datetime(2024, 1, 15, 16, 0, 0),
            datetime(2024, 1, 15, 20, 0, 0),
        ]
        
        # Act & Assert
        for ts in valid_timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '4h')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_daily_timeframe_no_alignment_required(self):
        """Test daily timeframe doesn't require minute alignment"""
        # Arrange
        timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 37, 0),
            datetime(2024, 1, 15, 16, 0, 0),
        ]
        
        # Act & Assert
        for ts in timestamps:
            result = CandleValidator.validate_timeframe_alignment(ts, '1D')
            assert result.is_valid is True, f"Failed for {ts}"
    
    def test_unknown_timeframe_passes(self):
        """Test unknown timeframe is accepted (lenient)"""
        # Arrange
        timestamp = datetime(2024, 1, 15, 10, 37, 0)
        
        # Act
        result = CandleValidator.validate_timeframe_alignment(timestamp, 'unknown')
        
        # Assert
        assert result.is_valid is True


class TestComprehensiveValidation:
    """Test suite for comprehensive candle validation"""
    
    def test_valid_candle_all_checks_pass(self):
        """Test validation passes when all checks pass"""
        # Arrange
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_candle(
            open_price=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000,
            timestamp=past_time,
            timeframe='1D'
        )
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_candle_multiple_errors(self):
        """Test validation reports all errors when multiple checks fail"""
        # Arrange
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Act
        result = CandleValidator.validate_candle(
            open_price=Decimal("160.00"),  # Invalid: open > high
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=-1000,  # Invalid: negative volume
            timestamp=future_time,  # Invalid: future timestamp
            timeframe='5m'
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Should have multiple errors
        error_types = {e.error_type for e in result.errors}
        assert ValidationErrorType.OHLC_INVALID in error_types
        assert ValidationErrorType.VOLUME_NEGATIVE in error_types
        assert ValidationErrorType.TIMESTAMP_FUTURE in error_types
    
    def test_invalid_candle_timeframe_misalignment(self):
        """Test validation catches timeframe misalignment"""
        # Arrange
        past_time = datetime(2024, 1, 15, 10, 7, 0)  # Not aligned to 5m
        
        # Act
        result = CandleValidator.validate_candle(
            open_price=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000,
            timestamp=past_time,
            timeframe='5m'
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.TIMEFRAME_MISALIGNMENT
    
    def test_validation_result_boolean_context(self):
        """Test ValidationResult can be used in boolean context"""
        # Arrange
        valid_result = ValidationResult.success()
        invalid_result = ValidationResult.failure([
            ValidationError(ValidationErrorType.OHLC_INVALID, "Test error")
        ])
        
        # Act & Assert
        assert bool(valid_result) is True
        assert bool(invalid_result) is False
        
        # Can use in if statements
        if valid_result:
            pass  # Should execute
        else:
            pytest.fail("Valid result should be truthy")
        
        if invalid_result:
            pytest.fail("Invalid result should be falsy")


class TestValidateCandleDict:
    """Test suite for validate_candle_dict convenience function"""
    
    def test_valid_candle_dict(self):
        """Test validation passes for valid candle dictionary"""
        # Arrange
        candle = {
            'open': Decimal('150.00'),
            'high': Decimal('155.00'),
            'low': Decimal('149.00'),
            'close': Decimal('154.00'),
            'volume': 1000000,
            'timestamp': datetime.now(timezone.utc) - timedelta(hours=1),
            'timeframe': '1D'
        }
        
        # Act
        result = validate_candle_dict(candle)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_candle_dict(self):
        """Test validation fails for invalid candle dictionary"""
        # Arrange
        candle = {
            'open': Decimal('160.00'),  # Invalid: open > high
            'high': Decimal('155.00'),
            'low': Decimal('149.00'),
            'close': Decimal('154.00'),
            'volume': -1000,  # Invalid: negative volume
            'timestamp': datetime.now(timezone.utc) + timedelta(hours=1),  # Invalid: future
            'timeframe': '1D'
        }
        
        # Act
        result = validate_candle_dict(candle)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) >= 2


class TestValidationErrorDetails:
    """Test suite for validation error details"""
    
    def test_error_contains_field_information(self):
        """Test validation errors include field information"""
        # Arrange & Act
        result = CandleValidator.validate_volume(-1000)
        
        # Assert
        assert result.errors[0].field == "volume"
        assert result.errors[0].value == -1000
    
    def test_error_contains_descriptive_message(self):
        """Test validation errors include descriptive messages"""
        # Arrange & Act
        result = CandleValidator.validate_ohlc(
            Decimal("160.00"),
            Decimal("155.00"),
            Decimal("149.00"),
            Decimal("154.00")
        )
        
        # Assert
        assert len(result.errors) > 0
        assert "Open" in result.errors[0].message
        assert "160" in result.errors[0].message
