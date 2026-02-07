"""
Verification script for indicator protocol and base classes.

This script performs basic validation of the indicator module without
requiring pytest or a full test environment.
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal

# Add app to path
sys.path.insert(0, '.')

try:
    from app.services.indicators import (
        Candle,
        IndicatorValue,
        Indicator,
        BaseIndicator,
        IndicatorRegistry,
        Timeframe
    )
    print("✅ Successfully imported all indicator classes")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 1: Create a valid candle
print("\n--- Test 1: Create valid candle ---")
try:
    candle = Candle(
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('150.00'),
        high=Decimal('155.00'),
        low=Decimal('149.00'),
        close=Decimal('154.00'),
        volume=1000000,
        timeframe='1D'
    )
    print(f"✅ Created valid candle: {candle.close} at {candle.timestamp}")
    assert candle.is_valid()
    print("✅ Candle validation passed")
except Exception as e:
    print(f"❌ Failed to create candle: {e}")
    sys.exit(1)

# Test 2: Test candle validation (should fail)
print("\n--- Test 2: Test invalid candle (high < low) ---")
try:
    invalid_candle = Candle(
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        open=Decimal('150.00'),
        high=Decimal('149.00'),  # High < Low
        low=Decimal('151.00'),
        close=Decimal('150.00'),
        volume=1000000
    )
    print("❌ Should have raised ValueError for invalid candle")
    sys.exit(1)
except ValueError as e:
    print(f"✅ Correctly rejected invalid candle: {e}")

# Test 3: Test typical price calculation
print("\n--- Test 3: Test typical price calculation ---")
candle = Candle(
    timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    open=Decimal('150.00'),
    high=Decimal('156.00'),
    low=Decimal('147.00'),
    close=Decimal('153.00'),
    volume=1000000
)
typical = candle.typical_price()
expected = Decimal('152.00')
if typical == expected:
    print(f"✅ Typical price calculation correct: {typical}")
else:
    print(f"❌ Typical price incorrect: got {typical}, expected {expected}")
    sys.exit(1)

# Test 4: Test true range calculation
print("\n--- Test 4: Test true range calculation ---")
tr_without_prev = candle.true_range()
expected_tr = Decimal('9.00')  # 156 - 147
if tr_without_prev == expected_tr:
    print(f"✅ True range without prev_close correct: {tr_without_prev}")
else:
    print(f"❌ True range incorrect: got {tr_without_prev}, expected {expected_tr}")
    sys.exit(1)

# Test 5: Create indicator value
print("\n--- Test 5: Create indicator value ---")
try:
    value = IndicatorValue(
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        indicator_name='SMA_20',
        value=Decimal('152.50')
    )
    print(f"✅ Created indicator value: {value.indicator_name} = {value.value}")
except Exception as e:
    print(f"❌ Failed to create indicator value: {e}")
    sys.exit(1)

# Test 6: Create indicator value with metadata
print("\n--- Test 6: Create indicator value with metadata ---")
try:
    metadata = {
        'upper_band': Decimal('155.00'),
        'lower_band': Decimal('145.00')
    }
    value = IndicatorValue(
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        indicator_name='BB_20',
        value=Decimal('150.00'),
        metadata=metadata
    )
    print(f"✅ Created indicator value with metadata: {value.indicator_name}")
    print(f"   Upper band: {value.metadata['upper_band']}")
    print(f"   Lower band: {value.metadata['lower_band']}")
except Exception as e:
    print(f"❌ Failed to create indicator value with metadata: {e}")
    sys.exit(1)

# Test 7: Test indicator registry
print("\n--- Test 7: Test indicator registry ---")
try:
    registry = IndicatorRegistry()
    print("✅ Created indicator registry")
    
    # Verify empty registry
    if len(registry.list_all()) == 0:
        print("✅ Registry is initially empty")
    else:
        print("❌ Registry should be empty initially")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to create registry: {e}")
    sys.exit(1)

# Test 8: Test Timeframe enum
print("\n--- Test 8: Test Timeframe enum ---")
try:
    assert Timeframe.ONE_MINUTE.value == "1m"
    assert Timeframe.FIVE_MINUTE.value == "5m"
    assert Timeframe.ONE_DAY.value == "1D"
    print("✅ Timeframe enum values correct")
except Exception as e:
    print(f"❌ Timeframe enum test failed: {e}")
    sys.exit(1)

# Test 9: Test concrete indicator implementation
print("\n--- Test 9: Test concrete indicator implementation ---")
try:
    from typing import Dict, Any, List
    
    class SimpleMovingAverage(BaseIndicator):
        """Simple test implementation of SMA"""
        
        @property
        def name(self) -> str:
            return "SMA_TEST"
        
        def required_periods(self, params: Dict[str, Any]) -> int:
            return params.get('period', 20)
        
        def _compute_values(
            self,
            candles: List[Candle],
            params: Dict[str, Any]
        ) -> List[IndicatorValue]:
            period = params['period']
            values = []
            
            for i in range(period - 1, len(candles)):
                window = candles[i - period + 1:i + 1]
                avg = sum(c.close for c in window) / period
                
                values.append(IndicatorValue(
                    timestamp=candles[i].timestamp,
                    indicator_name=self.name,
                    value=avg
                ))
            
            return values
    
    # Create test candles
    candles = []
    for i in range(10):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal(str(150 + i)),
            volume=1000000
        ))
    
    # Test indicator
    sma = SimpleMovingAverage()
    print(f"✅ Created SMA indicator: {sma.name}")
    
    # Compute values
    values = sma.compute(candles, {'period': 5})
    print(f"✅ Computed {len(values)} indicator values")
    
    # Verify first value
    # First 5 closes: 150, 151, 152, 153, 154
    # Average: (150 + 151 + 152 + 153 + 154) / 5 = 760 / 5 = 152
    if values[0].value == Decimal('152'):
        print(f"✅ First SMA value correct: {values[0].value}")
    else:
        print(f"❌ First SMA value incorrect: got {values[0].value}, expected 152")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Concrete indicator test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 10: Test insufficient data handling
print("\n--- Test 10: Test insufficient data handling ---")
try:
    class TestIndicator(BaseIndicator):
        @property
        def name(self) -> str:
            return "TEST"
        
        def required_periods(self, params: Dict[str, Any]) -> int:
            return 20
        
        def _compute_values(
            self,
            candles: List[Candle],
            params: Dict[str, Any]
        ) -> List[IndicatorValue]:
            return []
    
    indicator = TestIndicator()
    
    # Create only 10 candles (need 20)
    candles = []
    for i in range(10):
        candles.append(Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        ))
    
    try:
        indicator.compute(candles, {})
        print("❌ Should have raised ValueError for insufficient data")
        sys.exit(1)
    except ValueError as e:
        if "requires at least 20 candles" in str(e):
            print(f"✅ Correctly rejected insufficient data: {e}")
        else:
            print(f"❌ Wrong error message: {e}")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ Insufficient data test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL VERIFICATION TESTS PASSED!")
print("="*60)
print("\nThe indicator protocol and base classes are working correctly.")
print("Ready for indicator implementations (SMA, EMA, RSI, etc.)")
