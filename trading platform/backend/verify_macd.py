"""
Verification script for MACD indicator implementation.

This script manually tests the MACD indicator with known inputs
to verify correctness before running the full test suite.
"""

from datetime import datetime, timezone
from decimal import Decimal
from app.services.indicators import Candle, MACDIndicator


def test_macd_basic():
    """Test MACD with basic uptrend data"""
    print("=" * 60)
    print("Test 1: MACD with basic uptrend")
    print("=" * 60)
    
    # Create 40 candles with steadily increasing prices
    candles = []
    for i in range(40):
        close = Decimal(str(100 + i * 2))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    # Compute MACD with standard parameters
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    print(f"Indicator name: {macd.name}")
    print(f"Required periods: {macd.required_periods({'fast': 12, 'slow': 26, 'signal': 9})}")
    
    values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
    
    print(f"\nNumber of values computed: {len(values)}")
    print(f"Expected: {40 - 34 + 1} = 7 values")
    
    print("\nFirst 3 MACD values:")
    for i, value in enumerate(values[:3]):
        print(f"  [{i}] Timestamp: {value.timestamp}")
        print(f"      MACD: {value.value}")
        print(f"      Signal: {value.metadata['signal_line']}")
        print(f"      Histogram: {value.metadata['histogram']}")
        print()
    
    # Verify all MACD values are positive in uptrend
    all_positive = all(v.value > Decimal('0') for v in values)
    print(f"All MACD values positive (expected in uptrend): {all_positive}")
    
    if all_positive:
        print("✅ Test 1 PASSED")
    else:
        print("❌ Test 1 FAILED")
    
    return all_positive


def test_macd_downtrend():
    """Test MACD with downtrend data"""
    print("\n" + "=" * 60)
    print("Test 2: MACD with downtrend")
    print("=" * 60)
    
    # Create 40 candles with steadily decreasing prices
    candles = []
    for i in range(40):
        close = Decimal(str(200 - i * 2))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close + Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    # Compute MACD
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
    
    print(f"Number of values computed: {len(values)}")
    
    print("\nFirst 3 MACD values:")
    for i, value in enumerate(values[:3]):
        print(f"  [{i}] MACD: {value.value}, Signal: {value.metadata['signal_line']}, Histogram: {value.metadata['histogram']}")
    
    # Verify all MACD values are negative in downtrend
    all_negative = all(v.value < Decimal('0') for v in values)
    print(f"\nAll MACD values negative (expected in downtrend): {all_negative}")
    
    if all_negative:
        print("✅ Test 2 PASSED")
    else:
        print("❌ Test 2 FAILED")
    
    return all_negative


def test_macd_flat_prices():
    """Test MACD with flat prices"""
    print("\n" + "=" * 60)
    print("Test 3: MACD with flat prices")
    print("=" * 60)
    
    # Create 40 candles with constant price
    candles = []
    for i in range(40):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('100.00'),
            low=Decimal('100.00'),
            close=Decimal('100.00'),
            volume=1000000
        ))
    
    # Compute MACD
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
    
    print(f"Number of values computed: {len(values)}")
    
    print("\nFirst 3 MACD values:")
    for i, value in enumerate(values[:3]):
        print(f"  [{i}] MACD: {value.value}, Signal: {value.metadata['signal_line']}, Histogram: {value.metadata['histogram']}")
    
    # Verify all values are zero
    all_zero = all(v.value == Decimal('0') and v.metadata['signal_line'] == 0.0 and v.metadata['histogram'] == 0.0 for v in values)
    print(f"\nAll values zero (expected with flat prices): {all_zero}")
    
    if all_zero:
        print("✅ Test 3 PASSED")
    else:
        print("❌ Test 3 FAILED")
    
    return all_zero


def test_macd_histogram():
    """Test MACD histogram calculation"""
    print("\n" + "=" * 60)
    print("Test 4: MACD histogram calculation")
    print("=" * 60)
    
    # Create 50 candles with varying prices
    closes = [
        100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
        111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
        119, 121, 123, 122, 124, 126, 125, 127, 129, 128,
        130, 132, 131, 133, 135, 134, 136, 138, 137, 139,
        141, 140, 142, 144, 143, 145, 147, 146, 148, 150
    ]
    
    candles = []
    for i, close in enumerate(closes):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal(str(close - 1)),
            high=Decimal(str(close + 2)),
            low=Decimal(str(close - 2)),
            close=Decimal(str(close)),
            volume=1000000
        ))
    
    # Compute MACD
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
    
    print(f"Number of values computed: {len(values)}")
    
    # Verify histogram calculation for all values
    all_correct = True
    for i, value in enumerate(values):
        macd_value = float(value.value)
        signal_value = value.metadata['signal_line']
        histogram_value = value.metadata['histogram']
        
        expected_histogram = macd_value - signal_value
        diff = abs(histogram_value - expected_histogram)
        
        if i < 3:  # Print first 3
            print(f"\n  [{i}] MACD: {macd_value:.6f}")
            print(f"      Signal: {signal_value:.6f}")
            print(f"      Histogram: {histogram_value:.6f}")
            print(f"      Expected: {expected_histogram:.6f}")
            print(f"      Difference: {diff:.10f}")
        
        if diff >= 0.0001:
            all_correct = False
            print(f"❌ Histogram mismatch at index {i}")
    
    print(f"\nAll histogram calculations correct: {all_correct}")
    
    if all_correct:
        print("✅ Test 4 PASSED")
    else:
        print("❌ Test 4 FAILED")
    
    return all_correct


def test_macd_parameter_validation():
    """Test MACD parameter validation"""
    print("\n" + "=" * 60)
    print("Test 5: MACD parameter validation")
    print("=" * 60)
    
    # Create test candles
    candles = []
    for i in range(40):
        close = Decimal(str(100 + i))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    macd = MACDIndicator()
    
    # Test 1: fast >= slow should fail
    try:
        macd.compute(candles, {'fast': 26, 'slow': 12, 'signal': 9})
        print("❌ Should have raised error for fast >= slow")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised error for fast >= slow: {e}")
    
    # Test 2: missing parameter should fail
    try:
        macd.compute(candles, {'fast': 12, 'slow': 26})
        print("❌ Should have raised error for missing signal")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised error for missing signal: {e}")
    
    # Test 3: insufficient data should fail
    short_candles = candles[:30]  # Only 30, need 34
    try:
        macd.compute(short_candles, {'fast': 12, 'slow': 26, 'signal': 9})
        print("❌ Should have raised error for insufficient data")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised error for insufficient data: {e}")
    
    print("✅ Test 5 PASSED")
    return True


def main():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("MACD Indicator Verification")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Basic uptrend", test_macd_basic()))
        results.append(("Downtrend", test_macd_downtrend()))
        results.append(("Flat prices", test_macd_flat_prices()))
        results.append(("Histogram calculation", test_macd_histogram()))
        results.append(("Parameter validation", test_macd_parameter_validation()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
