"""
Verification script for RSI (Relative Strength Index) indicator.

This script manually tests the RSI implementation with known values
to verify correctness before running the full test suite.

Run this script to verify RSI implementation:
    python verify_rsi.py
"""

from datetime import datetime, timezone
from decimal import Decimal
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.indicators import Candle, RSIIndicator


def create_candle(day: int, close: float) -> Candle:
    """Helper to create a candle with given close price"""
    return Candle(
        timestamp=datetime(2024, 1, day, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('100.00'),
        high=Decimal('110.00'),
        low=Decimal('90.00'),
        close=Decimal(str(close)),
        volume=1000000
    )


def test_rsi_all_gains():
    """Test RSI with all gains (should equal 100)"""
    print("\n" + "="*60)
    print("TEST 1: RSI with all gains (should equal 100)")
    print("="*60)
    
    # Create candles with steadily increasing prices
    candles = []
    for i in range(16):
        candles.append(create_candle(i + 1, 100 + i * 5))
    
    print(f"Created {len(candles)} candles with increasing prices")
    print(f"Closes: {[float(c.close) for c in candles[:5]]}...")
    
    # Compute 14-period RSI
    rsi = RSIIndicator(period=14)
    values = rsi.compute(candles, {'period': 14})
    
    print(f"\nRSI values computed: {len(values)}")
    for i, value in enumerate(values):
        print(f"  Position {i}: RSI = {value.value}")
    
    # Verify all values are 100
    all_100 = all(v.value == Decimal('100') for v in values)
    print(f"\n✓ All values equal 100: {all_100}")
    
    if not all_100:
        print("❌ FAILED: Expected all RSI values to be 100 (all gains)")
        return False
    
    print("✅ PASSED")
    return True


def test_rsi_all_losses():
    """Test RSI with all losses (should equal 0)"""
    print("\n" + "="*60)
    print("TEST 2: RSI with all losses (should equal 0)")
    print("="*60)
    
    # Create candles with steadily decreasing prices
    candles = []
    for i in range(16):
        candles.append(create_candle(i + 1, 100 - i * 2))
    
    print(f"Created {len(candles)} candles with decreasing prices")
    print(f"Closes: {[float(c.close) for c in candles[:5]]}...")
    
    # Compute 14-period RSI
    rsi = RSIIndicator(period=14)
    values = rsi.compute(candles, {'period': 14})
    
    print(f"\nRSI values computed: {len(values)}")
    for i, value in enumerate(values):
        print(f"  Position {i}: RSI = {value.value}")
    
    # Verify all values are 0
    all_0 = all(v.value == Decimal('0') for v in values)
    print(f"\n✓ All values equal 0: {all_0}")
    
    if not all_0:
        print("❌ FAILED: Expected all RSI values to be 0 (all losses)")
        return False
    
    print("✅ PASSED")
    return True


def test_rsi_simple_calculation():
    """Test RSI with simple known values"""
    print("\n" + "="*60)
    print("TEST 3: RSI with simple known values")
    print("="*60)
    
    # Create a simple scenario
    # Closes: 100, 102, 101, 103, 102
    # Changes: +2, -1, +2, -1
    closes = [100, 102, 101, 103, 102]
    candles = [create_candle(i + 1, close) for i, close in enumerate(closes)]
    
    print(f"Closes: {closes}")
    print(f"Changes: +2, -1, +2, -1")
    
    # Compute 3-period RSI
    rsi = RSIIndicator(period=3)
    values = rsi.compute(candles, {'period': 3})
    
    print(f"\nRSI values computed: {len(values)}")
    for i, value in enumerate(values):
        print(f"  Position {i}: RSI = {value.value}")
    
    # Manual calculation:
    # First 3 changes: +2, -1, +2
    # Avg gain = (2 + 0 + 2) / 3 = 4/3
    # Avg loss = (0 + 1 + 0) / 3 = 1/3
    # RS = (4/3) / (1/3) = 4
    # RSI = 100 - 100/(1+4) = 100 - 20 = 80
    expected = Decimal('80')
    
    print(f"\nExpected RSI: {expected}")
    print(f"Actual RSI: {values[0].value}")
    
    if values[0].value != expected:
        print(f"❌ FAILED: Expected {expected}, got {values[0].value}")
        return False
    
    print("✅ PASSED")
    return True


def test_rsi_range_invariant():
    """Test RSI values are always in range [0, 100]"""
    print("\n" + "="*60)
    print("TEST 4: RSI range invariant [0, 100]")
    print("="*60)
    
    # Create candles with varying prices
    closes = [
        100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
        105, 107, 106, 108, 107, 109, 108, 110, 109, 111
    ]
    candles = [create_candle(i + 1, close) for i, close in enumerate(closes)]
    
    print(f"Created {len(candles)} candles with varying prices")
    
    # Compute 14-period RSI
    rsi = RSIIndicator(period=14)
    values = rsi.compute(candles, {'period': 14})
    
    print(f"\nRSI values computed: {len(values)}")
    
    # Check all values are in range
    all_in_range = True
    for i, value in enumerate(values):
        in_range = Decimal('0') <= value.value <= Decimal('100')
        print(f"  Position {i}: RSI = {value.value} (in range: {in_range})")
        if not in_range:
            all_in_range = False
    
    if not all_in_range:
        print("❌ FAILED: Some RSI values are outside [0, 100] range")
        return False
    
    print("\n✅ PASSED: All RSI values in range [0, 100]")
    return True


def test_rsi_required_periods():
    """Test RSI requires period + 1 candles"""
    print("\n" + "="*60)
    print("TEST 5: RSI required periods (period + 1)")
    print("="*60)
    
    rsi = RSIIndicator(period=14)
    required = rsi.required_periods({'period': 14})
    
    print(f"Period: 14")
    print(f"Required candles: {required}")
    print(f"Expected: 15 (period + 1)")
    
    if required != 15:
        print(f"❌ FAILED: Expected 15, got {required}")
        return False
    
    print("✅ PASSED")
    return True


def test_rsi_insufficient_data():
    """Test RSI raises error with insufficient data"""
    print("\n" + "="*60)
    print("TEST 6: RSI with insufficient data (should raise error)")
    print("="*60)
    
    # Create only 10 candles (need 15 for period=14)
    candles = [create_candle(i + 1, 100 + i) for i in range(10)]
    
    print(f"Created {len(candles)} candles")
    print(f"Attempting to compute 14-period RSI (needs 15 candles)")
    
    rsi = RSIIndicator(period=14)
    
    try:
        values = rsi.compute(candles, {'period': 14})
        print("❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✓ Raised ValueError as expected: {e}")
        print("✅ PASSED")
        return True


def test_rsi_name():
    """Test RSI indicator name"""
    print("\n" + "="*60)
    print("TEST 7: RSI indicator name")
    print("="*60)
    
    rsi_14 = RSIIndicator(period=14)
    rsi_20 = RSIIndicator(period=20)
    
    print(f"RSI(14) name: {rsi_14.name}")
    print(f"RSI(20) name: {rsi_20.name}")
    
    if rsi_14.name != "RSI_14" or rsi_20.name != "RSI_20":
        print("❌ FAILED: Incorrect indicator names")
        return False
    
    print("✅ PASSED")
    return True


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("RSI INDICATOR VERIFICATION")
    print("="*60)
    
    tests = [
        test_rsi_name,
        test_rsi_required_periods,
        test_rsi_all_gains,
        test_rsi_all_losses,
        test_rsi_simple_calculation,
        test_rsi_range_invariant,
        test_rsi_insufficient_data,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
