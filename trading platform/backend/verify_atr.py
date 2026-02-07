"""
Verification script for ATR (Average True Range) indicator.

This script demonstrates the ATR indicator implementation with various
test scenarios to verify correctness.

Run this script to manually verify ATR computation:
    python verify_atr.py
"""

from datetime import datetime, timezone
from decimal import Decimal
from app.services.indicators import Candle, ATRIndicator


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_candle(candle: Candle, index: int):
    """Print candle details"""
    print(f"Candle {index}: {candle.timestamp.date()} | "
          f"O:{candle.open:7.2f} H:{candle.high:7.2f} "
          f"L:{candle.low:7.2f} C:{candle.close:7.2f} V:{candle.volume}")


def print_atr_value(value, index: int):
    """Print ATR value details"""
    tr = value.metadata.get('true_range', 0) if value.metadata else 0
    print(f"ATR {index}: {value.timestamp.date()} | "
          f"ATR: {value.value:7.4f} | TR: {tr:7.4f}")


def test_basic_atr():
    """Test basic ATR computation with constant range"""
    print_section("Test 1: Basic ATR with Constant Range")
    
    # Create 20 candles with constant range of 10
    candles = []
    for i in range(20):
        close = Decimal('100.00')
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close,
            high=close + Decimal('5'),  # Range of 10
            low=close - Decimal('5'),
            close=close,
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with constant range of 10")
    print("First 3 candles:")
    for i in range(3):
        print_candle(candles[i], i)
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    print("All ATR values:")
    for i, value in enumerate(values):
        print_atr_value(value, i)
    
    print(f"\nExpected: ATR should be close to 10 (the constant range)")
    print(f"Actual: ATR values range from {min(v.value for v in values):.4f} to {max(v.value for v in values):.4f}")


def test_gap_up():
    """Test ATR with gap up scenario"""
    print_section("Test 2: ATR with Gap Up")
    
    candles = []
    
    # First candle: close = 100
    candles.append(Candle(
        timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('100.00'),
        high=Decimal('102.00'),
        low=Decimal('98.00'),
        close=Decimal('100.00'),
        volume=1000000
    ))
    
    # Gap up: previous close = 100, current high = 115, low = 110
    # TR = max(115-110=5, |115-100|=15, |110-100|=10) = 15
    candles.append(Candle(
        timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('112.00'),
        high=Decimal('115.00'),
        low=Decimal('110.00'),
        close=Decimal('113.00'),
        volume=1000000
    ))
    
    # Add more candles with normal ranges
    for i in range(2, 20):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('113.00'),
            high=Decimal('115.00'),
            low=Decimal('111.00'),
            close=Decimal('113.00'),
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with gap up on day 2")
    print("First 3 candles:")
    for i in range(3):
        print_candle(candles[i], i)
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    print("All ATR values:")
    for i, value in enumerate(values):
        print_atr_value(value, i)
    
    print(f"\nNote: Gap up on day 2 should increase true range to 15")
    print(f"ATR should reflect this increased volatility")


def test_gap_down():
    """Test ATR with gap down scenario"""
    print_section("Test 3: ATR with Gap Down")
    
    candles = []
    
    # First candle: close = 100
    candles.append(Candle(
        timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('100.00'),
        high=Decimal('102.00'),
        low=Decimal('98.00'),
        close=Decimal('100.00'),
        volume=1000000
    ))
    
    # Gap down: previous close = 100, current high = 90, low = 85
    # TR = max(90-85=5, |90-100|=10, |85-100|=15) = 15
    candles.append(Candle(
        timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('88.00'),
        high=Decimal('90.00'),
        low=Decimal('85.00'),
        close=Decimal('87.00'),
        volume=1000000
    ))
    
    # Add more candles with normal ranges
    for i in range(2, 20):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('87.00'),
            high=Decimal('89.00'),
            low=Decimal('85.00'),
            close=Decimal('87.00'),
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with gap down on day 2")
    print("First 3 candles:")
    for i in range(3):
        print_candle(candles[i], i)
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    print("All ATR values:")
    for i, value in enumerate(values):
        print_atr_value(value, i)
    
    print(f"\nNote: Gap down on day 2 should increase true range to 15")
    print(f"ATR should reflect this increased volatility")


def test_zero_volatility():
    """Test ATR with zero volatility"""
    print_section("Test 4: ATR with Zero Volatility")
    
    # Create candles with zero range (all OHLC equal)
    candles = []
    for i in range(20):
        price = Decimal('100.00')
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with zero volatility (all OHLC = 100)")
    print("First 3 candles:")
    for i in range(3):
        print_candle(candles[i], i)
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    print("All ATR values:")
    for i, value in enumerate(values):
        print_atr_value(value, i)
    
    print(f"\nExpected: ATR should be 0 with zero volatility")
    print(f"Actual: All ATR values are {values[0].value}")


def test_increasing_volatility():
    """Test ATR with increasing volatility"""
    print_section("Test 5: ATR with Increasing Volatility")
    
    # Create candles with increasing range
    candles = []
    for i in range(25):
        range_size = Decimal(str(5 + i * 0.5))  # Increasing range
        close = Decimal('100.00')
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close,
            high=close + range_size,
            low=close - range_size,
            close=close,
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with increasing range")
    print("First 3 candles:")
    for i in range(3):
        print_candle(candles[i], i)
    print("Last 3 candles:")
    for i in range(22, 25):
        print_candle(candles[i], i)
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    print("First 3 ATR values:")
    for i in range(3):
        print_atr_value(values[i], i)
    print("Last 3 ATR values:")
    for i in range(len(values) - 3, len(values)):
        print_atr_value(values[i], i)
    
    print(f"\nExpected: ATR should increase as volatility increases")
    print(f"First ATR: {values[0].value:.4f}, Last ATR: {values[-1].value:.4f}")
    print(f"Change: {values[-1].value - values[0].value:+.4f}")


def test_different_periods():
    """Test ATR with different period parameters"""
    print_section("Test 6: ATR with Different Periods")
    
    # Create 30 candles
    candles = []
    for i in range(30):
        close = Decimal(str(100 + (i % 10) * 2))
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('3'),
            low=close - Decimal('3'),
            close=close,
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with oscillating prices")
    
    # Test with period=10
    atr_10 = ATRIndicator(period=10)
    values_10 = atr_10.compute(candles, {'period': 10})
    
    print(f"\nATR with period=10: {len(values_10)} values")
    print("First 3 values:")
    for i in range(3):
        print_atr_value(values_10[i], i)
    
    # Test with period=20
    atr_20 = ATRIndicator(period=20)
    values_20 = atr_20.compute(candles, {'period': 20})
    
    print(f"\nATR with period=20: {len(values_20)} values")
    print("First 3 values:")
    for i in range(3):
        print_atr_value(values_20[i], i)
    
    print(f"\nNote: Shorter period (10) produces more values and may be more responsive")
    print(f"Longer period (20) produces fewer values and is more smoothed")


def test_non_negativity():
    """Test that ATR is always non-negative"""
    print_section("Test 7: ATR Non-Negativity Invariant")
    
    # Create candles with varying prices
    candles = []
    for i in range(25):
        close = Decimal(str(100 + (i % 10) * 5))  # Oscillating prices
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=close - Decimal('1'),
            high=close + Decimal('3'),
            low=close - Decimal('3'),
            close=close,
            volume=1000000
        ))
    
    print(f"\nCreated {len(candles)} candles with oscillating prices")
    
    # Compute ATR
    atr = ATRIndicator(period=14)
    values = atr.compute(candles, {'period': 14})
    
    print(f"\nComputed {len(values)} ATR values (period=14)")
    
    # Check non-negativity
    all_non_negative = all(v.value >= Decimal('0') for v in values)
    min_value = min(v.value for v in values)
    max_value = max(v.value for v in values)
    
    print(f"\nNon-negativity check: {'PASS' if all_non_negative else 'FAIL'}")
    print(f"Min ATR: {min_value:.4f}")
    print(f"Max ATR: {max_value:.4f}")
    print(f"All values >= 0: {all_non_negative}")


def main():
    """Run all verification tests"""
    print("\n" + "=" * 80)
    print("  ATR (Average True Range) Indicator Verification")
    print("=" * 80)
    
    try:
        test_basic_atr()
        test_gap_up()
        test_gap_down()
        test_zero_volatility()
        test_increasing_volatility()
        test_different_periods()
        test_non_negativity()
        
        print("\n" + "=" * 80)
        print("  All verification tests completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
