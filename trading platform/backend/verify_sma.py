#!/usr/bin/env python3
"""
Verification script for SMA indicator implementation.

This script tests the SMA indicator implementation without requiring
a full test environment setup.
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.indicators import Candle, SMAIndicator


def test_sma_basic():
    """Test basic SMA computation"""
    print("Testing basic SMA computation...")
    
    # Create 5 candles with closes: 10, 20, 30, 40, 50
    candles = []
    for i in range(5):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal(str(10 * (i + 1))),
            volume=1000000
        ))
    
    # Compute 3-period SMA
    sma = SMAIndicator(period=3)
    values = sma.compute(candles, {'period': 3})
    
    # Verify results
    assert len(values) == 3, f"Expected 3 values, got {len(values)}"
    assert values[0].value == Decimal('20'), f"Expected 20, got {values[0].value}"
    assert values[1].value == Decimal('30'), f"Expected 30, got {values[1].value}"
    assert values[2].value == Decimal('40'), f"Expected 40, got {values[2].value}"
    
    print("✅ Basic SMA computation test passed")


def test_sma_realistic():
    """Test SMA with realistic data"""
    print("Testing SMA with realistic data...")
    
    closes = [
        150.00, 151.50, 149.75, 152.25, 153.00,
        154.50, 153.75, 155.00, 156.25, 155.50,
        157.00, 158.25, 157.50, 159.00, 160.25,
        159.50, 161.00, 162.25, 161.50, 163.00,
        164.25, 163.50, 165.00, 166.25, 165.50
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
    
    # Compute 20-period SMA
    sma = SMAIndicator(period=20)
    values = sma.compute(candles, {'period': 20})
    
    # Verify results
    assert len(values) == 6, f"Expected 6 values, got {len(values)}"
    
    # Verify first SMA value
    expected_first = sum(Decimal(str(c)) for c in closes[:20]) / Decimal('20')
    assert values[0].value == expected_first, f"Expected {expected_first}, got {values[0].value}"
    
    print("✅ Realistic SMA computation test passed")


def test_sma_edge_cases():
    """Test SMA edge cases"""
    print("Testing SMA edge cases...")
    
    # Test with period=1 (should equal close price)
    candles = []
    for i in range(5):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal(str(100 + i * 10)),
            volume=1000000
        ))
    
    sma = SMAIndicator(period=1)
    values = sma.compute(candles, {'period': 1})
    
    assert len(values) == 5, f"Expected 5 values, got {len(values)}"
    for i, value in enumerate(values):
        assert value.value == candles[i].close, f"Expected {candles[i].close}, got {value.value}"
    
    print("✅ Edge case tests passed")


def test_sma_insufficient_data():
    """Test SMA with insufficient data"""
    print("Testing SMA with insufficient data...")
    
    # Create only 10 candles
    candles = []
    for i in range(10):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('105.00'),
            volume=1000000
        ))
    
    # Try to compute 20-period SMA
    sma = SMAIndicator(period=20)
    
    try:
        sma.compute(candles, {'period': 20})
        print("❌ Should have raised ValueError for insufficient data")
        sys.exit(1)
    except ValueError as e:
        if "requires at least 20 candles" in str(e):
            print("✅ Insufficient data error handling test passed")
        else:
            print(f"❌ Wrong error message: {e}")
            sys.exit(1)


def test_sma_unsorted_candles():
    """Test SMA handles unsorted candles"""
    print("Testing SMA with unsorted candles...")
    
    # Create candles in wrong order
    candles = [
        Candle(
            timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('30'),
            volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('10'),
            volume=1000000
        ),
        Candle(
            timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('20'),
            volume=1000000
        ),
    ]
    
    # Compute 3-period SMA
    sma = SMAIndicator(period=3)
    values = sma.compute(candles, {'period': 3})
    
    # Should have 1 value
    assert len(values) == 1, f"Expected 1 value, got {len(values)}"
    
    # Should be average of sorted closes: (10 + 20 + 30) / 3 = 20
    assert values[0].value == Decimal('20'), f"Expected 20, got {values[0].value}"
    
    print("✅ Unsorted candles test passed")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("SMA Indicator Verification")
    print("=" * 60)
    print()
    
    try:
        test_sma_basic()
        test_sma_realistic()
        test_sma_edge_cases()
        test_sma_insufficient_data()
        test_sma_unsorted_candles()
        
        print()
        print("=" * 60)
        print("✅ All SMA indicator tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed with error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
