#!/usr/bin/env python3
"""
Quick verification script for the validation module.
This script tests basic functionality without requiring pytest.
"""

import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add app to path
sys.path.insert(0, '.')

try:
    from app.services.validation import (
        CandleValidator,
        ValidationResult,
        ValidationError,
        ValidationErrorType,
        validate_candle_dict
    )
    print("✓ Successfully imported validation module")
except ImportError as e:
    print(f"✗ Failed to import validation module: {e}")
    sys.exit(1)

# Test 1: Valid OHLC
print("\nTest 1: Valid OHLC validation")
result = CandleValidator.validate_ohlc(
    Decimal("150.00"),
    Decimal("155.00"),
    Decimal("149.00"),
    Decimal("154.00")
)
assert result.is_valid, "Valid OHLC should pass"
print("✓ Valid OHLC test passed")

# Test 2: Invalid OHLC (high < low)
print("\nTest 2: Invalid OHLC validation (high < low)")
result = CandleValidator.validate_ohlc(
    Decimal("150.00"),
    Decimal("145.00"),  # Invalid: high < low
    Decimal("149.00"),
    Decimal("148.00")
)
assert not result.is_valid, "Invalid OHLC should fail"
assert len(result.errors) > 0, "Should have errors"
print(f"✓ Invalid OHLC test passed - caught {len(result.errors)} error(s)")

# Test 3: Valid volume
print("\nTest 3: Valid volume validation")
result = CandleValidator.validate_volume(1000000)
assert result.is_valid, "Positive volume should pass"
print("✓ Valid volume test passed")

# Test 4: Invalid volume (negative)
print("\nTest 4: Invalid volume validation (negative)")
result = CandleValidator.validate_volume(-1000)
assert not result.is_valid, "Negative volume should fail"
assert result.errors[0].error_type == ValidationErrorType.VOLUME_NEGATIVE
print("✓ Invalid volume test passed")

# Test 5: Valid timestamp (past)
print("\nTest 5: Valid timestamp validation (past)")
past_time = datetime.now(timezone.utc) - timedelta(hours=1)
result = CandleValidator.validate_timestamp(past_time)
assert result.is_valid, "Past timestamp should pass"
print("✓ Valid timestamp test passed")

# Test 6: Invalid timestamp (future)
print("\nTest 6: Invalid timestamp validation (future)")
future_time = datetime.now(timezone.utc) + timedelta(hours=1)
result = CandleValidator.validate_timestamp(future_time)
assert not result.is_valid, "Future timestamp should fail"
assert result.errors[0].error_type == ValidationErrorType.TIMESTAMP_FUTURE
print("✓ Invalid timestamp test passed")

# Test 7: Valid 5m timeframe alignment
print("\nTest 7: Valid 5m timeframe alignment")
aligned_time = datetime(2024, 1, 15, 10, 5, 0)
result = CandleValidator.validate_timeframe_alignment(aligned_time, '5m')
assert result.is_valid, "5m aligned timestamp should pass"
print("✓ Valid 5m alignment test passed")

# Test 8: Invalid 5m timeframe alignment
print("\nTest 8: Invalid 5m timeframe alignment")
misaligned_time = datetime(2024, 1, 15, 10, 7, 0)
result = CandleValidator.validate_timeframe_alignment(misaligned_time, '5m')
assert not result.is_valid, "5m misaligned timestamp should fail"
assert result.errors[0].error_type == ValidationErrorType.TIMEFRAME_MISALIGNMENT
print("✓ Invalid 5m alignment test passed")

# Test 9: Comprehensive validation (valid candle)
print("\nTest 9: Comprehensive validation (valid candle)")
past_time = datetime.now(timezone.utc) - timedelta(hours=1)
result = CandleValidator.validate_candle(
    open_price=Decimal("150.00"),
    high=Decimal("155.00"),
    low=Decimal("149.00"),
    close=Decimal("154.00"),
    volume=1000000,
    timestamp=past_time,
    timeframe='1D'
)
assert result.is_valid, "Valid candle should pass all checks"
print("✓ Comprehensive validation test passed")

# Test 10: Comprehensive validation (multiple errors)
print("\nTest 10: Comprehensive validation (multiple errors)")
future_time = datetime.now(timezone.utc) + timedelta(hours=1)
result = CandleValidator.validate_candle(
    open_price=Decimal("160.00"),  # Invalid: open > high
    high=Decimal("155.00"),
    low=Decimal("149.00"),
    close=Decimal("154.00"),
    volume=-1000,  # Invalid: negative volume
    timestamp=future_time,  # Invalid: future timestamp
    timeframe='1D'
)
assert not result.is_valid, "Invalid candle should fail"
assert len(result.errors) >= 2, "Should have multiple errors"
print(f"✓ Multiple errors test passed - caught {len(result.errors)} error(s)")

# Test 11: validate_candle_dict convenience function
print("\nTest 11: validate_candle_dict convenience function")
candle = {
    'open': Decimal('150.00'),
    'high': Decimal('155.00'),
    'low': Decimal('149.00'),
    'close': Decimal('154.00'),
    'volume': 1000000,
    'timestamp': datetime.now(timezone.utc) - timedelta(hours=1),
    'timeframe': '1D'
}
result = validate_candle_dict(candle)
assert result.is_valid, "Valid candle dict should pass"
print("✓ validate_candle_dict test passed")

# Test 12: ValidationResult boolean context
print("\nTest 12: ValidationResult boolean context")
valid_result = ValidationResult.success()
invalid_result = ValidationResult.failure([
    ValidationError(ValidationErrorType.OHLC_INVALID, "Test error")
])
assert bool(valid_result) is True, "Valid result should be truthy"
assert bool(invalid_result) is False, "Invalid result should be falsy"
print("✓ ValidationResult boolean context test passed")

print("\n" + "="*60)
print("✓ All verification tests passed!")
print("="*60)
print("\nThe validation module is working correctly.")
print("You can now run the full test suite with: pytest tests/test_validation.py")
