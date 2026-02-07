"""Quick syntax check for ATR indicator"""

try:
    from app.services.indicators import ATRIndicator, Candle
    from datetime import datetime, timezone
    from decimal import Decimal
    
    print("✅ ATRIndicator imported successfully")
    
    # Create a simple test
    atr = ATRIndicator(period=14)
    print(f"✅ ATRIndicator instantiated: {atr.name}")
    
    # Create test candles
    candles = [
        Candle(
            timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('105.00'),
            low=Decimal('95.00'),
            close=Decimal(str(100 + i)),
            volume=1000000
        )
        for i in range(20)
    ]
    print(f"✅ Created {len(candles)} test candles")
    
    # Compute ATR
    values = atr.compute(candles, {'period': 14})
    print(f"✅ Computed {len(values)} ATR values")
    
    # Check first value
    first_value = values[0]
    print(f"✅ First ATR value: {first_value.value:.4f}")
    print(f"✅ True range in metadata: {first_value.metadata['true_range']:.4f}")
    
    # Check non-negativity
    all_non_negative = all(v.value >= Decimal('0') for v in values)
    print(f"✅ All values non-negative: {all_non_negative}")
    
    print("\n✅ All syntax checks passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
