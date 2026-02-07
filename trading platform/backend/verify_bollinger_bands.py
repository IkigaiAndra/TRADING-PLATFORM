"""
Verification script for Bollinger Bands indicator implementation.

This script manually tests the Bollinger Bands indicator to verify:
1. Basic computation correctness
2. Ordering invariant (lower < middle < upper)
3. Middle band equals SMA
4. Metadata structure
5. Parameter validation
6. Edge cases

Run this script to verify the implementation before running full test suite.
"""

from datetime import datetime, timezone
from decimal import Decimal
from app.services.indicators import (
    Candle,
    BollingerBandsIndicator,
    SMAIndicator
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_basic_computation():
    """Test basic Bollinger Bands computation"""
    print_section("Test 1: Basic Computation")
    
    # Create 25 candles with varying prices
    candles = []
    for i in range(25):
        close = Decimal(str(100 + i * 2))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    # Compute Bollinger Bands
    bb = BollingerBandsIndicator(period=20, std_dev=2.0)
    values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
    
    print(f"✓ Created {len(candles)} candles")
    print(f"✓ Computed {len(values)} Bollinger Bands values")
    print(f"✓ Expected: {len(candles) - 20 + 1} = 6 values")
    
    assert len(values) == 6, f"Expected 6 values, got {len(values)}"
    
    # Display first and last values
    first = values[0]
    last = values[-1]
    
    print(f"\nFirst value (timestamp: {first.timestamp}):")
    print(f"  Middle Band: {first.value}")
    print(f"  Upper Band:  {first.metadata['upper_band']}")
    print(f"  Lower Band:  {first.metadata['lower_band']}")
    print(f"  Bandwidth:   {first.metadata['bandwidth']}")
    
    print(f"\nLast value (timestamp: {last.timestamp}):")
    print(f"  Middle Band: {last.value}")
    print(f"  Upper Band:  {last.metadata['upper_band']}")
    print(f"  Lower Band:  {last.metadata['lower_band']}")
    print(f"  Bandwidth:   {last.metadata['bandwidth']}")
    
    print("\n✅ Basic computation test PASSED")


def test_ordering_invariant():
    """Test that lower < middle < upper always holds"""
    print_section("Test 2: Ordering Invariant")
    
    # Create 25 candles with oscillating prices
    candles = []
    for i in range(25):
        close = Decimal(str(100 + (i % 10) * 5))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    bb = BollingerBandsIndicator(period=20, std_dev=2.0)
    values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
    
    print(f"✓ Testing ordering invariant on {len(values)} values")
    
    all_valid = True
    for i, value in enumerate(values):
        middle = float(value.value)
        upper = value.metadata['upper_band']
        lower = value.metadata['lower_band']
        
        if not (lower < middle < upper):
            print(f"✗ Ordering violation at index {i}:")
            print(f"  Lower: {lower}, Middle: {middle}, Upper: {upper}")
            all_valid = False
        else:
            print(f"  Value {i}: {lower:.2f} < {middle:.2f} < {upper:.2f} ✓")
    
    assert all_valid, "Ordering invariant violated!"
    print("\n✅ Ordering invariant test PASSED")


def test_middle_band_equals_sma():
    """Test that middle band equals SMA with same period"""
    print_section("Test 3: Middle Band = SMA")
    
    # Create 25 candles
    candles = []
    for i in range(25):
        close = Decimal(str(100 + i * 2))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    # Compute Bollinger Bands
    bb = BollingerBandsIndicator(period=20, std_dev=2.0)
    bb_values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
    
    # Compute SMA with same period
    sma = SMAIndicator(period=20)
    sma_values = sma.compute(candles, {'period': 20})
    
    print(f"✓ Computed {len(bb_values)} BB values and {len(sma_values)} SMA values")
    
    assert len(bb_values) == len(sma_values), "Length mismatch!"
    
    all_match = True
    for i, (bb_val, sma_val) in enumerate(zip(bb_values, sma_values)):
        if bb_val.timestamp != sma_val.timestamp:
            print(f"✗ Timestamp mismatch at index {i}")
            all_match = False
        elif bb_val.value != sma_val.value:
            print(f"✗ Value mismatch at index {i}:")
            print(f"  BB middle: {bb_val.value}, SMA: {sma_val.value}")
            all_match = False
        else:
            print(f"  Value {i}: BB={bb_val.value} == SMA={sma_val.value} ✓")
    
    assert all_match, "Middle band does not equal SMA!"
    print("\n✅ Middle band = SMA test PASSED")


def test_parameter_validation():
    """Test parameter validation"""
    print_section("Test 4: Parameter Validation")
    
    candles = []
    for i in range(25):
        close = Decimal(str(100 + i))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    bb = BollingerBandsIndicator()
    
    # Test missing period
    try:
        bb.compute(candles, {'std_dev': 2.0})
        print("✗ Should have raised error for missing period")
        assert False
    except ValueError as e:
        print(f"✓ Missing period error: {e}")
    
    # Test missing std_dev
    try:
        bb.compute(candles, {'period': 20})
        print("✗ Should have raised error for missing std_dev")
        assert False
    except ValueError as e:
        print(f"✓ Missing std_dev error: {e}")
    
    # Test invalid period
    try:
        bb.compute(candles, {'period': 0, 'std_dev': 2.0})
        print("✗ Should have raised error for invalid period")
        assert False
    except ValueError as e:
        print(f"✓ Invalid period error: {e}")
    
    # Test invalid std_dev
    try:
        bb.compute(candles, {'period': 20, 'std_dev': -1.0})
        print("✗ Should have raised error for invalid std_dev")
        assert False
    except ValueError as e:
        print(f"✓ Invalid std_dev error: {e}")
    
    print("\n✅ Parameter validation test PASSED")


def test_insufficient_data():
    """Test error handling with insufficient data"""
    print_section("Test 5: Insufficient Data")
    
    # Only 15 candles, but need 20
    candles = []
    for i in range(15):
        close = Decimal(str(100 + i))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('2'),
            low=close - Decimal('2'),
            close=close,
            volume=1000000
        ))
    
    bb = BollingerBandsIndicator(period=20, std_dev=2.0)
    
    try:
        bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        print("✗ Should have raised error for insufficient data")
        assert False
    except ValueError as e:
        print(f"✓ Insufficient data error: {e}")
    
    print("\n✅ Insufficient data test PASSED")


def test_exact_computation():
    """Test exact computation with known values"""
    print_section("Test 6: Exact Computation")
    
    # Create 5 candles with known values
    # Closes: [100, 102, 104, 103, 105]
    candles = [
        Candle(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('99'), high=Decimal('101'), low=Decimal('98'),
            close=Decimal('100'), volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('101'), high=Decimal('103'), low=Decimal('100'),
            close=Decimal('102'), volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('103'), high=Decimal('105'), low=Decimal('102'),
            close=Decimal('104'), volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 4, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('104'), high=Decimal('105'), low=Decimal('102'),
            close=Decimal('103'), volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('104'), high=Decimal('106'), low=Decimal('103'),
            close=Decimal('105'), volume=1000000
        ),
    ]
    
    # Compute with period=5, std_dev=2.0
    bb = BollingerBandsIndicator(period=5, std_dev=2.0)
    values = bb.compute(candles, {'period': 5, 'std_dev': 2.0})
    
    print(f"✓ Computed {len(values)} value(s)")
    assert len(values) == 1, f"Expected 1 value, got {len(values)}"
    
    # Calculate expected values manually
    # Mean = (100 + 102 + 104 + 103 + 105) / 5 = 514 / 5 = 102.8
    expected_middle = Decimal('102.8')
    
    # Variance = [(100-102.8)^2 + (102-102.8)^2 + (104-102.8)^2 + (103-102.8)^2 + (105-102.8)^2] / 5
    #          = [7.84 + 0.64 + 1.44 + 0.04 + 4.84] / 5
    #          = 14.8 / 5 = 2.96
    # Std Dev = sqrt(2.96) ≈ 1.72047
    # Upper = 102.8 + 2.0 * 1.72047 ≈ 106.24
    # Lower = 102.8 - 2.0 * 1.72047 ≈ 99.36
    
    value = values[0]
    
    print(f"\nComputed values:")
    print(f"  Middle Band: {value.value}")
    print(f"  Upper Band:  {value.metadata['upper_band']}")
    print(f"  Lower Band:  {value.metadata['lower_band']}")
    
    print(f"\nExpected values:")
    print(f"  Middle Band: {expected_middle}")
    print(f"  Upper Band:  ~106.24")
    print(f"  Lower Band:  ~99.36")
    
    # Check middle band
    assert abs(value.value - expected_middle) < Decimal('0.01'), \
        f"Middle band mismatch: {value.value} vs {expected_middle}"
    print(f"✓ Middle band matches expected value")
    
    # Check upper and lower bands are in reasonable range
    assert 105 < value.metadata['upper_band'] < 107, \
        f"Upper band out of range: {value.metadata['upper_band']}"
    print(f"✓ Upper band in expected range")
    
    assert 98 < value.metadata['lower_band'] < 100, \
        f"Lower band out of range: {value.metadata['lower_band']}"
    print(f"✓ Lower band in expected range")
    
    print("\n✅ Exact computation test PASSED")


def main():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("  Bollinger Bands Indicator Verification")
    print("=" * 60)
    
    try:
        test_basic_computation()
        test_ordering_invariant()
        test_middle_band_equals_sma()
        test_parameter_validation()
        test_insufficient_data()
        test_exact_computation()
        
        print("\n" + "=" * 60)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe Bollinger Bands indicator implementation is correct.")
        print("You can now run the full test suite with:")
        print("  pytest tests/test_indicators.py::TestBollingerBandsIndicator -v")
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("  ❌ TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print("  ❌ UNEXPECTED ERROR!")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
