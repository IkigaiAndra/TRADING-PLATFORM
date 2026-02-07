"""
Verification script for EMA (Exponential Moving Average) indicator.

This script tests the EMA implementation with known values to ensure correctness.
"""

from datetime import datetime, timezone
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.indicators import Candle, EMAIndicator


def create_test_candles(closes):
    """Create test candles with given close prices"""
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
    return candles


def test_ema_basic():
    """Test EMA with simple known values"""
    print("Test 1: EMA with simple known values")
    print("-" * 50)
    
    # Create 5 candles with closes: 10, 20, 30, 40, 50
    candles = create_test_candles([10, 20, 30, 40, 50])
    
    # Compute 3-period EMA
    # α = 2 / (3 + 1) = 0.5
    ema = EMAIndicator(period=3)
    values = ema.compute(candles, {'period': 3})
    
    print(f"Number of values: {len(values)} (expected: 3)")
    assert len(values) == 3, "Should have 3 values"
    
    # EMA at position 2: SMA(10, 20, 30) = 20
    print(f"First EMA value: {values[0].value} (expected: 20)")
    assert values[0].value == Decimal('20'), "First value should be 20"
    
    # EMA at position 3: 0.5 * 40 + 0.5 * 20 = 30
    print(f"Second EMA value: {values[1].value} (expected: 30)")
    assert values[1].value == Decimal('30'), "Second value should be 30"
    
    # EMA at position 4: 0.5 * 50 + 0.5 * 30 = 40
    print(f"Third EMA value: {values[2].value} (expected: 40)")
    assert values[2].value == Decimal('40'), "Third value should be 40"
    
    print("✅ Test 1 passed!\n")


def test_ema_first_value_is_sma():
    """Test that first EMA value equals SMA"""
    print("Test 2: First EMA value equals SMA")
    print("-" * 50)
    
    closes = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
    candles = create_test_candles(closes)
    
    # Compute 5-period EMA
    ema = EMAIndicator(period=5)
    ema_values = ema.compute(candles, {'period': 5})
    
    # First EMA value should equal SMA of first 5 closes
    expected_sma = sum(Decimal(str(c)) for c in closes[:5]) / Decimal('5')
    print(f"First EMA value: {ema_values[0].value}")
    print(f"Expected SMA: {expected_sma}")
    assert ema_values[0].value == expected_sma, "First EMA should equal SMA"
    
    print("✅ Test 2 passed!\n")


def test_ema_recursive_formula():
    """Test EMA recursive formula verification"""
    print("Test 3: EMA recursive formula verification")
    print("-" * 50)
    
    closes = [100, 105, 110, 115, 120, 125]
    candles = create_test_candles(closes)
    
    # Compute 3-period EMA
    # α = 2 / (3 + 1) = 0.5
    ema = EMAIndicator(period=3)
    values = ema.compute(candles, {'period': 3})
    
    alpha = Decimal('2') / Decimal('4')  # 0.5
    print(f"Smoothing factor α: {alpha}")
    
    # First value: SMA(100, 105, 110) = 105
    expected_0 = (Decimal('100') + Decimal('105') + Decimal('110')) / Decimal('3')
    print(f"EMA[0]: {values[0].value} (expected: {expected_0})")
    assert values[0].value == expected_0
    
    # Second value: 0.5 * 115 + 0.5 * 105 = 110
    expected_1 = alpha * Decimal('115') + (Decimal('1') - alpha) * expected_0
    print(f"EMA[1]: {values[1].value} (expected: {expected_1})")
    assert values[1].value == expected_1
    
    # Third value: 0.5 * 120 + 0.5 * 110 = 115
    expected_2 = alpha * Decimal('120') + (Decimal('1') - alpha) * expected_1
    print(f"EMA[2]: {values[2].value} (expected: {expected_2})")
    assert values[2].value == expected_2
    
    # Fourth value: 0.5 * 125 + 0.5 * 115 = 120
    expected_3 = alpha * Decimal('125') + (Decimal('1') - alpha) * expected_2
    print(f"EMA[3]: {values[3].value} (expected: {expected_3})")
    assert values[3].value == expected_3
    
    print("✅ Test 3 passed!\n")


def test_ema_realistic_data():
    """Test EMA with realistic price data"""
    print("Test 4: EMA with realistic price data")
    print("-" * 50)
    
    closes = [
        150.00, 151.50, 149.75, 152.25, 153.00,
        154.50, 153.75, 155.00, 156.25, 155.50,
        157.00, 158.25, 157.50, 159.00, 160.25,
        159.50, 161.00, 162.25, 161.50, 163.00,
        164.25, 163.50, 165.00, 166.25, 165.50
    ]
    
    candles = create_test_candles(closes)
    
    # Compute 12-period EMA
    ema = EMAIndicator(period=12)
    values = ema.compute(candles, {'period': 12})
    
    print(f"Number of values: {len(values)} (expected: 14)")
    assert len(values) == 14, "Should have 14 values"
    
    # Verify first EMA value equals SMA of first 12 closes
    expected_first = sum(Decimal(str(c)) for c in closes[:12]) / Decimal('12')
    print(f"First EMA value: {values[0].value}")
    print(f"Expected SMA: {expected_first}")
    assert values[0].value == expected_first
    
    # Verify EMA values are monotonically increasing (since prices trend up)
    print("Checking monotonic increase...")
    for i in range(1, len(values)):
        assert values[i].value > values[i-1].value, f"EMA should increase at position {i}"
    
    print(f"Last EMA value: {values[-1].value}")
    print("✅ Test 4 passed!\n")


def test_ema_period_1():
    """Test EMA with period=1"""
    print("Test 5: EMA with period=1")
    print("-" * 50)
    
    candles = create_test_candles([100, 110, 120, 130, 140])
    
    # EMA with period=1: α = 2/(1+1) = 1.0
    # So EMA(i) = 1.0 * close(i) + 0.0 * EMA(i-1) = close(i)
    ema = EMAIndicator(period=1)
    values = ema.compute(candles, {'period': 1})
    
    print(f"Number of values: {len(values)} (expected: 5)")
    assert len(values) == 5
    
    # First value is SMA of first candle = close price
    print(f"First value: {values[0].value} (expected: {candles[0].close})")
    assert values[0].value == candles[0].close
    
    # All subsequent values should equal close price (α = 1.0)
    for i in range(1, len(values)):
        print(f"Value[{i}]: {values[i].value} (expected: {candles[i].close})")
        assert values[i].value == candles[i].close
    
    print("✅ Test 5 passed!\n")


def test_ema_error_handling():
    """Test EMA error handling"""
    print("Test 6: EMA error handling")
    print("-" * 50)
    
    # Test insufficient data
    candles = create_test_candles([100, 110, 120])
    ema = EMAIndicator(period=5)
    
    try:
        ema.compute(candles, {'period': 5})
        print("❌ Should have raised ValueError for insufficient data")
        assert False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    
    # Test missing period parameter
    candles = create_test_candles([100, 110, 120, 130, 140])
    try:
        ema.compute(candles, {})
        print("❌ Should have raised ValueError for missing period")
        assert False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    
    print("✅ Test 6 passed!\n")


def main():
    """Run all verification tests"""
    print("=" * 50)
    print("EMA Indicator Verification")
    print("=" * 50)
    print()
    
    try:
        test_ema_basic()
        test_ema_first_value_is_sma()
        test_ema_recursive_formula()
        test_ema_realistic_data()
        test_ema_period_1()
        test_ema_error_handling()
        
        print("=" * 50)
        print("✅ All EMA verification tests passed!")
        print("=" * 50)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
